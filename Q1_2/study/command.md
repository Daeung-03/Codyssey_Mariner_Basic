## Docker

  Dockerfile:

  - FROM debian:bookworm-slim: Linux 실행 환경입니다. Debian 12 버전
  - procps: ps, top 등 관측 명령을 제공합니다.
  - iproute2: 포트 바인딩 상태를 ss로 확인할 때 씁니다.
  - analyst: 과제 요구인 “root가 아닌 일반 사용자”입니다.
  - WORKDIR /workspace: 이후 로컬 과제 폴더를 여기에 마운트할 예정. root 소유가 될 수 있으니 analysist 소유로 생성.
  - USER analyst: 컨테이너 실행 시 애플리케이션도 이 일반 사용자 권한으로 실행됩니다.
  - CMD ["bash"]: 시작 시 셸에 진입합니다. 실제 앱 실행은 다음 단계에서 명시적으로 합니다.

docker build -t agent-leak-lab:local -f docker/Dockerfile .
  
  -t 태그 설정. -f 도커파일 경로 마지막 . 빌드 컨텍스트 전달(무조건 작성해야 하는 Argument, 다만 내 경우에는 필요 없음)

docker run --rm -it \
    --name agent-leak-lab \
    -v "$PWD:/workspace" \
    -w /workspace \
    -p 15034:15034 \
    agent-leak-lab:local

  - --rm: 셸을 종료하면 컨테이너만 삭제합니다. 마운트한 로컬 파일은 삭제되지 않습니다.
  - -v "$PWD:/workspace": 현재 로컬 과제 폴더를 컨테이너 /workspace에 연결합니다.
  - -w /workspace: 컨테이너 시작 위치를 과제 폴더로 맞춥니다.
  - -p 15034:15034: 나중에 앱이 컨테이너 안에서 사용하는 15034 포트를 호스트에서도 접근 가능하게 합니다.
  - 이미지의 USER analyst가 적용되므로 root가 아닌 사용자로 시작해야 합니다.

## Prepare.sh

애플리케이션 실행 전 준비사항에 맞게 세팅하는 스크립트

  : "${CASE_NAME:=manual}"

  - CASE_NAME이 비어 있거나 없다면 manual을 넣습니다.

  export CASE_NAME RUN_ID MEMORY_LIMIT CPU_MAX_OCCUPY MULTI_THREAD_ENABLE

  export해야 이후 이 셸에서 시작할 agent-leak-app이라는 자식 프로세스가 값을 받을 수 있습니다.

  실행: source scripts/prepare-runtime.sh

   ./scripts/prepare-runtime.sh로 직접 실행하면, 폴더와 키 파일은 생성되지만 export한 값은 그 자식 셸이 끝나는 순간 사라집니다.
  앱 실행 전에 환경변수를 유지하려면 컨테이너의 Bash에서 source를 사용해야한다. 또 실험 전에 미리 값을 주면 값이 있는 변수는 덮어쓰지 않음.

## start-app.sh

앱을 백그라운드로 시작하고, 분석 대상 PID와 콘솔 로그를 실행별 증거 폴더에 남기는 실행 스크립트

  : "${RUN_DIR:?Run 'source scripts/prepare-runtime.sh' first.}"

  - RUN_DIR이 없으면 실행을 중단 후 준비 스크립트 실행

  if [[ ! -x "$APP" ]]; then

  - -x는 파일 존재와 실행 가능 여부를 검사

  "$APP" > "$RUN_DIR/console.log" 2>&1 &

  - >: 표준 출력(stdout)을 console.log로 저장합니다.
  - 2>&1: 표준 오류(stderr)도 같은 파일에 합칩니다. 부트 실패나 보호 종료 메시지도 놓치지 않기 위해서입니다.
  - &: 앱을 백그라운드로 실행합니다. 현재 셸에서 ps, top, 관제 스크립트를 이어서 실행할 수 있습니다.

  LAUNCHER_PID=$!
  스크립트를 실행한 프로세스 ID

  for _ in {1..20}; do
    WORKER_PID=$(pgrep -P "$LAUNCHER_PID" | head -n 1)

    if [[ -n "$WORKER_PID" ]]; then
      break
    fi

    sleep 0.1
  done

  - 런처가 만든 자식 프로세스를 0.1 초씩 최대 20번 반복해서 검색한다.
  - -P: 부모의 PID를 기준으로 검색(런쳐의 PID를 부모로 가지는 프로세스 검색)
  - -n: 문자열 길이가 0보다 크면 참
  - -z: -n과 반대(0이면 참)




## monitor.sh

로그 기록용 스크립트

  PID="${1:?Usage: scripts/monitor.sh <pid>}"
  INTERVAL=1

  - 첫 번째 인자에는 앱 PID를 받습니다.
  - 두 번째 인자는 측정 간격, 일단 1로 고정
  - PID가 없으면 잘못된 실행이므로 즉시 사용법을 표시합니다.

  MONITOR_LOG="$RUN_DIR/monitor.tsv"

  - tsv는 탭으로 열을 나눈 로그, 쉼표가 포함될 수 있는 명령 이름 등을 CSV에서 이스케이프하는 문제를 피함. 

  ps -p "$PID" -o pid= -o stat= -o pcpu= -o rss= -o nlwp= -o etime= -o comm=

  - stat: 프로세스 상태. Deadlock을 단독으로 판정하지는 않지만, 계속 대기 상태인지 볼 보조 정보입니다.
  - pcpu: CPU 사용률
  - rss: 물리 메모리 점유량(KB)
  - nlwp: 스레드 수
  - etime: 실행 후 경과 시간
  - comm: 실행 파일 이름

  if [[ -z "$SAMPLE" ]]; then

  대상 PID가 더 이상 없으면 OOM·CPU 케이스처럼 앱이 종료된 것. 별도 이벤트 로그에 남기고 관제를 끝냄
  Deadlock은 PID가 유지되므로 이 종료 조건에 걸리지 않고 계속 기록될 것

  read -r OBSERVED_PID STATE CPU RSS_KB THREADS ELAPSED COMMAND <<< "$SAMPLE"

  ps의 한 줄 결과를 공백 기준으로 각 변수에 분해. -r: 역슬래시를 특별하게 처리 X

## capture-snapshot.sh

종료 시점의 스냅샷 기록 스크립트

  ps -p "$PID" -o pid,ppid,user,stat,pcpu,pmem,rss,nlwp,etime,comm

  - ppid: 어떤 부모 프로세스가 시작했는지
  - user: analyst인지 확인. root 실행 금지 조건의 보조 증거가 됩니다.
  - stat: 실행/대기 등 상태
  - rss: 물리 메모리
  - nlwp: 스레드 수

  ps -eo ... --sort=-pcpu | head -n 20

  전체 프로세스를 CPU 사용률 내림차순으로 정렬해 상위 20개만 저장. 
  CPU 케이스에서 agent-leak-app이 상위에 있는지, 또는 다른 프로세스가 원인인지 비교하는 자료

  top -b -H -n 1 -p "$PID"

  - -b: 대화형 화면이 아니라 파일에 저장 가능한 배치 모드
  - -H: 프로세스 대신 스레드를 표시
  - -n 1: 한 번만 출력
  - -p "$PID": 대상 프로세스와 그 스레드로 범위를 제한