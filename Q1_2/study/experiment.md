## OOM

### 일반 실행

    export CASE_NAME=oom
    export RUN_ID=before-04
    export MEMORY_LIMIT=50
    export CPU_MAX_OCCUPY=10
    export MULTI_THREAD_ENABLE=false

    source scripts/prepare-runtime.sh

    scripts/start-app.sh

    analyst@50e0b074c0ca:/workspace$ cat "$RUN_DIR/monitor.tsv"
    timestamp	pid	state	cpu_percent	rss_kb	rss_mb	threads	elapsed command
    2026-07-12T08:32:56+00:00	397	R	50.0	9128	8.91	1	00:00	agent-leak-app-
    2026-07-12T08:32:57+00:00	397	SN	3.8	16696	16.30	1	00:01	agent-leak-app-
    2026-07-12T08:32:58+00:00	397	SN	1.9	16696	16.30	1	00:02	agent-leak-app-
    2026-07-12T08:32:59+00:00	397	SN	1.6	42300	41.31	1	00:03	agent-leak-app-
    2026-07-12T08:33:01+00:00	397	SN	1.2	42300	41.31	1	00:04	agent-leak-app-
    2026-07-12T08:33:02+00:00	397	RN	0.9	57800	56.45	1	00:05	agent-leak-app-

    analyst@50e0b074c0ca:/workspace$ tail -n 20 "$RUN_DIR/console.log"
    ...
    >>> SYSTEM STATUS: STABLE. STARTING WORKLOAD MONITORING...
    ==================================================

    2026-07-12 08:17:19,669 [INFO] [MemoryWorker] Current Heap: 25MB
    2026-07-12 08:17:22,679 [INFO] [MemoryWorker] Current Heap: 50MB
    2026-07-12 08:17:22,680 [CRITICAL] [MemoryGuard] Memory limit exceeded (50MB >= 50MB) / (Recommend Over 256MB)
    2026-07-12 08:17:22,680 [CRITICAL] [MemoryGuard] Self-terminating process 210 to prevent system instability.

    analyst@50e0b074c0ca:/workspace$ cat "$RUN_DIR/monitor-events.log"
    2026-07-12T08:17:23+00:00	PID 397 is no longer present

    - RSS가 8.38MB -> 16.30MB -> 41.31MB -> 51.51MB로 상승
    - 앱 로그의 Heap도 25MB -> 50MB로 증가
    - MemoryGuard가 50MB >= 50MB를 감지

