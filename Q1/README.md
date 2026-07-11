# Q1 리눅스 서버 운영 환경 구축 과제

## 과제 개요

이 과제는 macOS 호스트에서 Docker 기반 Ubuntu 22.04 컨테이너를 만들고, 그 안에 Agent 애플리케이션을 실행할 수 있는 리눅스 운영 환경을 구성하는 과제이다.

핵심 목표는 단순히 앱을 실행하는 것이 아니라, 실제 서버 운영에 필요한 기본 보안, 권한 분리, 실행 환경 고정, 모니터링 자동화, 로그 누적 구조를 직접 구성하고 검증하는 것이다.

구성 대상은 다음과 같다.

- SSH 포트 변경 및 root 원격 로그인 차단
- UFW 방화벽 정책 구성
- `agent-admin`, `agent-dev`, `agent-test` 계정 생성
- `agent-common`, `agent-core` 그룹 기반 권한 분리
- Agent 앱 실행 디렉터리 및 로그 디렉터리 권한 설정
- 앱 실행 환경 변수와 API 키 파일 구성
- Agent 앱 부팅 및 포트 리슨 검증
- `monitor.sh`를 통한 프로세스, 포트, 리소스 상태 점검
- `cron`을 통한 모니터링 자동 실행
- `/var/log/agent-app/monitor.log` 누적 기록 관리

## 수행 요약

macOS에서는 Docker 컨테이너 제어와 저장소 파일 관리를 수행하고, SSH, 방화벽, 계정, 권한, cron 등 리눅스 운영 설정은 Ubuntu 22.04 컨테이너 내부에서 수행했다.

컨테이너는 `agent-q1` 이름으로 실행했으며, SSH 포트 `20022`와 Agent 앱 포트 `15034`를 호스트에 게시했다. UFW 방화벽 설정을 위해 `NET_ADMIN` capability를 추가했다.

제공된 Agent 앱 바이너리 중 컨테이너 아키텍처에 맞는 ARM64 바이너리를 선택하여 `/home/agent-admin/agent-app/agent-app` 경로에 배치했다.

사용자와 그룹은 역할에 따라 분리했다.

- `agent-admin`: 앱 실행 및 cron 실행 계정
- `agent-dev`: `monitor.sh` 소유 및 관리 계정
- `agent-test`: 테스트 계정
- `agent-common`: 세 계정이 모두 포함되는 공용 그룹
- `agent-core`: `agent-admin`, `agent-dev`만 포함되는 운영 그룹

디렉터리 권한은 공유 영역과 보안 영역을 분리하도록 설정했다.

- `upload_files`: `agent-common` 그룹이 읽고 쓸 수 있는 공유 디렉터리
- `api_keys`: `agent-core` 그룹만 접근 가능한 키 디렉터리
- `/var/log/agent-app`: `agent-core` 그룹만 접근 가능한 로그 디렉터리
- `bin`: 운영 스크립트를 보관하는 실행 디렉터리

`agent-test`가 `upload_files`에는 접근해야 하지만 상위 디렉터리인 `$AGENT_HOME`의 민감한 영역에는 접근하면 안 되므로, ACL을 사용해 `agent-common` 그룹에 `$AGENT_HOME` 통과 권한만 부여했다.

Agent 앱 실행 과정에서는 제공 앱의 실제 동작과 초기 요구 경로 사이에 차이가 있었다. 과제 요구에 따라 `t_secret.key`를 만들었고, 앱 바이너리가 요구하는 `secret.key`도 같은 내용으로 추가했다. 또한 앱은 `AGENT_KEY_PATH`를 키 파일 경로가 아니라 키 디렉터리 경로로 기대했으므로 실행 환경에서는 `/home/agent-admin/agent-app/api_keys`로 맞췄다.

`monitor.sh`는 Bash로 작성했으며 다음 기능을 수행한다.

