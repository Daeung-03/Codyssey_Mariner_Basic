# [Bug] OOM Crash - 힙 사용량 누적으로 MemoryGuard 자체 종료

| 항목 | 내용 |
|---|---|
| 심각도 | High |
| 발생 시각 | 2026-07-19 08:36:03~08:36:08 UTC |
| 대상 | `agent-leak-app` worker PID 5565 |
| Before | `MEMORY_LIMIT=50`, `CPU_MAX_OCCUPY=10`, `MULTI_THREAD_ENABLE=false` |
| After | `MEMORY_LIMIT=256`, 나머지 조건 동일 |

## 1. Description (현상 설명)

`MEMORY_LIMIT=50`으로 실행한 `agent-leak-app`의 RSS가 시간에 따라 계속 증가했고, 시작 약 5.03초 뒤 내부 `MemoryGuard`가 힙 50MB 도달을 감지하여 프로세스 PID 5565를 자체 종료했습니다.

이 사건은 Linux 커널의 OOM killer가 프로세스를 제거한 것이 아닙니다. 애플리케이션 로그에 한도 초과와 자체 종료 주체가 명시되어 있으므로, 정확한 현상은 **지속적인 메모리 누적에 따른 애플리케이션 보호 정책 발동**입니다.

재현 설정:

```bash
export CASE_NAME=oom
export RUN_ID=before-01
export MEMORY_LIMIT=50
export CPU_MAX_OCCUPY=10
export MULTI_THREAD_ENABLE=false
source scripts/prepare-runtime.sh
scripts/start-app.sh
```

## 2. Evidence & Logs (증거 자료)

### 메모리 관제

[Before 전체 관제 로그](../artifacts/oom/before-01/monitor.tsv)에서 RSS가 5초 동안 9.65MB에서 41.31MB로 증가했습니다. 힙 50MB 할당 직후 프로세스가 자체 종료되어, 그 할당이 반영된 다음 1초 주기의 RSS 표본은 수집되지 않았습니다.

| 경과 시간 | 상태 | RSS | 스레드 |
|---:|---|---:|---:|
| 00:00 | R | 9.65MB | 1 |
| 00:01 | SN | 16.31MB | 1 |
| 00:03 | SN | 41.31MB | 1 |
| 00:05 | SN | 41.31MB | 1 |

앱 로그의 힙 수치도 같은 방향으로 증가했습니다. [Before 실행 로그](../artifacts/oom/before-01/console.log)의 핵심 구간은 다음과 같습니다.

```text
2026-07-19 08:36:05,541 [INFO] [MemoryWorker] Current Heap: 25MB
2026-07-19 08:36:08,551 [INFO] [MemoryWorker] Current Heap: 50MB
2026-07-19 08:36:08,552 [CRITICAL] [MemoryGuard] Memory limit exceeded (50MB >= 50MB)
2026-07-19 08:36:08,552 [CRITICAL] [MemoryGuard] Self-terminating process 5565 to prevent system instability.
```

[프로세스 종료 이벤트](../artifacts/oom/before-01/monitor-events.log)에는 바로 다음 관제 시각인 `08:36:09 UTC`에 PID 5565가 더 이상 존재하지 않는다고 기록되어 있습니다.

### 시스템 도구 스냅샷

[Before 프로세스 스냅샷](../artifacts/oom/before-01/snapshots/20260719-083605-oom-before-mid-process.txt)은 PID 5565가 일반 사용자 `analyst` 권한으로 실행되고 있으며, 경과 2초 시점에 RSS 16,700KB와 단일 스레드를 사용했음을 보여 줍니다. 바로 뒤이어 수집된 [`top` 스냅샷](../artifacts/oom/before-01/snapshots/20260719-083605-oom-before-mid-top-process.txt)에서는 첫 25MB 힙 할당이 반영되어 RSS가 42,304KB까지 증가했습니다.