### After(MemoryGuard 상승)

    export CASE_NAME=oom
    export RUN_ID=after-01
    export MEMORY_LIMIT=256
    export CPU_MAX_OCCUPY=10
    export MULTI_THREAD_ENABLE=false

    source scripts/prepare-runtime.sh

    analyst@a73fa66c6583:/workspace$ cat "$RUN_DIR/monitor.tsv"
    timestamp	pid	state	cpu_percent	rss_kb	rss_mb	threads	elapsedcommand
    2026-07-16T10:36:23+00:00	3064	R	0.0	7708	7.53	1	00:00	agent-leak-app-
    2026-07-16T10:36:24+00:00	3064	SN	4.9	16696	16.30	1	00:01	agent-leak-app-
    2026-07-16T10:36:25+00:00	3064	SN	2.4	16696	16.30	1	00:02	agent-leak-app-
    2026-07-16T10:36:26+00:00	3064	SN	1.6	42300	41.31	1	00:03	agent-leak-app-
    2026-07-16T10:36:27+00:00	3064	SN	1.2	42300	41.31	1	00:04	agent-leak-app-
    2026-07-16T10:36:28+00:00	3064	SN	0.9	42300	41.31	1	00:05	agent-leak-app-
    2026-07-16T10:36:29+00:00	3064	SN	0.8	67904	66.31	1	00:06	agent-leak-app-
    2026-07-16T10:36:30+00:00	3064	SN	0.7	67904	66.31	1	00:07	agent-leak-app-
    2026-07-16T10:36:31+00:00	3064	SN	0.6	67904	66.31	1	00:08	agent-leak-app-
    2026-07-16T10:36:32+00:00	3064	SN	0.6	93508	91.32	1	00:09	agent-leak-app-
    2026-07-16T10:36:33+00:00	3064	SN	0.5	93508	91.32	1	00:10	agent-leak-app-
    2026-07-16T10:36:34+00:00	3064	SN	0.5	119112	116.32	1	00:11	agent-leak-app-
    2026-07-16T10:36:35+00:00	3064	SN	0.4	119112	116.32	1	00:12	agent-leak-app-
    2026-07-16T10:36:36+00:00	3064	SN	0.4	119112	116.32	1	00:13	agent-leak-app-
    2026-07-16T10:36:37+00:00	3064	SN	0.4	144716	141.32	1	00:14	agent-leak-app-
    2026-07-16T10:36:38+00:00	3064	SN	0.3	144716	141.32	1	00:15	agent-leak-app-
    2026-07-16T10:36:39+00:00	3064	SN	0.3	144716	141.32	1	00:16	agent-leak-app-
    2026-07-16T10:36:40+00:00	3064	SN	0.4	170320	166.33	1	00:17	agent-leak-app-
    2026-07-16T10:36:41+00:00	3064	SN	0.4	170320	166.33	1	00:18	agent-leak-app-
    2026-07-16T10:36:42+00:00	3064	SN	0.4	170320	166.33	1	00:19	agent-leak-app-
    2026-07-16T10:36:43+00:00	3064	SN	0.3	195924	191.33	1	00:20	agent-leak-app-
    2026-07-16T10:36:44+00:00	3064	SN	0.3	195924	191.33	1	00:21	agent-leak-app-
    2026-07-16T10:36:45+00:00	3064	SN	0.3	195924	191.33	1	00:22	agent-leak-app-
    2026-07-16T10:36:46+00:00	3064	SN	0.3	221528	216.34	1	00:23	agent-leak-app-
    2026-07-16T10:36:47+00:00	3064	SN	0.3	221528	216.34	1	00:24	agent-leak-app-
    2026-07-16T10:36:48+00:00	3064	SN	0.3	221528	216.34	1	00:25	agent-leak-app-
    2026-07-16T10:36:49+00:00	3064	SN	0.3	247132	241.34	1	00:26	agent-leak-app-
    2026-07-16T10:36:50+00:00	3064	SN	0.3	247132	241.34	1	00:27	agent-leak-app-
    2026-07-16T10:36:51+00:00	3064	SN	0.3	247132	241.34	1	00:28	agent-leak-app-
    2026-07-16T10:36:52+00:00	3064	SN	0.3	272736	266.34	1	00:29	agent-leak-app-
    2026-07-16T10:36:53+00:00	3064	SN	0.2	272736	266.34	1	00:30	agent-leak-app-
    2026-07-16T10:36:54+00:00	3064	SN	0.2	272736	266.34	1	00:31	agent-leak-app-

    analyst@a73fa66c6583:/workspace$ tail -n 60 "$RUN_DIR/console.log"
     >>> SYSTEM STATUS: STABLE. STARTING WORKLOAD MONITORING...
    ==================================================

    2026-07-16 10:36:25,645 [INFO] [MemoryWorker] Current Heap: 25MB
    2026-07-16 10:36:28,666 [INFO] [MemoryWorker] Current Heap: 50MB
    2026-07-16 10:36:31,673 [INFO] [MemoryWorker] Current Heap: 75MB
    2026-07-16 10:36:34,696 [INFO] [MemoryWorker] Current Heap: 100MB
    2026-07-16 10:36:37,717 [INFO] [MemoryWorker] Current Heap: 125MB
    2026-07-16 10:36:40,738 [INFO] [MemoryWorker] Current Heap: 150MB
    2026-07-16 10:36:43,765 [INFO] [MemoryWorker] Current Heap: 175MB
    2026-07-16 10:36:46,791 [INFO] [MemoryWorker] Current Heap: 200MB
    2026-07-16 10:36:49,816 [INFO] [MemoryWorker] Current Heap: 225MB
    2026-07-16 10:36:52,839 [INFO] [MemoryWorker] Current Heap: 250MB
    2026-07-16 10:36:55,861 [INFO] [MemoryWorker] Current Heap: 275MB
    2026-07-16 10:36:55,863 [CRITICAL] [MemoryGuard] Memory limit exceeded (275MB >= 256MB) / (Recommend Over 256MB)
    2026-07-16 10:36:55,863 [CRITICAL] [MemoryGuard] Self-terminating process 3064 to prevent system instability.

    - 앱 Heap 순차적으로 증가, MemoryGuard가 자체 종료
    - 생존 시간 증가.
    - CPU 동일하고, 프로세스 종료까지 확인함
    - 512로 설정 시 flush 정책 확인 -> 아마 MemoryGuard랑 별개로 MemoryWorker가 특정 용량 넘어가면 flush 하는 방식인 거 같음

