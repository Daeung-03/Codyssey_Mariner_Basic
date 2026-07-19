# [Bug] CPU Latency - 내부 부하 임계치 위반 후 보호 종료

| 항목 | 내용 |
|---|---|
| 심각도 | High (OS 수준 과점유는 관측되지 않음) |
| 발생 시각 | 2026-07-19 08:53:32~08:54:02 UTC |
| 대상 | `agent-leak-app` worker PID 5797 |
| Before | `MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=100`, `MULTI_THREAD_ENABLE=false` |
| After | `CPU_MAX_OCCUPY=10`, 나머지 설정 동일 |

## 1. Description (현상 설명)

`CPU_MAX_OCCUPY=100`으로 실행하면 애플리케이션의 `CpuWorker Current Load`가 5.00%에서 55.96%까지 계속 상승합니다. 내부 부하가 50%를 넘어선 직후 `CPU Threshold Violated!`가 기록되고 worker PID 5797이 시작 약 30.27초 만에 종료됐습니다.

연속 `top`으로 확인한 실제 OS CPU 사용량은 내부 지표와 달랐습니다. 초기화 직후 첫 표본을 제외한 worker의 순간 최대는 10.0%였고, 그 시점에도 시스템 전체 CPU는 98.6% idle이었습니다. 따라서 확인된 장애는 **애플리케이션 내부 부하 지표의 안전 임계치 위반과 보호 종료**이며, 실제 OS CPU 포화에 의한 시스템 전체 지연은 이 실행에서 입증되지 않았습니다.

재현 설정:

```bash
export CASE_NAME=cpu
export RUN_ID=before-01
export MEMORY_LIMIT=512
export CPU_MAX_OCCUPY=100
export MULTI_THREAD_ENABLE=false
source scripts/prepare-runtime.sh
scripts/start-app.sh
```

## 2. Evidence & Logs (증거 자료)

### 내부 부하 상승 및 프로세스 종료

[Before 실행 로그](../artifacts/cpu/before-01/console.log)의 내부 지표는 다음과 같이 상승했습니다.

```text
2026-07-19 08:53:34,292 [INFO] [CpuWorker] Current Load: 5.00%
2026-07-19 08:53:49,926 [INFO] [CpuWorker] Current Load: 28.99%
2026-07-19 08:53:56,180 [INFO] [CpuWorker] Current Load: 40.73%
2026-07-19 08:53:59,309 [INFO] [CpuWorker] Current Load: 49.79%
2026-07-19 08:54:02,441 [INFO] [CpuWorker] Current Load: 55.96%
2026-07-19 08:54:02,544 [CRITICAL] [CpuWorker] CPU Threshold Violated! (55.96%).
```

[종료 이벤트](../artifacts/cpu/before-01/monitor-events.log)는 같은 시각인 `08:54:02 UTC`에 PID 5797이 더 이상 존재하지 않음을 기록합니다. 로그에는 `WATCHDOG` 또는 `SIGTERM` 문자열이 없으므로 정확한 종료 신호까지는 확정하지 않습니다.

### 실제 OS CPU 관제

[Before 연속 `top`](../artifacts/cpu/before-01/top-timeseries.txt)은 launcher와 worker를 0.5초 간격으로 수집한 자료입니다. `top`의 첫 프로세스 표본은 실행 직후 매우 짧은 누적 구간을 계산해 18.8%로 표시됐으며 After에서도 동일하게 나타났으므로 초기화 표본으로 분리했습니다.

첫 표본 이후 worker의 실제 순간 CPU는 대부분 0%였고, 내부 부하 증가 로그가 출력되는 시점에 짧게 상승했습니다.

| 시각 | 내부 Current Load | worker 순간 `%CPU` | 시스템 idle |
|---|---:|---:|---:|
| 08:53:53 | 35.12% | 최대 3.9% | 99% 이상 |
| 08:53:56 | 40.73% | 최대 7.8% | 99% 안팎 |
| 08:53:59 | 49.79% | 최대 10.0% | 98.6% |
| 08:54:02 | 55.96%, 종료 | 종료 직전 표본 0.0% | 98% 이상 |

[`ps` 전체 프로세스 시계열](../artifacts/cpu/before-01/ps-timeseries.txt)에서도 종료 직전 worker의 누적 평균은 약 0.8~1.0%, launcher는 약 0.2~0.3%였습니다. 이는 컨테이너 프로세스 중 worker의 사용량이 상대적으로 가장 높다는 점은 보여 주지만 시스템 포화를 의미하지는 않습니다.

[내부 부하 40.73% 시점의 프로세스 스냅샷](../artifacts/cpu/before-01/snapshots/20260719-085356-cpu-before-high-load-process.txt)은 PID 5797이 `analyst` 권한, `SN` 상태, CPU 0.9%, RSS 16,760KB, 단일 스레드였음을 기록합니다. 같은 시점의 [CPU 순위](../artifacts/cpu/before-01/snapshots/20260719-085356-cpu-before-high-load-cpu-ranking.txt)에서도 worker가 0.9%로 가장 높았고 launcher는 0.3%였습니다.