- Agent 앱 프로세스 확인
- TCP `15034` LISTEN 상태 확인
- UFW 또는 firewalld 활성 상태 확인
- CPU, 메모리, 루트 디스크 사용률 수집
- 임계값 초과 시 경고 출력
- `/var/log/agent-app/monitor.log`에 구조화된 로그 1줄 추가
- `monitor.log`가 10MB를 넘으면 최대 10개까지 회전 보관

마지막으로 `agent-admin` 계정의 crontab에 `monitor.sh`를 매분 실행하도록 등록했다.

## 제출 산출물

- `README.md`: 수행 내역서 및 학습 목표 답안
- `monitor.sh`: 시스템 상태 수집 및 로깅 자동화 스크립트

## 실행 기록 증거

아래 영역은 재실행 후 실제 출력으로 채운다.

### 1. Docker 컨테이너 및 포트 게시 확인

```bash
hugeung@gimdaeung-ui-MacBookAir ~ %  docker run \                
    --name agent-q1 \
    --hostname agent-q1 \
    --cap-add NET_ADMIN \
    --security-opt apparmor=unconfined \
    -p 20022:20022 \
    -p 15034:15034 \
    -v /Users/hugeung/Documents/Codyssey/Codyssey_Mariner_Basic/Q1:/workspace \
    -w /workspace \
    -d ubuntu:22.04 sleep infinity

hugeung@gimdaeung-ui-MacBookAir ~ % docker ps -a
CONTAINER ID   IMAGE          COMMAND            CREATED         STATUS         PORTS                                                                                              NAMES
9db04647e3dd   ubuntu:22.04   "sleep infinity"   4 minutes ago   Up 4 minutes   0.0.0.0:15034->15034/tcp, [::]:15034->15034/tcp, 0.0.0.0:20022->20022/tcp, [::]:20022->20022/tcp   agent-q1

hugeung@gimdaeung-ui-MacBookAir ~ % docker port agent-q1
15034/tcp -> 0.0.0.0:15034
15034/tcp -> [::]:15034
20022/tcp -> 0.0.0.0:20022
20022/tcp -> [::]:20022
```

### 2. 파일복사, SSH 포트 변경 및 root 원격 접속 차단 확인

```bash
hugeung@gimdaeung-ui-MacBookAir ~ % docker exec -it agent-q1 bash
root@agent-q1:/workspace# uname -m
aarch64

root@agent-q1:/workspace#   mkdir -p /home/agent-admin/agent-app
root@agent-q1:/workspace# cp /workspace/agent-app/agent-app-linux-arm64 /home/agent-admin/agent-app/agent-app
root@agent-q1:/workspace# chmod 755 /home/agent-admin/agent-app/agent-app
root@agent-q1:/workspace# ls -l /home/agent-admin/agent-app
total 7364
-rwxr-xr-x 1 root root 7537848 Jul  5 05:47 agent-app
root@agent-q1:/workspace# test -x /home/agent-admin/agent-app/agent-app && echo executable=ok
executable=ok

root@agent-q1:/workspace# mkdir -p /etc/ssh/sshd_config.d /run/sshd
root@agent-q1:/workspace#   printf "%s\n" \
    "Port 20022" \
    "PermitRootLogin no" \
    > /etc/ssh/sshd_config.d/99-agent-q1.conf

// root 계정 비밀번호 설정
root@agent-q1:/workspace# passwd root
New password: 
Retype new password: 
passwd: password updated successfully

// 컨테이너 내부에서 로그인 성공
agent-admin@agent-q1:~$ su root
Password: 
root@agent-q1:/home/agent-admin#

// SSH 외부에서 접속 시도
hugeung@gimdaeung-ui-MacBookAir ~ % ssh -p 20022 agent-admin@localhost
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.12.72-linuxkit aarch64)
agent-admin@agent-q1:~$ // agent-admin 계정은 성공함

hugeung@gimdaeung-ui-MacBookAir ~ % ssh -p 20022 root@localhost
root@localhost's password: 
Permission denied, please try again.
root@localhost's password: 
Permission denied, please try again.
root@localhost's password: 
root@localhost: Permission denied (publickey,password) // 비밀번호 정확하게 입력해도 실패함
```

