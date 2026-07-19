# [Bug] Deadlock - 상반된 락 획득 순서로 worker 스레드 무응답

| 항목 | 내용 |
|---|---|
| 심각도 | Critical |
| 발생 시각 | 2026-07-19 09:02:58~09:03:51 UTC |
| 대상 | `agent-leak-app` worker PID 6591 |
| Before | `MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=10`, `MULTI_THREAD_ENABLE=true` |
| After | `MULTI_THREAD_ENABLE=false`, 나머지 설정 동일 |

## 1. Description (현상 설명)

멀티스레드 모드에서 두 worker 스레드가 각각 하나의 락을 획득한 뒤 상대 스레드가 보유한 락을 기다렸습니다. `09:03:00 UTC`부터 애플리케이션 로그 진행이 완전히 멈췄지만 worker PID 6591과 세 스레드는 60초 관측 종료 시점까지 유지됐습니다. 이 구간의 CPU와 RSS도 사실상 정체됐습니다.

PID가 존재한다는 사실만으로는 정상 유휴, I/O 대기, 느린 처리와 교착을 구분할 수 없습니다. 이 건은 **PID 생존**, **CPU·RSS 정체**, **로그 진행 중단**, **상호 락 대기 기록**이 동시에 나타나므로 Deadlock으로 판정했습니다.

재현 설정:

```bash
export CASE_NAME=deadlock
export RUN_ID=before-01
export MEMORY_LIMIT=512
export CPU_MAX_OCCUPY=10
export MULTI_THREAD_ENABLE=true
source scripts/prepare-runtime.sh
scripts/start-app.sh
```

## 2. Evidence & Logs (증거 자료)

### 상호 락 대기와 로그 중단

[Before 실행 로그](../artifacts/deadlock/before-01/console.log)의 마지막 구간은 각 스레드가 보유한 락과 추가로 요청한 락을 명시합니다.

```text
2026-07-19 09:02:58,305 [Worker-Thread-1] LOCK ACQUIRED: [Shared_Memory_A]. (Holding...)
2026-07-19 09:02:58,306 [Worker-Thread-2] LOCK ACQUIRED: [Socket_Pool_B]. (Holding...)
2026-07-19 09:03:00,321 [Worker-Thread-1] Need resource [Socket_Pool_B] to finish job.
2026-07-19 09:03:00,322 [Worker-Thread-2] Need resource [Shared_Memory_A] to write logs.
2026-07-19 09:03:00,323 [Worker-Thread-1] WAITING for [Socket_Pool_B]... (Status: BLOCKED)
2026-07-19 09:03:00,324 [Worker-Thread-2] WAITING for [Shared_Memory_A]... (Status: BLOCKED)
```

마지막 BLOCKED 기록 이후 정상 완료나 후속 작업 로그는 한 줄도 발생하지 않았습니다.

### PID 생존과 자원 정체

[Before 관제 로그](../artifacts/deadlock/before-01/monitor.tsv)는 스레드가 생성된 경과 7초부터 실험자가 종료하기 직전인 경과 60초까지 PID 6591과 세 스레드가 계속 존재했음을 보여 줍니다.

| 경과 시간 | PID | 상태 | 누적 CPU | RSS | 스레드 |
|---:|---:|---|---:|---:|---:|
| 00:07 | 6591 | SNl | 0.5% | 16.41MB | 3 |
| 00:15 | 6591 | SNl | 0.3% | 16.41MB | 3 |
| 00:45 | 6591 | SNl | 0.1% | 16.44MB | 3 |
| 01:00 | 6591 | SNl | 0.0% | 16.44MB | 3 |

BLOCKED 이후 RSS 변화는 28KB에 불과했고 누적 CPU는 새로운 작업을 하지 않으면서 0.0%로 수렴했습니다. [`ps` 전체 프로세스 시계열](../artifacts/deadlock/before-01/ps-timeseries.txt)에서도 PID 6591이 관측 구간 내내 유지됩니다.

### 스레드별 정체

[15초 스레드 `top` 스냅샷](../artifacts/deadlock/before-01/snapshots/20260719-090306-deadlock-before-15s-top-threads.txt)과 [45초 스레드 `top` 스냅샷](../artifacts/deadlock/before-01/snapshots/20260719-090336-deadlock-before-45s-top-threads.txt)은 모두 같은 결과를 기록합니다.

- 세 스레드 모두 sleeping 상태
- running 스레드 0개
- 세 스레드의 순간 CPU 0.0%
- RSS 약 16.4MB로 유지

[0.5초 간격 스레드 시계열](../artifacts/deadlock/before-01/top-threads-timeseries.txt)에서도 BLOCKED 직후를 제외하면 두 worker 스레드는 계속 CPU 0.0%였습니다. `top`의 sleeping 상태만으로 락 대기를 확정할 수는 없지만, 상호 락 대기 로그 및 장시간 진행 정체와 결합하면 교착 판정을 지지합니다.