## CPU 과점유

### Before

    export CASE_NAME=cpu
    export RUN_ID=before-03
    export MEMORY_LIMIT=512
    export CPU_MAX_OCCUPY=100
    export MULTI_THREAD_ENABLE=false

    source scripts/prepare-runtime.sh
    scripts/start-app.sh

    analyst@a73fa66c6583:/workspace$ tail -n 40 "$RUN_DIR/console.log"
    ---
    >>> SYSTEM STATUS: STABLE. STARTING WORKLOAD MONITORING...
    ==================================================

    2026-07-19 05:37:40,831 [INFO] [CpuWorker] Started. Maximum CPU Limit: 100%
    2026-07-19 05:37:40,832 [INFO] [CpuWorker] Current Load: 5.00%
    2026-07-19 05:37:43,959 [INFO] [CpuWorker] Current Load: 12.47%
    2026-07-19 05:37:47,083 [INFO] [CpuWorker] Current Load: 22.07%
    2026-07-19 05:37:50,207 [INFO] [CpuWorker] Current Load: 23.65%
    2026-07-19 05:37:53,336 [INFO] [CpuWorker] Current Load: 31.56%
    2026-07-19 05:37:56,465 [INFO] [CpuWorker] Current Load: 39.01%
    2026-07-19 05:37:59,587 [INFO] [CpuWorker] Current Load: 48.35%
    2026-07-19 05:38:02,717 [INFO] [CpuWorker] Current Load: 55.95%
    2026-07-19 05:38:02,824 [CRITICAL] [CpuWorker] CPU Threshold Violated! (55.949999999999996%).
    
    analyst@a73fa66c6583:/workspace$ tail -n 20 "$RUN_DIR/monitor.tsv"
    2026-07-19T05:37:42+00:00	3801	SN	0.9	16756	16.36	1	00:04	agent-leak-app-
    2026-07-19T05:37:43+00:00	3801	SN	0.7	16756	16.36	1	00:05	agent-leak-app-
    2026-07-19T05:37:44+00:00	3801	SN	0.9	16756	16.36	1	00:06	agent-leak-app-
    2026-07-19T05:37:45+00:00	3801	SN	0.8	16756	16.36	1	00:07	agent-leak-app-
    2026-07-19T05:37:46+00:00	3801	SN	0.7	16756	16.36	1	00:08	agent-leak-app-
    2026-07-19T05:37:47+00:00	3801	SN	0.8	16756	16.36	1	00:09	agent-leak-app-
    2026-07-19T05:37:48+00:00	3801	SN	0.7	16756	16.36	1	00:10	agent-leak-app-
    2026-07-19T05:37:49+00:00	3801	SN	0.7	16756	16.36	1	00:11	agent-leak-app-
    2026-07-19T05:37:50+00:00	3801	SN	0.8	16756	16.36	1	00:12	agent-leak-app-
    2026-07-19T05:37:51+00:00	3801	SN	0.7	16756	16.36	1	00:13	agent-leak-app-
    2026-07-19T05:37:52+00:00	3801	SN	0.7	16756	16.36	1	00:14	agent-leak-app-
    2026-07-19T05:37:53+00:00	3801	SN	0.8	16756	16.36	1	00:15	agent-leak-app-
    2026-07-19T05:37:54+00:00	3801	SN	0.8	16756	16.36	1	00:16	agent-leak-app-
    2026-07-19T05:37:55+00:00	3801	SN	0.7	16756	16.36	1	00:17	agent-leak-app-
    2026-07-19T05:37:56+00:00	3801	SN	0.9	16756	16.36	1	00:18	agent-leak-app-
    2026-07-19T05:37:58+00:00	3801	SN	0.8	16756	16.36	1	00:19	agent-leak-app-
    2026-07-19T05:37:59+00:00	3801	SN	0.8	16756	16.36	1	00:20	agent-leak-app-
    2026-07-19T05:38:00+00:00	3801	SN	1.0	16756	16.36	1	00:21	agent-leak-app-
    2026-07-19T05:38:01+00:00	3801	SN	0.9	16756	16.36	1	00:22	agent-leak-app-
    2026-07-19T05:38:02+00:00	3801	SN	0.9	16756	16.36	1	00:23	agent-leak-app-

    - 앱 내부 정책에 의해 종료됨(실제 OS CPU를 과점유 한 것으로 보이지는 않음)
    - Launcher도 확인했으나 그렇게까지 오르지 않음