### 3. UFW 방화벽 활성화 및 허용 포트 확인

```bash
root@agent-q1:/workspace#   ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 20022/tcp
  ufw allow 15034/tcp
  ufw --force enable

root@agent-q1:/workspace#   ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
20022/tcp                  ALLOW IN    Anywhere                  
15034/tcp                  ALLOW IN    Anywhere                  
20022/tcp (v6)             ALLOW IN    Anywhere (v6)             
15034/tcp (v6)             ALLOW IN    Anywhere (v6)  
```

### 4. 계정 및 그룹 생성 확인

```bash
root@agent-q1:/workspace#   useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
  useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
  useradd -m -s /bin/bash -G agent-common agent-test

root@agent-q1:/workspace#  id agent-admin
  id agent-dev
  id agent-test
  getent group agent-common
  getent group agent-core
uid=1000(agent-admin) gid=1002(agent-admin) groups=1002(agent-admin),1000(agent-common),1001(agent-core)
uid=1001(agent-dev) gid=1003(agent-dev) groups=1003(agent-dev),1000(agent-common),1001(agent-core)
uid=1002(agent-test) gid=1004(agent-test) groups=1004(agent-test),1000(agent-common)
agent-common:x:1000:agent-admin,agent-dev,agent-test
agent-core:x:1001:agent-admin,agent-dev
```

### 5. 디렉터리 권한 및 ACL 확인

```bash
export AGENT_HOME=/home/agent-admin/agent-app

mkdir -p "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app

chown agent-admin:agent-core "$AGENT_HOME"
chown agent-admin:agent-core "$AGENT_HOME/agent-app" 2>/dev/null || true
chown agent-admin:agent-common "$AGENT_HOME/upload_files"
chown agent-admin:agent-core "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
chmod 750 "$AGENT_HOME"
chmod 755 "$AGENT_HOME/agent-app" 2>/dev/null || true
chmod 770 "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" /var/log/agent-app
chmod 750 "$AGENT_HOME/bin"

root@agent-q1:/workspace# ls -ld "$AGENT_HOME" "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
drwxr-x--- 5 agent-admin agent-core   4096 Jul  5 08:40 /home/agent-admin/agent-app
drwxrwx--- 2 agent-admin agent-core   4096 Jul  5 08:40 /home/agent-admin/agent-app/api_keys
drwxr-x--- 2 agent-admin agent-core   4096 Jul  5 08:40 /home/agent-admin/agent-app/bin
drwxrwx--- 2 agent-admin agent-common 4096 Jul  5 08:40 /home/agent-admin/agent-app/upload_files
drwxrwx--- 2 agent-admin agent-core   4096 Jul  5 08:40 /var/log/agent-app

root@agent-q1:/workspace# getfacl "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" /var/log/agent-app
getfacl: Removing leading '/' from absolute path names
# file: home/agent-admin/agent-app/upload_files
# owner: agent-admin
# group: agent-common
user::rwx
group::rwx
other::---

# file: home/agent-admin/agent-app/api_keys
# owner: agent-admin
# group: agent-core
user::rwx
group::rwx
other::---

# file: var/log/agent-app
# owner: agent-admin
# group: agent-core
user::rwx
group::rwx
other::---

// agent-app -> common 실행 가능하게
root@agent-q1:/workspace# setfacl -m g:agent-common:--x /home/agent-admin/agent-app //핵심~!!!!!!
root@agent-q1:/workspace# getfacl /home/agent-admin/agent-app /home/agent-admin/agent-app/upload_files
getfacl: Removing leading '/' from absolute path names
# file: home/agent-admin/agent-app
# owner: agent-admin
# group: agent-core
user::rwx
group::r-x
group:agent-common:--x
mask::r-x
other::---

# file: home/agent-admin/agent-app/upload_files
# owner: agent-admin
# group: agent-common
user::rwx
group::rwx
other::---

```

### 6. 환경 변수 및 키 파일 확인