[After 10초 프로세스 스냅샷](../artifacts/oom/after-01/snapshots/20260719-083651-oom-after-10s-process.txt)은 PID 5619가 여전히 생존한 상태에서 RSS 93,512KB, 단일 스레드임을 기록합니다. 같은 시점의 [`top` 스냅샷](../artifacts/oom/after-01/snapshots/20260719-083651-oom-after-10s-top-process.txt)에서도 RSS 93,512KB가 확인됩니다.

### After 관제

`MEMORY_LIMIT=256`으로 상향한 [After 관제 로그](../artifacts/oom/after-01/monitor.tsv)에서도 RSS는 8.20MB에서 266.35MB까지 계속 증가했습니다.

| 경과 시간 | RSS | 앱 힙 로그 |
|---:|---:|---:|
| 00:00 | 8.20MB | - |
| 00:09 | 91.32MB | 75MB |
| 00:20 | 191.34MB | 175MB |
| 00:29 | 266.35MB | 250MB |
| 약 00:32 | 관제 종료 | 275MB, MemoryGuard 발동 |

[After 실행 로그](../artifacts/oom/after-01/console.log)에는 `275MB >= 256MB`로 한도를 넘어 자체 종료한 사실이 남아 있습니다. RSS가 앱의 논리적 힙보다 큰 것은 런타임·공유 라이브러리·할당자 오버헤드 등 힙 외 상주 메모리도 RSS에 포함되기 때문입니다.

## 3. Root Cause Analysis (원인 분석)

직접 확인된 사실은 다음과 같습니다.

- 동일 워크로드에서 앱이 약 3초마다 힙을 25MB씩 늘립니다.
- RSS도 약 25MB 단위로 계단식 상승하며 관측 구간 내 감소나 안정 구간이 없습니다.
- 설정된 임계치에 도달하면 `MemoryGuard`가 이를 감지하고 프로세스를 종료합니다.

따라서 장애의 직접 원인은 **상한 없이 누적되는 힙 객체 또는 해제되지 않는 참조**이고, 종료 트리거는 **애플리케이션 내부 MemoryGuard**입니다. 제공물이 바이너리이며 리버스 엔지니어링이 금지되어 있어 어느 자료구조가 객체를 보유하는지까지는 확정할 수 없지만, 관측 패턴은 메모리 누수 또는 의도적인 무제한 보유와 일치합니다.

256MB 실행에서 250MB가 아니라 275MB에서 보호 정책이 발동한 것은 25MB 단위 할당 후 주기적으로 한도를 검사하기 때문으로 해석됩니다. 즉, 검사 간격과 할당 단위만큼 설정 한도를 일시적으로 초과할 수 있습니다.

## 4. Workaround & Verification (조치 및 검증)

임시 조치로 `MEMORY_LIMIT`을 50MB에서 256MB로 높이고, CPU 및 멀티스레드 조건은 동일하게 유지했습니다.

| 비교 항목 | Before | After | 변화 |
|---|---:|---:|---:|
| `MEMORY_LIMIT` | 50MB | 256MB | +206MB |
| 종료 시 힙 | 50MB | 275MB | 지속 증가 |
| 마지막 관제 RSS | 41.31MB | 266.35MB | 지속 증가 |
| 시작부터 자체 종료까지 | 약 5.03초 | 약 32.23초 | 약 6.4배 증가 |
| 종료 원인 | MemoryGuard | MemoryGuard | 동일 |

한도 상향은 장애 시점을 늦춰 서비스 연속성을 일시적으로 늘렸지만 누수를 해결하지 못했습니다. 근본 조치로는 누적 객체의 수명과 참조 경로를 확인하고, 처리 완료 데이터 해제, 큐·캐시 상한 설정, 백프레셔 적용이 필요합니다. 운영 측면에서는 RSS 증가율과 MemoryGuard 임계치 근접도를 기준으로 사전 경보를 추가해야 합니다.
