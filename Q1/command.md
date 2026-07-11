## 1. Docker run

  docker run \
    --name agent-q1 \
    --hostname agent-q1 \
    --cap-add NET_ADMIN \
    --security-opt apparmor=unconfined \
    -p 20022:20022 \
    -p 15034:15034 \
    -v /Users/hugeung/Documents/Codyssey/Codyssey_Mariner_Basic/Q1:/workspace \
    -w /workspace \
    -d ubuntu:22.04 sleep infinity

- hostname agent-q1: 컨테이너 내부 호스트명을 agent-q1으로 지정. 
- cap--add NET_ADMIN: 컨테이너에 네트워크 관리 권한 추가, 컨테이너 내부에서 UFW 방화벽 정책을 설정하고 활성화하려면 네트워크 관리 권한이 필요함
- security-opt apparmor=unconfined: AppArmor 보안 프로필 제한 완화 -> Docker 기본 보안 정책 제한으로 ufw/iptables 계열 명령이 막힐 수 있음

## 2. SSH 설정
root@agent-q1:/workspace# cat /etc/ssh/sshd_config.d/99-agent-q1.conf
Port 20022
PermitRootLogin no
- SSH에서 RootLogin 방지(다만 도커 명령어로 접속이 가능함. 이번에는 그냥 SSH 접속만 막아보자)

## 3. 계정 생성
  groupadd agent-common
  groupadd agent-core

  useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
  useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
  useradd -m -s /bin/bash -G agent-common agent-test

  - m 사용자의 홈 디렉토리 설정 (/Home/agent-*), 기본 설정 파일들(bashrc 같은거)도 복사됨
  - s 로그인 할 때 사용할 기본 쉘 지정
  - G 추가 그룹 지정(기본은 자기 자신만 있는 그룹 하나 배정 받는다)

## 4. 방화벽 설정
ufw status verbose - 상태 출력

## 5. 환경 변수 / 키 고정
  printf "%s\n" \
    "export AGENT_HOME=/home/agent-admin/agent-app" \
    "export AGENT_PORT=15034" \
    "export AGENT_UPLOAD_DIR=\$AGENT_HOME/upload_files" \
    "export AGENT_KEY_PATH=\$AGENT_HOME/api_keys" \
    "export AGENT_LOG_DIR=/var/log/agent-app" \
    > /etc/profile.d/agent-app.sh

    profile.d: 해당 계정으로 로그인 하면 안에 있는 모든 스크립트를 실행함\

## 8. Monitor.sh 실행

## 12. cron
  cron_line='* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1'
  tmp=$(mktemp)
  crontab -u agent-admin -l 2>/dev/null | grep -vF '/home/agent-admin/agent-app/bin/monitor.sh' > "$tmp" || true
  printf "%s\n" "$cron_line" >> "$tmp"
  crontab -u agent-admin "$tmp"
                 tail -n 5 /var/log/agent-app/monitor.logrm -f "$tmp"