### After

    export CASE_NAME=cpu
    export RUN_ID=after-02
    export MEMORY_LIMIT=512
    export CPU_MAX_OCCUPY=10
    export MULTI_THREAD_ENABLE=false

    source scripts/prepare-runtime.sh
    scripts/start-app.sh

    analyst@a73fa66c6583:/workspace$ tail -n 40 "$RUN_DIR/console.log"
    2026-07-19 05:51:35,306 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
    2026-07-19 05:51:36,115 [INFO] [MemoryWorker] Current Heap: 75MB
    2026-07-19 05:51:36,313 [INFO] [CpuWorker] Current Load: 10.00%
    2026-07-19 05:51:39,141 [INFO] [MemoryWorker] Current Heap: 100MB
    2026-07-19 05:51:39,437 [INFO] [CpuWorker] Current Load: 8.88%
    2026-07-19 05:51:42,166 [INFO] [MemoryWorker] Current Heap: 125MB
    2026-07-19 05:51:42,563 [INFO] [CpuWorker] Current Load: 6.43%
    2026-07-19 05:51:44,680 [INFO] [CpuWorker] Cooldown complete (5.00%). Resuming load increase...
    2026-07-19 05:51:45,190 [INFO] [MemoryWorker] Current Heap: 150MB
    2026-07-19 05:51:45,690 [INFO] [CpuWorker] Current Load: 5.00%
    2026-07-19 05:51:47,815 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
    2026-07-19 05:51:48,215 [INFO] [MemoryWorker] Current Heap: 175MB

    analyst@a73fa66c6583:/workspace$ tail -n 20 "$RUN_DIR/monitor.tsv"
    2026-07-19T05:51:29+00:00	4412	SN	1.9	16680	16.29	1	00:02	agent-leak-app-
    2026-07-19T05:51:30+00:00	4412	SNl	1.9	42544	41.55	3	00:03	agent-leak-app-
    2026-07-19T05:51:31+00:00	4412	SNl	1.4	42544	41.55	3	00:04	agent-leak-app-
    2026-07-19T05:51:32+00:00	4412	SNl	1.1	42544	41.55	3	00:05	agent-leak-app-
    2026-07-19T05:51:33+00:00	4412	SNl	1.3	68148	66.55	3	00:06	agent-leak-app-
    2026-07-19T05:51:34+00:00	4412	SNl	1.1	68148	66.55	3	00:07	agent-leak-app-
    2026-07-19T05:51:35+00:00	4412	SNl	0.9	68148	66.55	3	00:08	agent-leak-app-
    2026-07-19T05:51:36+00:00	4412	SNl	0.9	93752	91.55	3	00:09	agent-leak-app-
    2026-07-19T05:51:37+00:00	4412	SNl	0.9	93752	91.55	3	00:10	agent-leak-app-
    2026-07-19T05:51:38+00:00	4412	SNl	0.8	93752	91.55	3	00:11	agent-leak-app-
    2026-07-19T05:51:39+00:00	4412	SNl	0.8	119356	116.56	3	00:12	agent-leak-app-
    2026-07-19T05:51:40+00:00	4412	SNl	0.8	119356	116.56	3	00:13	agent-leak-app-
    2026-07-19T05:51:41+00:00	4412	SNl	0.7	119356	116.56	3	00:14	agent-leak-app-
    2026-07-19T05:51:42+00:00	4412	SNl	0.7	144960	141.56	3	00:15	agent-leak-app-
    2026-07-19T05:51:43+00:00	4412	SNl	0.8	144960	141.56	3	00:16	agent-leak-app-
    2026-07-19T05:51:44+00:00	4412	SNl	0.7	144960	141.56	3	00:17	agent-leak-app-
    2026-07-19T05:51:45+00:00	4412	SNl	0.7	170564	166.57	3	00:18	agent-leak-app-
    2026-07-19T05:51:46+00:00	4412	SNl	0.7	170564	166.57	3	00:19	agent-leak-app-
    2026-07-19T05:51:47+00:00	4412	SNl	0.6	170564	166.57	3	00:20	agent-leak-app-
    2026-07-19T05:51:48+00:00	4412	SNl	0.6	196168	191.57	3	00:21	agent-leak-app-

    - flush, cooldown으로 인해 종료되지 않음