```bash
// 환경 변수 고정을 위해 profile.d 파일로 관리
root@agent-q1:/workspace# cat /etc/profile.d/agent-app.sh 
  export AGENT_HOME=/home/agent-admin/agent-app
  export AGENT_PORT=15034
  export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
  export AGENT_KEY_PATH=$AGENT_HOME/api_keys
  export AGENT_LOG_DIR=/var/log/agent-app

printf "%s\n" "agent_api_key_test" > /home/agent-admin/agent-app/api_keys/t_secret.key
cp /home/agent-admin/agent-app/api_keys/t_secret.key /home/agent-admin/agent-app/api_keys/secret.key

root@agent-q1:/workspace#   ls -l /etc/profile.d/agent-app.sh \
    /home/agent-admin/agent-app/api_keys/t_secret.key \
    /home/agent-admin/agent-app/api_keys/secret.key
-rw-r--r-- 1 root        root       212 Jul  5 08:50 /etc/profile.d/agent-app.sh
-rw-r----- 1 agent-admin agent-core  19 Jul  5 08:51 /home/agent-admin/agent-app/api_keys/secret.key
-rw-r----- 1 agent-admin agent-core  19 Jul  5 08:51 /home/agent-admin/agent-app/api_keys/t_secret.key

root@agent-q1:/workspace# su - agent-test -c 'test -r /home/agent-admin/agent-app/api_keys/t_secret.key||echo agent-test-key-read: deny'
agent-test-key-read: deny
```

### 7. Agent 앱 Boot Sequence 및 포트 리슨 확인

```bash
su - agent-admin -c 'cd "$AGENT_HOME" && nohup ./agent-app > /var/log/agent-app/agent-app.out 2>&1 & echo app_pid=$!'
app_pid=4271

root@agent-q1:/workspace# cat /var/log/agent-app/agent-app.out
>>> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
   ... Running as service user 'agent-admin' (uid=1000)
[2/5] Verifying Environment Variables     [OK]
   ... All required Envs correct
[3/5] Checking Required Files             [OK]
   ... Verified 'secret.key' with correct key string.
[4/5] Checking Port Availability          [OK]
   ... Port 15034 is available.
[5/5] Verifying Log Permission            [OK]
   ... Log directory is writable: /var/log/agent-app
------------------------------------------------------------
All Boot Checks Passed!
Agent READY
2026-07-05 09:00:02,077 [INFO] [SafetyGuard] Process priority lowered (nice=10).
2026-07-05 09:00:02,077 [INFO] Agent listening at port 15034
2026-07-05 09:00:02,077 [INFO] === Agent Worker Started ===
2026-07-05 09:00:02,077 [INFO]    > Cycle: 0 -> 256MB/Lv10 -> 0
2026-07-05 09:00:02,077 [INFO] --- Step Info: Mode=UP, CPU Lv=1, Mem=0MB ---
2026-07-05 09:00:02,090 [INFO] [Memory] Increasing... (+25 MB) Total: 25 MB
2026-07-05 09:00:02,090 [INFO] [CPU] Occupy core for 1s (Level 1)
2026-07-05 09:00:04,096 [INFO] --- Step Info: Mode=UP, CPU Lv=2, Mem=25MB ---
2026-07-05 09:00:04,111 [INFO] [Memory] Increasing... (+25 MB) Total: 50 MB
2026-07-05 09:00:04,111 [INFO] [CPU] Occupy core for 2s (Level 2)
2026-07-05 09:00:07,117 [INFO] --- Step Info: Mode=UP, CPU Lv=3, Mem=50MB ---
2026-07-05 09:00:07,133 [INFO] [Memory] Increasing... (+25 MB) Total: 75 MB
2026-07-05 09:00:07,133 [INFO] [CPU] Occupy core for 3s (Level 3)
2026-07-05 09:00:11,137 [INFO] --- Step Info: Mode=UP, CPU Lv=4, Mem=75MB ---
2026-07-05 09:00:11,154 [INFO] [Memory] Increasing... (+25 MB) Total: 100 MB
2026-07-05 09:00:11,154 [INFO] [CPU] Occupy core for 4s (Level 4)
2026-07-05 09:00:16,156 [INFO] --- Step Info: Mode=UP, CPU Lv=5, Mem=100MB ---
2026-07-05 09:00:16,176 [INFO] [Memory] Increasing... (+25 MB) Total: 125 MB

root@agent-q1:/workspace# ss -tulnp | grep ':15034'
tcp   LISTEN 0      1            0.0.0.0:15034      0.0.0.0:*

```

