# 시스템 장애 분석 리포트

이 디렉터리는 `Problem.md`의 GitHub Issue 양식과 케이스별 최소 증거 요건에 맞춰 원본 산출물을 다시 검증한 결과입니다. `study/experiment.md`의 서술보다 `artifacts/`의 실행별 `console.log`, `monitor.tsv`, `monitor-events.log`, `snapshots/`를 우선 근거로 사용했습니다.

## 리포트 목록

1. [OOM Crash - 메모리 보호 정책에 따른 자체 종료](01-oom-crash.md)
2. [CPU Latency - 내부 부하 임계치 위반에 따른 종료](02-cpu-latency.md)
3. [Deadlock - 상반된 락 획득 순서로 인한 무응답](03-deadlock.md)

## 분석 결과 요약

| 장애 | Before | 임시 조치 | After | 판정 |
|---|---|---|---|---|
| OOM Crash | `MEMORY_LIMIT=50`, 약 5.03초 후 MemoryGuard 자체 종료 | `MEMORY_LIMIT=256` | 약 32.23초 후 동일 원인으로 종료 | 생존 시간만 약 6.4배 증가, 누수 미해결 |
| CPU Latency | `CPU_MAX_OCCUPY=100`, 내부 부하 55.96%에서 약 30.27초 후 종료 | `CPU_MAX_OCCUPY=10` | 45초 동안 cooldown을 반복한 뒤 실험자 종료 | 실제 순간 최대 10.0%→4.0%, OS 포화는 관측되지 않음 |
| Deadlock | `MULTI_THREAD_ENABLE=true`, PID 6591이 60초 동안 존재하나 진행 정지 | `MULTI_THREAD_ENABLE=false` | 작업 A/B/C가 약 0.82초 안에 완료 | 45초간 교착 재발 없음, 동시성 비활성화에 따른 처리량 손실 가능 |

## 증거 해석 시 주의 사항

- `agent-leak-app`은 launcher와 worker의 두 프로세스로 실행됩니다. 각 실행의 `app.pid`가 가리키는 worker를 관제 대상으로 삼았습니다.
- `monitor.tsv`의 `cpu_percent`는 `ps -o pcpu` 값으로, 프로세스 시작 이후의 평균 CPU 비율입니다. 짧은 순간의 spike를 정확히 나타내는 순간값은 아닙니다.
- OOM 케이스는 Linux 커널 OOM killer가 아니라 애플리케이션 내부 `MemoryGuard`가 한도 초과를 감지해 자체 종료한 사건입니다.
- CPU Before의 앱 내부 `Current Load`와 OS 관제 `%CPU`는 서로 일치하지 않습니다. 이 차이를 무시하고 “실제 CPU 55.96% 과점유”라고 단정하면 현재 증거와 모순됩니다.
- 최종 OOM, CPU, Deadlock 실험은 각각 새 실행 디렉터리에서 한 번씩 수집하여 과거 실행 로그가 섞이지 않았습니다.

## CPU 증거 해석 결론

CPU Before/After 재실행에서 launcher와 worker의 0.5초 간격 `top`, 전체 프로세스 CPU 순위, 임계치 근처 스냅샷을 확보했습니다. 재실행에서도 앱 내부 `Current Load=55.96%`와 실제 OS `%CPU`는 일치하지 않았고 시스템 전체는 98% 이상 idle이었습니다. 따라서 현재 바이너리는 실제 시스템 포화보다 내부 부하 시나리오를 모사하는 것으로 판단하며, 이 한계를 CPU 리포트에 명시했습니다.

Before 종료 로그에는 `CPU Threshold Violated!`만 있고 `WATCHDOG`나 종료 신호는 기록되지 않습니다. 반면 After는 45초 검증 뒤 실험자가 보낸 SIGTERM을 `operator-actions.log`에 별도로 기록했으므로 두 종료 원인을 구분할 수 있습니다.