## Deadlock

### Before

    export CASE_NAME=deadlock
    export RUN_ID=before-01
    export MEMORY_LIMIT=512
    export CPU_MAX_OCCUPY=10
    export MULTI_THREAD_ENABLE=true

    source scripts/prepare-runtime.sh
    scripts/start-app.sh

    tail -n 40 "$RUN_DIR/console.log"
    2026-07-19 05:55:45,847 [WARNING] [AgentWorker] Initializing concurrent transaction processors...
    2026-07-19 05:55:45,848 [WARNING] [System] CAUTION: Strict resource locking is enabled.
    2026-07-19 05:55:50,881 [INFO] [Worker-Thread-1] Process Started. Attempting to lock [Shared_Memory_A]...
    2026-07-19 05:55:50,882 [INFO] [AgentWorker][Worker-Thread-2] Process Started. Attempting to lock [Socket_Pool_B]...
    2026-07-19 05:55:50,882 [INFO] [AgentWorker] Waiting for worker threads to complete transactions...
    2026-07-19 05:55:50,882 [INFO] [AgentWorker][Worker-Thread-1] LOCK ACQUIRED: [Shared_Memory_A]. (Holding...)
    2026-07-19 05:55:50,882 [INFO] [AgentWorker][Worker-Thread-2] LOCK ACQUIRED: [Socket_Pool_B]. (Holding...)
    2026-07-19 05:55:50,883 [INFO] [AgentWorker][Worker-Thread-1] Processing critical data in Memory A...
    2026-07-19 05:55:50,883 [INFO] [AgentWorker][Worker-Thread-2] Establishing network connections in Pool B...
    2026-07-19 05:55:52,899 [INFO] [AgentWorker][Worker-Thread-1] Need resource [Socket_Pool_B] to finish job.
    2026-07-19 05:55:52,900 [INFO] [AgentWorker][Worker-Thread-2] Need resource [Shared_Memory_A] to write logs.
    2026-07-19 05:55:52,901 [INFO] [AgentWorker][Worker-Thread-1] WAITING for [Socket_Pool_B]... (Status: BLOCKED)
    2026-07-19 05:55:52,901 [INFO] [AgentWorker][Worker-Thread-2] WAITING for [Shared_Memory_A]... (Status: BLOCKED)

    analyst@a73fa66c6583:/workspace$ tail -n 20 "$RUN_DIR/monitor.tsv"
    2026-07-19T05:56:57+00:00	4613	SNl	0.0	16820	16.43	3	01:13	agent-leak-app-
    2026-07-19T05:56:58+00:00	4613	SNl	0.0	16820	16.43	3	01:14	agent-leak-app-
    2026-07-19T05:56:59+00:00	4613	SNl	0.0	16820	16.43	3	01:15	agent-leak-app-
    2026-07-19T05:57:00+00:00	4613	SNl	0.0	16820	16.43	3	01:16	agent-leak-app-
    2026-07-19T05:57:01+00:00	4613	SNl	0.0	16820	16.43	3	01:17	agent-leak-app-
    2026-07-19T05:57:02+00:00	4613	SNl	0.0	16820	16.43	3	01:18	agent-leak-app-
    2026-07-19T05:57:03+00:00	4613	SNl	0.0	16820	16.43	3	01:19	agent-leak-app-
    2026-07-19T05:57:04+00:00	4613	SNl	0.0	16820	16.43	3	01:20	agent-leak-app-
    2026-07-19T05:57:05+00:00	4613	SNl	0.0	16820	16.43	3	01:21	agent-leak-app-
    2026-07-19T05:57:06+00:00	4613	SNl	0.0	16820	16.43	3	01:22	agent-leak-app-
    2026-07-19T05:57:07+00:00	4613	SNl	0.0	16820	16.43	3	01:23	agent-leak-app-
    2026-07-19T05:57:08+00:00	4613	SNl	0.0	16820	16.43	3	01:24	agent-leak-app-
    2026-07-19T05:57:09+00:00	4613	SNl	0.0	16820	16.43	3	01:26	agent-leak-app-
    2026-07-19T05:57:10+00:00	4613	SNl	0.0	16820	16.43	3	01:27	agent-leak-app-
    2026-07-19T05:57:11+00:00	4613	SNl	0.0	16820	16.43	3	01:28	agent-leak-app-
    2026-07-19T05:57:12+00:00	4613	SNl	0.0	16820	16.43	3	01:29	agent-leak-app-
    2026-07-19T05:57:13+00:00	4613	SNl	0.0	16820	16.43	3	01:30	agent-leak-app-
    2026-07-19T05:57:14+00:00	4613	SNl	0.0	16820	16.43	3	01:31	agent-leak-app-
    2026-07-19T05:57:15+00:00	4613	SNl	0.0	16820	16.43	3	01:32	agent-leak-app-
    2026-07-19T05:57:16+00:00	4613	SNl	0.0	16820	16.43	3	01:33	agent-leak-app-

    - PID 살아있었음.