### 8. monitor.sh 수동 실행 결과 확인

```bash
root@agent-q1:/workspace# su - agent-admin -c '/home/agent-admin/agent-app/bin/monitor.sh'
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent-app'... [OK] (PID: 4316)
Checking port 15034... [OK]
Firewall UFW... [OK]

[RESOURCE MONITORING]
CPU Usage : 0.3%
MEM Usage : 6.4%
DISK Used  : 2%


[INFO] Log appended: /var/log/agent-app/monitor.log

root@agent-q1:/workspace# tail -n 5 /var/log/agent-app/monitor.log
[2026-07-05 09:09:01] PID:4316 CPU:0.3% MEM:6.4% DISK_USED:2%
```

### 9. monitor.log 누적 기록 확인

```bash
 su - agent-admin -c '/home/agent-admin/agent-app/bin/monitor.sh'
 sleep 2
 x3

root@agent-q1:/workspace# tail -n 5 /var/log/agent-app/monitor.log
[2026-07-05 09:09:01] PID:4316 CPU:0.3% MEM:6.4% DISK_USED:2%
[2026-07-05 09:09:49] PID:4316 CPU:0.5% MEM:9.1% DISK_USED:2%
[2026-07-05 09:09:52] PID:4316 CPU:1.6% MEM:9.2% DISK_USED:2%
[2026-07-05 09:09:55] PID:4316 CPU:0.8% MEM:9.2% DISK_USED:2%
```

### 10. cron 등록 및 자동 실행 확인

```bash
root@agent-q1:/workspace# service cron start
 * Starting periodic command scheduler cron                              [ OK ] 
root@agent-q1:/workspace# service cron status
 * cron is running

root@agent-q1:/workspace# cron_line='* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-  cron.out 2>&1'

root@agent-q1:/workspace#   
  tmp=$(mktemp)
  crontab -u agent-admin -l 2>/dev/null | grep -vF '/home/agent-admin/agent-app/bin/monitor.sh' > "$tmp" || true
  printf "%s\n" "$cron_line" >> "$tmp"
  crontab -u agent-admin "$tmp"
  rm -f "$tmp"

root@agent-q1:/workspace# crontab -u agent-admin -l
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1

root@agent-q1:/workspace#   before=$(wc -l < /var/log/agent-app/monitor.log 2>/dev/null || echo 0)
  echo before_lines=$before

  sleep 60

  after=$(wc -l < /var/log/agent-app/monitor.log 2>/dev/null || echo 0)
  echo after_lines=$after
before_lines=6
after_lines=7


root@agent-q1:/workspace# tail -n 5 /var/log/agent-app/monitor.log
[2026-07-05 09:09:55] PID:4316 CPU:0.8% MEM:9.2% DISK_USED:2%
[2026-07-05 09:14:02] PID:4316 CPU:1.2% MEM:7.1% DISK_USED:2%
[2026-07-05 09:15:02] PID:4316 CPU:0.9% MEM:9.3% DISK_USED:2%
[2026-07-05 09:16:02] PID:4316 CPU:0.9% MEM:7.3% DISK_USED:2%
[2026-07-05 09:17:02] PID:4316 CPU:0.5% MEM:8.2% DISK_USED:2%

root@agent-q1:/workspace#  tail -n 20 /var/log/agent-app/monitor-cron.out
CPU Usage : 0.9%
MEM Usage : 7.3%
DISK Used  : 2%


[INFO] Log appended: /var/log/agent-app/monitor.log
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent-app'... [OK] (PID: 4316)
Checking port 15034... [OK]
Firewall UFW... [OK]

[RESOURCE MONITORING]
CPU Usage : 0.5%
MEM Usage : 8.2%
DISK Used  : 2%


[INFO] Log appended: /var/log/agent-app/monitor.log
```