Before PID는 장애 때문에 저절로 종료된 것이 아닙니다. [운영자 조치 로그](../artifacts/deadlock/before-01/operator-actions.log)에 기록한 대로 60초 관측을 마친 실험자가 SIGTERM으로 종료했고, [종료 이벤트](../artifacts/deadlock/before-01/monitor-events.log)는 다음 관제 시점에 PID 소멸을 확인했습니다.

### After 작업 완료

`MULTI_THREAD_ENABLE=false`를 적용한 [After 실행 로그](../artifacts/deadlock/after-01/console.log)에서는 Scheduler가 Thread-A, B, C를 순서대로 실행했습니다.

```text
2026-07-19 09:03:58,286 [Thread-A] Task Started. Calculating... (20%)
2026-07-19 09:03:58,502 [Thread-A] Task Completed. (100%)
2026-07-19 09:03:58,554 [Thread-B] Task Started. Calculating... (20%)
2026-07-19 09:03:58,775 [Thread-B] Task Completed. (100%)
2026-07-19 09:03:58,832 [Thread-C] Task Started. Calculating... (20%)
2026-07-19 09:03:59,048 [Thread-C] Task Completed. (100%)
2026-07-19 09:03:59,105 [Scheduler] All tasks completed.
```

세 작업은 Scheduler 시작 후 약 0.82초 안에 모두 완료됐습니다. 이후에도 45초 검증 종료까지 MemoryWorker와 CpuWorker 로그가 계속 발생했으며 WAITING/BLOCKED는 재발하지 않았습니다. After 역시 [운영자 조치 로그](../artifacts/deadlock/after-01/operator-actions.log)에 기록한 대로 검증을 마친 실험자가 SIGTERM으로 종료했습니다.

## 3. Root Cause Analysis (원인 분석)

두 스레드의 락 획득 순서가 서로 반대인 것이 직접 원인입니다.

```text
Worker-Thread-1: Shared_Memory_A 보유 → Socket_Pool_B 대기
Worker-Thread-2: Socket_Pool_B 보유 → Shared_Memory_A 대기
```

이 구조는 교착상태의 네 가지 필요 조건을 모두 만족합니다.

- 상호 배제: 각 락은 한 번에 한 스레드만 보유합니다.
- 점유 대기: 각 스레드는 첫 번째 락을 보유한 채 두 번째 락을 기다립니다.
- 비선점: 다른 스레드가 보유한 락을 강제로 회수하지 않습니다.
- 순환 대기: Thread-1 → Thread-2 → Thread-1의 대기 고리가 만들어집니다.

두 스레드 모두 두 번째 락을 획득하기 전에는 현재 락을 해제할 수 없으므로 대기 고리가 스스로 풀리지 않습니다. 그 결과 프로세스는 종료되지 않으면서 유효 작업과 로그 출력이 영구 정지합니다. CPU와 RSS가 낮고 안정적인 것은 정상 상태의 증거가 아니라 runnable 연산과 신규 할당이 멈춘 결과입니다.

## 4. Workaround & Verification (조치 및 검증)

임시 조치로 `MULTI_THREAD_ENABLE=false`를 적용하여 두 transaction worker가 동시에 서로 다른 락을 선점할 가능성을 제거했습니다.

| 비교 항목 | Before | After |
|---|---|---|
| `MULTI_THREAD_ENABLE` | true | false |
| 작업 방식 | 두 worker가 상반된 순서로 락 획득 | 작업 A/B/C 순차 실행 |
| 업무 로그 | WAITING/BLOCKED에서 정지 | 약 0.82초 안에 모두 완료 |
| 관측 결과 | PID 생존, CPU·RSS·로그 정체 | 45초 동안 BLOCKED 재발 없음 |
| 실험 종료 | 60초 후 실험자 SIGTERM | 45초 후 실험자 SIGTERM |

멀티스레드 비활성화는 교착을 회피하지만 병렬 처리량을 포기하는 임시 조치입니다. 근본 해결은 모든 코드 경로에서 락 획득 순서를 하나로 통일하는 것입니다. 예를 들어 항상 `Shared_Memory_A` 다음 `Socket_Pool_B` 순서로 획득해야 합니다.

가능하면 두 자원을 하나의 임계 구역으로 단순화하거나, timeout이 있는 락 획득과 실패 시 이미 보유한 락 해제를 적용해야 합니다. 운영 환경에는 요청 진행 시간과 lock-wait 시간을 별도 지표로 추가하고, PID 생존 여부가 아니라 일정 시간 동안의 작업 완료량을 기준으로 무응답을 탐지해야 합니다.