### After

    export CASE_NAME=deadlock
    export RUN_ID=after-01
    export MEMORY_LIMIT=512
    export CPU_MAX_OCCUPY=10
    export MULTI_THREAD_ENABLE=false

    source scripts/prepare-runtime.sh
    scripts/start-app.sh

    tail -n 40 "$RUN_DIR/console.log"
    2026-07-19 07:09:13,487 [INFO] [Scheduler] Task Scheduler Initialized.
    2026-07-19 07:09:13,488 [INFO] [Scheduler] Registered Tasks: ['Thread-A', 'Thread-B', 'Thread-C']
    2026-07-19 07:09:13,488 [INFO] [Scheduler] Starting task execution...
    2026-07-19 07:09:13,489 [INFO] [Thread-A] Task Started. Calculating... (20%)
    2026-07-19 07:09:13,540 [INFO] [Thread-A] Calculating... (40%)
    2026-07-19 07:09:13,596 [INFO] [Thread-A] Calculating... (60%)
    2026-07-19 07:09:13,652 [INFO] [Thread-A] Calculating... (80%)
    2026-07-19 07:09:13,708 [INFO] [Thread-A] Task Completed. (100%)
    2026-07-19 07:09:13,761 [INFO] [Thread-B] Task Started. Calculating... (20%)
    2026-07-19 07:09:13,815 [INFO] [Thread-B] Calculating... (40%)
    2026-07-19 07:09:13,868 [INFO] [Thread-B] Calculating... (60%)
    2026-07-19 07:09:13,921 [INFO] [Thread-B] Calculating... (80%)
    2026-07-19 07:09:13,976 [INFO] [Thread-B] Task Completed. (100%)
    2026-07-19 07:09:14,031 [INFO] [Thread-C] Task Started. Calculating... (20%)
    2026-07-19 07:09:14,083 [INFO] [Thread-C] Calculating... (40%)
    2026-07-19 07:09:14,135 [INFO] [Thread-C] Calculating... (60%)
    2026-07-19 07:09:14,190 [INFO] [Thread-C] Calculating... (80%)
    2026-07-19 07:09:14,243 [INFO] [Thread-C] Task Completed. (100%)
    2026-07-19 07:09:14,297 [INFO] [Scheduler] All tasks completed.
    2026-07-19 07:09:14,306 [INFO] [MemoryWorker] Current Heap: 25MB
    2026-07-19 07:09:14,307 [INFO] [CpuWorker] Started. Maximum CPU Limit: 10%
    2026-07-19 07:09:14,308 [INFO] [CpuWorker] Current Load: 5.00%
    2026-07-19 07:09:17,337 [INFO] [MemoryWorker] Current Heap: 50MB
    2026-07-19 07:09:17,436 [INFO] [CpuWorker] Current Load: 6.57%
    2026-07-19 07:09:19,550 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
    2026-07-19 07:09:20,369 [INFO] [MemoryWorker] Current Heap: 75MB
    2026-07-19 07:09:20,552 [INFO] [CpuWorker] Current Load: 10.00%
    2026-07-19 07:09:23,405 [INFO] [MemoryWorker] Current Heap: 100MB
    2026-07-19 07:09:23,679 [INFO] [CpuWorker] Current Load: 5.78%
    2026-07-19 07:09:25,797 [INFO] [CpuWorker] Cooldown complete (5.00%). Resuming load increase...
    2026-07-19 07:09:26,436 [INFO] [MemoryWorker] Current Heap: 125MB
    2026-07-19 07:09:26,809 [INFO] [CpuWorker] Current Load: 5.00%
    2026-07-19 07:09:29,463 [INFO] [MemoryWorker] Current Heap: 150MB
    2026-07-19 07:09:29,940 [INFO] [CpuWorker] Current Load: 5.40%
    2026-07-19 07:09:32,493 [INFO] [MemoryWorker] Current Heap: 175MB
    2026-07-19 07:09:33,071 [INFO] [CpuWorker] Current Load: 9.32%
    2026-07-19 07:09:35,190 [INFO] [CpuWorker] Peak reached (10.00%). Starting cooldown...
    2026-07-19 07:09:35,525 [INFO] [MemoryWorker] Current Heap: 200MB
    2026-07-19 07:09:36,199 [INFO] [CpuWorker] Current Load: 10.00%
    2026-07-19 07:09:38,553 [INFO] [MemoryWorker] Current Heap: 225MB

    analyst@a73fa66c6583:/workspace$ tail -n 20 "$RUN_DIR/monitor.tsv"
    2026-07-19T07:09:19+00:00	5234	SNl	1.1	68168	66.57	3	00:08	agent-leak-app-
    2026-07-19T07:09:20+00:00	5234	SNl	1.2	93772	91.57	3	00:09	agent-leak-app-
    2026-07-19T07:09:21+00:00	5234	SNl	1.1	93772	91.57	3	00:10	agent-leak-app-
    2026-07-19T07:09:22+00:00	5234	SNl	1.0	93772	91.57	3	00:11	agent-leak-app-
    2026-07-19T07:09:23+00:00	5234	SNl	1.0	119376	116.58	3	00:12	agent-leak-app-
    2026-07-19T07:09:24+00:00	5234	SNl	1.0	119376	116.58	3	00:13	agent-leak-app-
    2026-07-19T07:09:25+00:00	5234	SNl	0.9	119376	116.58	3	00:14	agent-leak-app-
    2026-07-19T07:09:26+00:00	5234	SNl	0.9	144980	141.58	3	00:15	agent-leak-app-
    2026-07-19T07:09:27+00:00	5234	SNl	0.9	144980	141.58	3	00:16	agent-leak-app-
    2026-07-19T07:09:28+00:00	5234	SNl	0.8	144980	141.58	3	00:17	agent-leak-app-
    2026-07-19T07:09:29+00:00	5234	SNl	0.8	170584	166.59	3	00:18	agent-leak-app-
    2026-07-19T07:09:30+00:00	5234	SNl	0.8	170584	166.59	3	00:19	agent-leak-app-
    2026-07-19T07:09:31+00:00	5234	SNl	0.8	170584	166.59	3	00:20	agent-leak-app-
    2026-07-19T07:09:32+00:00	5234	SNl	0.8	196188	191.59	3	00:21	agent-leak-app-
    2026-07-19T07:09:33+00:00	5234	SNl	0.8	196188	191.59	3	00:22	agent-leak-app-
    2026-07-19T07:09:34+00:00	5234	SNl	0.8	196188	191.59	3	00:23	agent-leak-app-
    2026-07-19T07:09:35+00:00	5234	SNl	0.8	221792	216.59	3	00:24	agent-leak-app-
    2026-07-19T07:09:36+00:00	5234	SNl	0.8	221792	216.59	3	00:25	agent-leak-app-
    2026-07-19T07:09:37+00:00	5234	SNl	0.8	221792	216.59	3	00:26	agent-leak-app-
    2026-07-19T07:09:38+00:00	5234	SNl	0.8	247396	241.60	3	00:27	agent-leak-app-