### After 동작

`CPU_MAX_OCCUPY=10`으로 낮춘 [After 실행 로그](../artifacts/cpu/after-01/console.log)에서는 내부 부하가 10%에 도달할 때마다 cooldown으로 전환되어 5%까지 내려간 뒤 다시 증가했습니다.

```text
2026-07-19 08:54:09,796 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
2026-07-19 08:54:16,041 [INFO] [CpuWorker] Cooldown complete (5.00%). Resuming load increase...
2026-07-19 08:54:22,305 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
2026-07-19 08:54:25,437 [INFO] [CpuWorker] Cooldown complete (5.00%). Resuming load increase...
```

[After 연속 `top`](../artifacts/cpu/after-01/top-timeseries.txt)의 초기화 표본 이후 worker 순간 최대는 4.0%였습니다. [35초 시점 CPU 순위](../artifacts/cpu/after-01/snapshots/20260719-085440-cpu-after-35s-cpu-ranking.txt)에서는 worker 누적 평균이 0.7%였고 다른 프로세스는 0.1% 이하였습니다.

After worker PID 6168은 45초 검증 구간 동안 임계치 위반 없이 생존했습니다. 이후 실험자가 의도적으로 SIGTERM을 보냈으며, 이 사실은 [운영자 조치 로그](../artifacts/cpu/after-01/operator-actions.log)와 [PID 종료 이벤트](../artifacts/cpu/after-01/monitor-events.log)에 각각 기록되어 있습니다. 따라서 After의 PID 소멸은 보호 정책 발동이 아닙니다.

## 3. Root Cause Analysis (원인 분석)

직접 확인된 인과관계는 다음과 같습니다.

1. `CPU_MAX_OCCUPY=100` 설정은 부팅 시 권장 상한 50%를 넘는 구성으로 경고됩니다.
2. 이 설정에서 앱 내부 부하 생성기는 cooldown 없이 `Current Load`를 계속 올립니다.
3. 내부 부하가 50%를 넘어 55.96%가 되면 `CpuWorker`가 임계치 위반을 기록하고 프로세스가 종료됩니다.
4. `CPU_MAX_OCCUPY=10`에서는 5~10% 구간의 cooldown 제어가 반복되고 임계치 위반이 발생하지 않습니다.

따라서 직접 원인은 **과도한 CPU 부하 상한 설정으로 내부 안전 경계를 넘긴 구성**이며, 종료는 `CpuWorker` 보호 로직과 연관됩니다.

다만 `Current Load`는 커널이 측정한 프로세스 `%CPU`와 동일한 값이 아닙니다. 내부 값 49.79% 시점의 실제 순간 CPU는 최대 10.0%였고 시스템은 98.6% idle이었습니다. 이는 앱의 내부 지표가 실제 CPU 사용률이 아니라 부하 시나리오 또는 제어 로직의 합성 값일 가능성이 높다는 근거입니다.

일반적으로 CPU 과점유가 발생하면 runnable 작업이 CPU 시간을 독점하여 run queue가 길어지고 다른 프로세스의 스케줄링과 응답이 지연됩니다. 하지만 이번 환경에서는 그 수준의 OS 포화가 관측되지 않았으므로, 실제 시스템 지연까지 발생했다고 확대 해석하지 않습니다.

## 4. Workaround & Verification (조치 및 검증)

임시 조치로 `CPU_MAX_OCCUPY`를 100%에서 10%로 낮췄습니다.

| 비교 항목 | Before | After |
|---|---:|---:|
| `CPU_MAX_OCCUPY` | 100% | 10% |
| 내부 부하 패턴 | 5.00% → 55.96% | 5~10% 사이 cooldown 반복 |
| 초기화 표본 이후 실제 순간 CPU 최대 | 10.0% | 4.0% |
| 관측 결과 | 약 30.27초 후 임계치 위반·종료 | 45초 동안 임계치 위반 없이 생존 |
| 종료 주체 | `CpuWorker` 보호 로직과 연관 | 검증 완료 후 실험자 SIGTERM |

설정 변경으로 내부 임계치 위반을 방지했고, 실제 순간 CPU 최대도 관측 구간에서 10.0%에서 4.0%로 낮아졌습니다. 다만 이 수치는 단일 실행의 최대 표본이므로 장기 성능 보장을 의미하지 않습니다.

근본 개선을 위해서는 `Current Load`의 산출 방식과 단위를 명시하고, 실제 OS CPU 텔레메트리와 내부 지표를 별도 이름으로 기록해야 합니다. 또한 보호 종료 시 정책명, 종료 신호, exit reason을 구조화해 남기고, 운영 환경에서는 프로세스 CPU뿐 아니라 run queue와 요청 지연시간을 함께 경보 기준으로 사용해야 합니다.
