Step 0부터 Step 7까지는 “macOS에서 Docker로 Ubuntu 컨테이너를 만들고, 그 안에 Agent 앱이 정상 실행될 수 있는 Linux 환경을 구성한 과정”입니다.

  Step 0: Docker 컨테이너 실행

  Ubuntu 22.04 컨테이너 agent-q1을 만들고 실행했습니다.

  docker run ... ubuntu:22.04 sleep infinity

  핵심은 컨테이너를 계속 켜두기 위해 sleep infinity를 사용했고, 외부에서 접근할 포트도 열었다는 점입니다.

  - 20022:20022: SSH 접속용
  - 15034:15034: Agent 앱 접속용
  - --cap-add NET_ADMIN: UFW 방화벽 설정을 위해 필요
  - -v ...:/workspace: macOS 작업 폴더를 컨테이너 안에 연결

  즉, macOS는 Docker를 조작하는 역할이고, 실제 Linux 과제 작업은 컨테이너 안에서 하도록 만든 겁니다.

  Step 1: 앱 바이너리 선택

  컨테이너 CPU 구조를 확인했습니다.

  uname -m

  결과가 aarch64라서 ARM64용 바이너리인 agent-app-linux-arm64를 선택했습니다.

  그 파일을 실행 위치로 복사했습니다.

  cp /workspace/agent-app/agent-app-linux-arm64 /home/agent-admin/agent-app/agent-app
  chmod 755 /home/agent-admin/agent-app/agent-app

  즉, 제공된 실행 파일 중 컨테이너에서 실행 가능한 파일을 골라 /home/agent-admin/agent-app/agent-app로 준비한 단계입니다.


  apt-get install -y openssh-server iproute2

  설정 파일에는 다음 내용을 넣었습니다.

  Port 20022
  PermitRootLogin no

  의미는:

  - SSH는 기본 포트 22가 아니라 20022에서 받음
  - root 계정으로 SSH 접속 금지

  그 다음 sshd -t로 설정 문법을 검사하고, /usr/sbin/sshd로 SSH 서버를 실행했습니다.

  마지막으로 ss -tulnp | grep ':20022'와 nc -zv localhost 20022로 포트가 열렸는지 확인했습니다.

  Step 3: 방화벽 설정

  UFW를 설치해서 방화벽 정책을 만들었습니다.

  apt-get install -y ufw iptables

  정책은 단순합니다.

  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 20022/tcp
  ufw allow 15034/tcp
  ufw --force enable

  의미는:

  - 기본적으로 외부에서 들어오는 연결은 막음
  - 나가는 연결은 허용
  - SSH 포트 20022 허용
  - Agent 앱 포트 15034 허용

  ufw status verbose로 실제 정책이 적용됐는지 확인했습니다.

  Step 4: 계정과 그룹 생성

  과제에서 요구하는 사용자와 그룹을 만들었습니다.

  사용자:

  - agent-admin
  - agent-dev
  - agent-test

  그룹:

  - agent-common
  - agent-core

  구성은 이렇게 했습니다.

  - agent-admin: 앱 실행 계정
  - agent-dev: 모니터링 스크립트 관리 계정
  - agent-test: 일반 테스트 계정
  - agent-common: 세 사용자 모두 포함
  - agent-core: agent-admin, agent-dev만 포함

  즉, 공용 작업은 agent-common, 민감한 앱 관리 작업은 agent-core로 분리한 겁니다.

  Step 5: 디렉터리와 권한 설정

  앱에 필요한 디렉터리를 만들었습니다.

  /home/agent-admin/agent-app
  /home/agent-admin/agent-app/upload_files
  /home/agent-admin/agent-app/api_keys
  /home/agent-admin/agent-app/bin
  /var/log/agent-app

  권한 의도는 다음과 같습니다.

  - upload_files: 세 사용자 공통 접근 가능
  - api_keys: agent-admin, agent-dev만 접근 가능
  - bin: 실행 스크립트 저장 위치, core 그룹만 접근
  - /var/log/agent-app: 앱 로그 저장 위치, core 그룹만 접근

  그리고 한 가지 문제가 있었습니다.

  upload_files는 agent-test도 접근해야 하는데, 상위 디렉터리인 /home/agent-admin/agent-app가 agent-core 전용이라서 agent-test가 들어갈 수 없었습니다.

  그래서 ACL을 추가했습니다.

  setfacl -m g:agent-common:--x /home/agent-admin/agent-app

  이건 agent-common에게 상위 디렉터리를 “통과만” 할 수 있게 해주는 설정입니다. 파일 목록을 보거나 민감 디렉터리에 접근하는 권한은 주지 않고, upload_files까
  지 도달할 수만 있게 한 겁니다.

  Step 6: 앱 환경변수와 키 파일 설정

  앱이 실행될 때 필요한 환경변수를 /etc/profile.d/agent-app.sh에 설정했습니다.

  초기 계획은 이렇게 잡았습니다.

  AGENT_HOME=/home/agent-admin/agent-app
  AGENT_PORT=15034
  AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
  AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys/t_secret.key
  AGENT_LOG_DIR=/var/log/agent-app

  그리고 키 파일을 만들었습니다.

  printf "%s\n" "agent_api_key_test" > /home/agent-admin/agent-app/api_keys/t_secret.key
  chown agent-admin:agent-core ...
  chmod 640 ...

  즉, 키 파일은 agent-admin이 소유하고, agent-core 그룹까지만 읽을 수 있게 했습니다.

  Step 7: 앱 실행과 부팅 검증

  앱을 반드시 root가 아니라 agent-admin으로 실행했습니다.

  su - agent-admin -c 'cd "$AGENT_HOME" && nohup ./agent-app > /var/log/agent-app/agent-app.out 2>&1 &'

  처음에는 실패했습니다.

  이유는 실제 앱 바이너리가 AGENT_KEY_PATH를 “키 파일 경로”가 아니라 “키 디렉터리 경로”로 기대했기 때문입니다.

  그래서 환경변수를 이렇게 수정했습니다.

  AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys

  그 다음 또 한 번 실패했는데, 이번에는 앱이 secret.key라는 고정 파일명을 찾고 있었습니다.

  그래서 기존 과제용 키 파일 t_secret.key는 그대로 두고, 앱 실행을 위해 같은 내용의 secret.key를 추가했습니다.

  cp t_secret.key secret.key
  chown agent-admin:agent-core secret.key
  chmod 640 secret.key

  그 후 다시 실행했더니 부팅 체크가 모두 통과했습니다.

  [1/5] Checking User Account               [OK]
  [2/5] Verifying Environment Variables     [OK]
  [3/5] Checking Required Files             [OK]
  [4/5] Checking Port Availability          [OK]
  [5/5] Verifying Log Permission            [OK]
  Agent READY

  마지막으로 포트도 확인했습니다.

  ss -tulnp | grep ':15034'

  결과적으로 Agent 앱이 0.0.0.0:15034에서 정상적으로 실행되는 것을 확인했습니다.

  Step 8: 모니터링 스크립트 설치와 수동 검증

  Agent 앱 상태를 확인하는 monitor.sh를 만들고 컨테이너 안의 실행 위치에 설치했습니다.

  /home/agent-admin/agent-app/bin/monitor.sh

  권한은 다음처럼 맞췄습니다.

  - 소유자: agent-dev
  - 그룹: agent-core
  - 권한: 750

  의미는:

  - agent-dev가 스크립트를 관리함
  - agent-core 그룹인 agent-admin, agent-dev만 실행 가능
  - agent-test는 실행 불가

  스크립트는 다음 내용을 확인합니다.

  - Agent 앱 프로세스가 떠 있는지
  - 15034 포트가 열려 있는지
  - UFW 방화벽이 활성 상태인지
  - CPU, 메모리, 디스크 사용량이 어느 정도인지

  수동으로 한 번 실행해서 `/var/log/agent-app/monitor.log`에 로그가 추가되는지도 확인했습니다.

  Step 9: cron 등록

  monitor.sh가 1분마다 자동 실행되도록 cron에 등록했습니다.

  처음 확인했을 때 컨테이너에는 cron이 설치되어 있지 않았습니다.

  그래서 cron 패키지를 설치했습니다.

  apt-get update
  apt-get install -y cron

  Docker 컨테이너는 일반 Linux 서버처럼 systemd가 자동으로 서비스를 띄우지 않기 때문에, cron 데몬을 직접 시작했습니다.

  service cron start

  그 다음 root가 아니라 agent-admin의 crontab에 등록했습니다.

  * * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1

  의미는:

  - `* * * * *`: 매분 실행
  - `/home/agent-admin/agent-app/bin/monitor.sh`: 실행할 모니터링 스크립트
  - `>> /var/log/agent-app/monitor-cron.out`: cron 실행 출력 저장
  - `2>&1`: 에러 출력도 같은 파일에 저장

  마지막으로 실제 자동 실행 여부를 확인했습니다.

  확인 전 monitor.log 줄 수:

  before_lines=3

  70초 대기 후 monitor.log 줄 수:

  after_lines=4

  즉, cron이 monitor.sh를 자동으로 실행했고, 그 결과 monitor.log에 새 기록이 1줄 추가됐습니다.

  추가된 로그 예시는 다음과 같습니다.

  [2026-07-05 05:09:02] PID:5119 CPU:1.4% MEM:9.7% DISK_USED:2%

  cron 실행 출력도 별도 파일에 저장되는 것을 확인했습니다.

  /var/log/agent-app/monitor-cron.out

  최종적으로 Step 9에서 확인한 내용은 다음과 같습니다.

  - cron 설치 완료
  - cron 데몬 실행 중
  - agent-admin crontab에 1분 주기 등록 완료
  - monitor.log가 실제로 증가함
  - cron 실행 출력 로그도 생성됨

  주의할 점:

  현재 컨테이너에서는 `service cron start`로 cron을 직접 띄웠습니다. 컨테이너를 재시작하거나 새로 만들면 cron도 다시 시작해야 합니다.