## 학습 목표 답안

### SSH 포트 변경과 root 원격 접속 차단이 기본 보안인 이유

SSH는 서버에 원격으로 로그인할 수 있는 핵심 진입점이다. 기본 포트인 `22`번은 자동 스캔과 무차별 대입 공격의 주요 대상이 되기 쉽다. 포트를 `20022`처럼 변경하면 보안을 완성하는 것은 아니지만, 기본 포트를 대상으로 하는 자동화 공격 노출을 줄일 수 있다.

root 원격 접속 차단은 더 중요하다. root는 시스템 전체 권한을 가진 계정이므로 원격 로그인에 성공하면 피해 범위가 즉시 전체 시스템으로 확대된다. 일반 계정으로 접속한 뒤 필요한 경우 제한적으로 권한을 상승시키는 방식이 감사와 통제에 더 유리하다.

### 필요한 포트만 허용하는 방화벽 정책을 구성하고 검증하는 방법

방화벽은 기본적으로 들어오는 연결을 차단하고, 서비스 운영에 필요한 포트만 허용하는 방식으로 구성한다. 이 과제에서는 SSH용 TCP `20022`와 Agent 앱용 TCP `15034`만 허용하면 된다.

UFW를 사용하는 경우 정책은 다음 흐름으로 구성한다.

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 20022/tcp
ufw allow 15034/tcp
ufw --force enable
ufw status verbose
```

검증할 때는 `ufw status verbose`로 기본 정책이 `deny incoming`인지, 허용 목록에 `20022/tcp`와 `15034/tcp`만 있는지 확인한다. Docker 환경에서는 컨테이너 내부 방화벽뿐 아니라 `docker port agent-q1`로 호스트 포트 게시 상태도 함께 확인해야 한다.

### 역할 기반 계정/그룹과 ACL로 공유 디렉터리와 보안 디렉터리를 분리하는 이유

운영 환경에서는 모든 사용자가 같은 권한을 가지면 안 된다. 역할별로 계정과 그룹을 나누면 필요한 사람에게 필요한 권한만 줄 수 있다.

이 과제에서는 `agent-common`과 `agent-core`를 분리했다. `agent-common`은 `agent-admin`, `agent-dev`, `agent-test`가 모두 포함되는 공용 그룹이고, `agent-core`는 운영 성격의 `agent-admin`, `agent-dev`만 포함하는 제한 그룹이다.

`upload_files`는 테스트 계정도 접근해야 하는 공유 디렉터리이므로 `agent-common`에 읽기/쓰기 권한을 준다. 반면 `api_keys`와 `/var/log/agent-app`은 키와 운영 로그를 포함하므로 `agent-core`만 접근해야 한다.

ACL은 기본 Unix 소유자/그룹/기타 권한만으로 표현하기 어려운 예외 권한을 줄 때 사용한다. 여기서는 `$AGENT_HOME`이 `agent-core` 중심으로 제한되어 있어 `agent-test`가 `upload_files`까지 도달할 수 없었기 때문에, `agent-common`에 상위 디렉터리 통과 권한만 부여했다. 이렇게 하면 공유 디렉터리는 사용할 수 있지만 키 디렉터리나 로그 디렉터리에는 접근할 수 없다.

### 환경 변수로 실행 환경을 고정하는 이유와 검증 방법

환경 변수는 애플리케이션이 사용할 경로, 포트, 로그 위치, 키 위치를 코드나 명령어에 흩어 놓지 않고 한곳에서 고정하기 위해 사용한다. 이렇게 하면 실행 계정이나 셸이 바뀌어도 앱이 같은 설정으로 실행되며, 운영 환경과 테스트 환경의 차이도 명확히 관리할 수 있다.

이 과제의 주요 환경 변수는 다음과 같다.

- `AGENT_HOME`: Agent 앱 홈 디렉터리
- `AGENT_PORT`: 앱 리슨 포트
- `AGENT_UPLOAD_DIR`: 업로드 파일 디렉터리
- `AGENT_KEY_PATH`: 키 경로
- `AGENT_LOG_DIR`: 로그 디렉터리

검증은 앱 실행 계정인 `agent-admin`으로 전환한 뒤 `printenv | grep '^AGENT_'`를 실행해 실제 로그인 셸에서 값이 로드되는지 확인한다. 또한 `ls -l`로 키 파일과 로그 디렉터리의 소유자, 그룹, 권한이 의도와 맞는지 확인한다.

### 쉘 스크립트로 상태를 수집하고 로그로 남기는 운영 흐름

운영 중 장애를 분석하려면 현재 상태뿐 아니라 과거 상태 기록이 필요하다. `monitor.sh`는 Agent 앱 프로세스와 포트 상태를 먼저 확인하고, CPU, 메모리, 디스크 사용량을 수집한 뒤 결과를 로그로 남긴다.

프로세스나 포트가 비정상이면 서비스가 정상 동작하지 않는 상태이므로 `exit 1`로 실패를 반환한다. 반면 방화벽 비활성이나 리소스 임계값 초과는 즉시 스크립트를 중단하기보다 `[WARNING]`을 출력해 운영자가 상태를 파악할 수 있게 한다.

로그는 다음 형식으로 누적한다.

```text
[YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%
```

이런 형식의 로그가 쌓이면 장애 시점의 프로세스 상태, 리소스 사용량, 반복적인 임계값 초과 여부를 추적할 수 있다.

### crontab 주기 실행과 로그 보존 정책이 필요한 이유

모니터링은 한 번 실행해서 끝나는 작업이 아니라 주기적으로 실행되어야 의미가 있다. `cron`을 사용하면 사용자가 직접 명령을 입력하지 않아도 `monitor.sh`를 매분 자동 실행할 수 있다.

이 과제에서는 `agent-admin` 계정의 crontab에 다음 형태로 등록한다.

```cron
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1
```

등록 후에는 1~2분 뒤 `/var/log/agent-app/monitor.log`의 라인 수가 증가했는지 확인해 자동 실행 여부를 검증한다.

로그 보존 정책도 필요하다. 로그를 무제한으로 쌓으면 디스크가 가득 차서 앱이나 시스템이 장애를 일으킬 수 있다. 따라서 `monitor.log`가 커지면 10MB 단위로 회전하고 최대 10개 파일만 유지하도록 제한한다. 장기 운영 환경에서는 여기에 압축, 아카이브 이동, 오래된 로그 삭제 정책까지 추가해 디스크 사용량과 장애 분석 가능성을 함께 관리한다.

## 구현 중 확인한 주요 결정

| 항목 | 결정 | 이유 |
| --- | --- | --- |
| 실행 환경 | macOS 호스트 + Ubuntu 22.04 Docker 컨테이너 | 리눅스 운영 설정을 macOS에 직접 적용하지 않기 위해 |
| 방화벽 | UFW 사용 | Ubuntu에서 간단하고 검증이 쉬움 |
| 컨테이너 capability | `NET_ADMIN` 추가 | 컨테이너 내부 UFW 활성화를 위해 필요 |
| 앱 실행 계정 | `agent-admin` | root 실행 금지 요구사항 충족 |
| 스크립트 소유자 | `agent-dev:agent-core` | 작성/관리 역할과 실행 권한 분리 |
| cron 실행 계정 | `agent-admin` | 앱 운영 계정 기준으로 주기 실행 |
| 공유 권한 | `upload_files`는 `agent-common`, 민감 디렉터리는 `agent-core` | 협업 가능 영역과 보안 영역 분리 |
| ACL 사용 | `$AGENT_HOME`에 `agent-common` 통과 권한 부여 | `agent-test`가 공유 디렉터리에만 도달하도록 제한 |
| 로그 회전 | `monitor.sh` 내부에서 10MB/10개 유지 | 별도 logrotate 설정 없이 요구사항 충족 |
