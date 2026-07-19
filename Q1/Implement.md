# Q1 Implementation Notes

This document records the actual implementation work performed for each step.

## Step 0: Build and Start Linux Container

### Goal

Create an Ubuntu 22.04 Linux environment in Docker from the macOS host.

The container is used for Linux-specific assignment work such as SSH, firewall,
users/groups, permissions, app execution, monitoring, and cron. The macOS host is
used only for Docker control and repository editing.

### Commands and Work Performed

```bash
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
```

Started a long-running Ubuntu 22.04 container.

Explanation:

- `--name agent-q1`: assigns the required container name.
- `--hostname agent-q1`: sets the container hostname for easier identification.
- `--cap-add NET_ADMIN`: allows later firewall work such as UFW rule handling.
- `--security-opt apparmor=unconfined`: reduces container security restrictions that can interfere with firewall testing.
- `-p 20022:20022`: exposes the container SSH port.
- `-p 15034:15034`: exposes the Agent app port.
- `-v ...:/workspace`: mounts the repository into the container.
- `-w /workspace`: sets the default working directory inside the container.
- `sleep infinity`: keeps the container running for interactive setup.

```bash
docker port agent-q1
```

Verified Docker port publishing.

Observed result:

```text
15034/tcp -> 0.0.0.0:15034
15034/tcp -> [::]:15034
20022/tcp -> 0.0.0.0:20022
20022/tcp -> [::]:20022
```

## Step 1: Select App Binary

### Goal

Select the Agent app binary that matches the container architecture and place it
under `AGENT_HOME`.

The selected runtime path is:

```text
/home/agent-admin/agent-app/agent-app
```

### Commands and Work Performed

```bash
docker exec agent-q1 bash -lc 'uname -m'
```

Checked the container architecture.

Observed result:

```text
aarch64
```

Because the container architecture is `aarch64`, the ARM64 app binary was selected:

```text
/workspace/agent-app/agent-app-linux-arm64
```

```bash
docker exec agent-q1 bash -lc 'ls -l /workspace/agent-app'
```

Checked the provided app binaries.

Observed files:

```text
agent-app-linux-arm64
agent-app-linux-x86
```

```bash
docker exec agent-q1 bash -lc 'mkdir -p /home/agent-admin/agent-app && cp /workspace/agent-app/agent-app-linux-arm64 /home/agent-admin/agent-app/agent-app && chmod 755 /home/agent-admin/agent-app/agent-app && ls -l /home/agent-admin/agent-app'
```

Created the app directory, copied the ARM64 binary into it, renamed it to
`agent-app`, and made it executable.

Explanation:

- `mkdir -p /home/agent-admin/agent-app`: creates the planned `AGENT_HOME`
  directory.
- `cp .../agent-app-linux-arm64 .../agent-app`: copies the architecture-matching
  binary to the runtime app path.
- `chmod 755 .../agent-app`: allows the app file to be executed.

Observed result:

```text
-rwxr-xr-x 1 root root ... agent-app
```

```bash
docker exec agent-q1 bash -lc 'test -x /home/agent-admin/agent-app/agent-app && echo executable=ok'
```

Verified that the copied app file is executable.

Observed result:

```text
executable=ok
```

Current note:

The file is temporarily owned by `root:root` because assignment users and groups
have not been created yet. Ownership will be corrected in the later
accounts/permissions steps.

## Step 2: Configure SSH

### Goal

Configure SSH inside the container so that:

- SSH listens on TCP port `20022`.
- Root remote login is disabled.
- The container exposes SSH through Docker port mapping `20022:20022`.

### Commands and Work Performed

```bash
docker exec agent-q1 bash -lc 'command -v sshd || true'
docker exec agent-q1 bash -lc 'dpkg -s openssh-server 2>/dev/null | grep Status || true'
```

Checked whether the SSH server was already installed.

No SSH server was found, so the required packages were installed.

```bash
docker exec agent-q1 bash -lc 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server iproute2'
```

Installed two packages:

- `openssh-server`: provides the SSH server daemon, `sshd`.
- `iproute2`: provides the `ss` command used to verify listening ports.

```bash
docker exec agent-q1 bash -lc 'mkdir -p /etc/ssh/sshd_config.d /run/sshd'
```

Created required directories.

Explanation:

- `/etc/ssh/sshd_config.d`: directory for additional SSH server configuration
  files.
- `/run/sshd`: runtime directory required by `sshd` when it starts.

```bash
docker exec agent-q1 bash -lc 'printf "%s\n" "Port 20022" "PermitRootLogin no" > /etc/ssh/sshd_config.d/99-agent-q1.conf'
```

Created the assignment-specific SSH configuration file:

```text
/etc/ssh/sshd_config.d/99-agent-q1.conf
```

Written content:

```text
Port 20022
PermitRootLogin no
```

Explanation:

- `Port 20022`: changes the SSH listening port from the default `22` to `20022`.
- `PermitRootLogin no`: blocks remote SSH login as `root`.

```bash
docker exec agent-q1 bash -lc 'sshd -t'
```

Checked the SSH server configuration syntax.

Explanation:

- `sshd -t` validates the configuration without starting the server.
- No output and exit code `0` means the SSH configuration is valid.

```bash
docker exec agent-q1 bash -lc '/usr/sbin/sshd'
```

Started the SSH daemon directly.

Explanation:

Containers often do not run a full `systemd` init system, so SSH was started
directly with `/usr/sbin/sshd` instead of relying on service auto-start.

```bash
docker exec agent-q1 bash -lc 'grep -R -E "^(Port|PermitRootLogin)" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf'
```

Verified the active SSH configuration files contain the required settings.

Observed result:

```text
/etc/ssh/sshd_config.d/99-agent-q1.conf:Port 20022
/etc/ssh/sshd_config.d/99-agent-q1.conf:PermitRootLogin no
```

```bash
docker exec agent-q1 bash -lc 'ss -tulnp | grep ":20022"'
```

Verified that `sshd` is listening on TCP port `20022`.

Observed result:

```text
tcp LISTEN ... 0.0.0.0:20022 ... users:(("sshd",pid=3676,...))
tcp LISTEN ... [::]:20022 ... users:(("sshd",pid=3676,...))
```

```bash
docker port agent-q1 20022
```

Verified that Docker exposes the container SSH port to the macOS host.

Observed result:

```text
0.0.0.0:20022
[::]:20022
```

```bash
nc -zv localhost 20022
```

Verified from the macOS host that TCP port `20022` is reachable.

Observed result:

```text
Connection to localhost port 20022 [tcp/*] succeeded!
```

Current note:

SSH login as `agent-admin` has not been tested yet because the `agent-admin`
account is created in a later step.

## Step 3: Configure Firewall

### Goal

Configure the container firewall so that:

- Inbound TCP `20022` is allowed for SSH.
- Inbound TCP `15034` is allowed for the Agent app.
- Other inbound traffic is denied by default.

UFW was selected because it is the recommended firewall implementation in
`PLAN.md` for Ubuntu 22.04.

### Commands and Work Performed

```bash
docker exec agent-q1 bash -lc 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ufw iptables'
```

Installed UFW and iptables support packages inside the Ubuntu container.

Explanation:

- `ufw`: provides the firewall command and policy layer.
- `iptables`: provides packet filtering support used by UFW.

```bash
docker exec agent-q1 bash -lc 'ufw --force reset && ufw default deny incoming && ufw default allow outgoing && ufw allow 20022/tcp && ufw allow 15034/tcp && ufw --force enable'
```

Configured and enabled the firewall policy.

Explanation:

- `ufw --force reset`: clears any previous rules so this step is reproducible.
- `ufw default deny incoming`: denies inbound ports unless explicitly allowed.
- `ufw default allow outgoing`: keeps outbound package and network access usable.
- `ufw allow 20022/tcp`: allows SSH on the assignment port.
- `ufw allow 15034/tcp`: allows the Agent app port.
- `ufw --force enable`: activates UFW without an interactive prompt.

Observed result:

```text
Default incoming policy changed to 'deny'
Default outgoing policy changed to 'allow'
Rules updated
Rules updated (v6)
Firewall is active and enabled on system startup
```

```bash
docker exec agent-q1 bash -lc 'ufw status verbose'
```

Verified the active firewall policy and allowed ports.

Observed result:

```text
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

```bash
docker port agent-q1
```

Verified Docker host port publishing for both required ports.

Observed result:

```text
15034/tcp -> 0.0.0.0:15034
15034/tcp -> [::]:15034
20022/tcp -> 0.0.0.0:20022
20022/tcp -> [::]:20022
```

```bash
nc -zv localhost 20022
nc -zv localhost 15034
```

Verified from the macOS host that both published TCP ports are reachable.

Observed result:

```text
Connection to localhost port 20022 [tcp/*] succeeded!
Connection to localhost port 15034 [tcp/*] succeeded!
```

Current note:

UFW activated successfully because the container was started with `NET_ADMIN`
capability in Step 0.

## Step 4: Create Accounts and Groups

Create the required Linux accounts and groups inside the container:

- Accounts: `agent-admin`, `agent-dev`, `agent-test`
- `agent-common`: `agent-admin`, `agent-dev`, `agent-test`
- `agent-core`: `agent-admin`, `agent-dev`

### Commands and Work Performed

```bash
docker exec agent-q1 bash -lc 'getent passwd agent-admin agent-dev agent-test; getent group agent-common agent-core'
```

Checked whether the target accounts and groups already existed.

Observed result:

```text
No matching users or groups were found.
```

```bash
docker exec agent-q1 bash -lc '
set -e
getent group agent-common >/dev/null || groupadd agent-common
getent group agent-core >/dev/null || groupadd agent-core
id agent-admin >/dev/null 2>&1 || useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
id agent-dev >/dev/null 2>&1 || useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
id agent-test >/dev/null 2>&1 || useradd -m -s /bin/bash -G agent-common agent-test
id agent-admin
id agent-dev
id agent-test
getent group agent-common
getent group agent-core
'
```

Created the required groups first, then created each account with the required
supplementary group membership.

Explanation:

- `agent-common`: shared group for all assignment users.
- `agent-core`: restricted group for `agent-admin` and `agent-dev`.
- `agent-admin`: app runtime account, member of `agent-common` and `agent-core`.
- `agent-dev`: monitoring script owner, member of `agent-common` and `agent-core`.
- `agent-test`: test account, member of `agent-common` only.
- The command is idempotent because it checks for existing groups and users
  before creating them.

Observed result:

```text
useradd: warning: the home directory /home/agent-admin already exists.
useradd: Not copying any file from skel directory into it.
uid=1000(agent-admin) gid=1002(agent-admin) groups=1002(agent-admin),1000(agent-common),1001(agent-core)
uid=1001(agent-dev) gid=1003(agent-dev) groups=1003(agent-dev),1000(agent-common),1001(agent-core)
uid=1002(agent-test) gid=1004(agent-test) groups=1004(agent-test),1000(agent-common)
agent-common:x:1000:agent-admin,agent-dev,agent-test
agent-core:x:1001:agent-admin,agent-dev
```

Current note:

The `agent-admin` home directory already existed because Step 1 created
`/home/agent-admin/agent-app` before the account was added. This warning is
expected and does not affect the required account or group membership. Ownership
of app directories will be corrected in the later permissions step.

## Step 5: Create Directories and Permissions

### Goal

Create the required Agent app directories and apply the collaboration and
minimum-permission policy.

Required directories:

```text
/home/agent-admin/agent-app
/home/agent-admin/agent-app/upload_files
/home/agent-admin/agent-app/api_keys
/home/agent-admin/agent-app/bin
/var/log/agent-app
```

### Commands and Work Performed

```bash
docker exec agent-q1 bash -lc '
set -euo pipefail
export AGENT_HOME=/home/agent-admin/agent-app
if ! command -v getfacl >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y acl
fi
mkdir -p "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
chown agent-admin:agent-core "$AGENT_HOME"
chown agent-admin:agent-core "$AGENT_HOME/agent-app" 2>/dev/null || true
chown agent-admin:agent-common "$AGENT_HOME/upload_files"
chown agent-admin:agent-core "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
chmod 750 "$AGENT_HOME"
chmod 755 "$AGENT_HOME/agent-app" 2>/dev/null || true
chmod 770 "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" /var/log/agent-app
chmod 750 "$AGENT_HOME/bin"
ls -ld "$AGENT_HOME" "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
getfacl "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" /var/log/agent-app
'
```

Created the required directories, installed `acl` for `getfacl` verification,
and applied the planned ownership and mode values.

Explanation:
- `set -euo pipefail`: failed if just one inst fail or undefined var
- `$AGENT_HOME`: owned by `agent-admin:agent-core`, mode `750`.
- `upload_files`: owned by `agent-admin:agent-common`, mode `770`.
- `api_keys`: owned by `agent-admin:agent-core`, mode `770`.
- `bin`: owned by `agent-admin:agent-core`, mode `750`.
- `/var/log/agent-app`: owned by `agent-admin:agent-core`, mode `770`.
- The copied app binary was changed from `root:root` to
  `agent-admin:agent-core` and kept executable.

Observed result:

```text
drwxr-x--- 5 agent-admin agent-core   4096 Jul  4 07:42 /home/agent-admin/agent-app
drwxrwx--- 2 agent-admin agent-core   4096 Jul  4 07:42 /home/agent-admin/agent-app/api_keys
drwxr-x--- 2 agent-admin agent-core   4096 Jul  4 07:42 /home/agent-admin/agent-app/bin
drwxrwx--- 2 agent-admin agent-common 4096 Jul  4 07:42 /home/agent-admin/agent-app/upload_files
drwxrwx--- 2 agent-admin agent-core   4096 Jul  4 07:42 /var/log/agent-app
```

Initial ACL verification:

```text
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
```

Permission check found that `agent-test` could not traverse `$AGENT_HOME` to
reach `upload_files`, because `$AGENT_HOME` is `750` and grouped as
`agent-core`.

```bash
docker exec agent-q1 bash -lc '
set -euo pipefail
setfacl -m g:agent-common:--x /home/agent-admin/agent-app
getfacl /home/agent-admin/agent-app /home/agent-admin/agent-app/upload_files
su - agent-test -c "touch /home/agent-admin/agent-app/upload_files/agent-test-write-check && rm /home/agent-admin/agent-app/upload_files/agent-test-write-check && echo agent-test-upload-write=ok"
'
```

Added an ACL entry granting `agent-common` execute-only traversal on
`$AGENT_HOME`. This preserves the restricted `agent-core` group ownership while
allowing common users to access the explicitly shared upload directory.


Observed result:

```text
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

agent-test-upload-write=ok
```

Final permission verification after Step 6 key file creation:

```bash
docker exec agent-q1 bash -lc '
set -euo pipefail
export AGENT_HOME=/home/agent-admin/agent-app
ls -ld "$AGENT_HOME" "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
getfacl "$AGENT_HOME" "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" /var/log/agent-app
su - agent-admin -c "test \"$(cat /home/agent-admin/agent-app/api_keys/t_secret.key)\" = agent_api_key_test && echo agent-admin-key-read=ok"
su - agent-dev -c "test -r /home/agent-admin/agent-app/api_keys/t_secret.key && echo agent-dev-key-read=ok"
if su - agent-test -c "test -r /home/agent-admin/agent-app/api_keys/t_secret.key"; then
  echo agent-test-key-read=unexpected
  exit 1
else
  echo agent-test-key-read=denied
fi
su - agent-test -c "touch /home/agent-admin/agent-app/upload_files/agent-test-write-check && rm /home/agent-admin/agent-app/upload_files/agent-test-write-check && echo agent-test-upload-write=ok"
'
```
Explaination:
- `su - agent-admin`: agent-admin 사용자로 로그인 셸 전환
- `C 명령어`: 문자열만 실행하고 종료
- `test 값=~`: 조건을 검사, 성공 0 반환, -r: 파일을 읽을 수 있는지 확인
- `$(명령어)`: 명령어 실행 결과를 문자열로 치환


Observed result:

```text
drwxr-x---+ 5 agent-admin agent-core   4096 Jul  4 07:42 /home/agent-admin/agent-app
drwxrwx---  2 agent-admin agent-core   4096 Jul  4 07:42 /home/agent-admin/agent-app/api_keys
drwxr-x---  2 agent-admin agent-core   4096 Jul  4 07:42 /home/agent-admin/agent-app/bin
drwxrwx---  2 agent-admin agent-common 4096 Jul  4 07:42 /home/agent-admin/agent-app/upload_files
drwxrwx---  2 agent-admin agent-core   4096 Jul  4 07:42 /var/log/agent-app

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

agent-admin-key-read=ok
agent-dev-key-read=ok
agent-test-key-read=denied
agent-test-upload-write=ok
```

Current note:

`$AGENT_HOME` shows a trailing `+` in `ls -ld` because of the ACL entry for
`agent-common` traversal. This ACL is required so `agent-test` can write to the
shared `upload_files` directory without gaining access to `api_keys` or
`/var/log/agent-app`.

## Step 6: Configure App Environment

### Goal

Configure the Agent app environment variables and create the required API key
file.

### Commands and Work Performed

```bash
docker exec agent-q1 bash -lc '
set -euo pipefail
cat > /etc/profile.d/agent-app.sh <<EOF
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=\$AGENT_HOME/upload_files
export AGENT_KEY_PATH=\$AGENT_HOME/api_keys/t_secret.key
export AGENT_LOG_DIR=/var/log/agent-app
EOF
chmod 644 /etc/profile.d/agent-app.sh
printf "%s\n" "agent_api_key_test" > /home/agent-admin/agent-app/api_keys/t_secret.key
chown agent-admin:agent-core /home/agent-admin/agent-app/api_keys/t_secret.key
chmod 640 /home/agent-admin/agent-app/api_keys/t_secret.key
su - agent-admin -c "printenv | grep ^AGENT_ | sort"
ls -l /home/agent-admin/agent-app/api_keys/t_secret.key
wc -l /home/agent-admin/agent-app/api_keys/t_secret.key
'
```

Created `/etc/profile.d/agent-app.sh` so login shells load the required app
environment, then created the required key file.

Explanation:

- `AGENT_HOME`: `/home/agent-admin/agent-app`
- `AGENT_PORT`: `15034`
- `AGENT_UPLOAD_DIR`: `$AGENT_HOME/upload_files`
- `AGENT_KEY_PATH`: `$AGENT_HOME/api_keys/t_secret.key`
- `AGENT_LOG_DIR`: `/var/log/agent-app`
- Key file content is one line: `agent_api_key_test`.
- Key file ownership is `agent-admin:agent-core`.
- Key file mode is `640`.

Observed result:

```text
AGENT_HOME=/home/agent-admin/agent-app
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys/t_secret.key
AGENT_LOG_DIR=/var/log/agent-app
AGENT_PORT=15034
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
-rw-r----- 1 agent-admin agent-core 19 Jul  4 07:42 /home/agent-admin/agent-app/api_keys/t_secret.key
1 /home/agent-admin/agent-app/api_keys/t_secret.key
```

Final verification:

```bash
docker exec agent-q1 bash -lc '
set -euo pipefail
ls -l /etc/profile.d/agent-app.sh /home/agent-admin/agent-app/api_keys/t_secret.key
su - agent-admin -c "printenv | grep ^AGENT_ | sort"
wc -c /home/agent-admin/agent-app/api_keys/t_secret.key
'
```

Observed result:

```text
-rw-r--r-- 1 root        root       215 Jul  4 07:42 /etc/profile.d/agent-app.sh
-rw-r----- 1 agent-admin agent-core  19 Jul  4 07:42 /home/agent-admin/agent-app/api_keys/t_secret.key
AGENT_HOME=/home/agent-admin/agent-app
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys/t_secret.key
AGENT_LOG_DIR=/var/log/agent-app
AGENT_PORT=15034
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
19 /home/agent-admin/agent-app/api_keys/t_secret.key
```

Current note:

The key file is 19 bytes because the required string has 18 characters plus a
single trailing newline from `printf "%s\n"`.

## Step 7: Run App and Verify Boot

Run the Agent app as `agent-admin`, verify the boot checks, and confirm that
TCP port `15034` is listening on `0.0.0.0`.

### Commands and Work Performed

Initial app start attempt:

```bash
docker exec agent-q1 bash -lc 'su - agent-admin -c "cd \$AGENT_HOME && nohup ./agent-app > /var/log/agent-app/agent-app.out 2>&1 & echo app_pid=\$!"; sleep 2; cat /var/log/agent-app/agent-app.out; ss -tulnp | grep ":15034"; ps -ef | grep -E "agent-app|agent-app-linux" | grep -v grep'
```

Started the app as `agent-admin` and captured its boot output.

Explanation:

- `cd $AGENT_HOME`: runs the binary from the app home dir.
- `nohup ./agent-app > /var/log/agent-app/agent-app.out 2>&1 &`: keeps the app
  running in the background and stores boot output in the app log dir.
- `sleep 2`: gives the app enough time to complete the boot checks.
- `cat /var/log/agent-app/agent-app.out`: captures the boot evidence.
- `ss -tulnp | grep ":15034"`: verifies the listening socket.
- `ps -ef | grep ...`: verifies the app process.

Observed result:

```text
[1/5] Checking User Account               [OK]
[2/5] Verifying Environment Variables     [FAIL]
>>> Key Path Mismatch. Expected: /home/agent-admin/agent-app/api_keys
System Boot Failed. Process Terminated.
```

Decision:

The assignment plan originally set `AGENT_KEY_PATH` to the key file path
`/home/agent-admin/agent-app/api_keys/t_secret.key`, but the provided app binary
expects `AGENT_KEY_PATH` to be the key directory path
`/home/agent-admin/agent-app/api_keys`. The runtime env was corrected to match
the actual binary behavior.

```bash
docker exec agent-q1 bash -lc 'set -euo pipefail
printf "%s\n" "export AGENT_HOME=/home/agent-admin/agent-app" "export AGENT_PORT=15034" "export AGENT_UPLOAD_DIR=\$AGENT_HOME/upload_files" "export AGENT_KEY_PATH=\$AGENT_HOME/api_keys" "export AGENT_LOG_DIR=/var/log/agent-app" > /etc/profile.d/agent-app.sh
chmod 644 /etc/profile.d/agent-app.sh
su - agent-admin -c "printenv | grep ^AGENT_ | sort"'
```

Updated the app env profile and verified the corrected runtime env.

Explanation:

- `printf ... > /etc/profile.d/agent-app.sh`: rewrites the app env profile with
  the directory-based `AGENT_KEY_PATH` expected by the binary.
- `chmod 644`: keeps the profile readable by login shells.
- `su - agent-admin -c ...`: verifies the env as the app runtime user.

Observed result:

```text
AGENT_HOME=/home/agent-admin/agent-app
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys
AGENT_LOG_DIR=/var/log/agent-app
AGENT_PORT=15034
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
```

Decision:

The provided app binary expects a fixed key filename,
`/home/agent-admin/agent-app/api_keys/secret.key`. The original required
`t_secret.key` file was kept, and a second key file with the same required test
key content was added for app compatibility.

```bash
docker exec agent-q1 bash -lc 'set -euo pipefail
cp /home/agent-admin/agent-app/api_keys/t_secret.key /home/agent-admin/agent-app/api_keys/secret.key
chown agent-admin:agent-core /home/agent-admin/agent-app/api_keys/secret.key
chmod 640 /home/agent-admin/agent-app/api_keys/secret.key
ls -l /home/agent-admin/agent-app/api_keys/t_secret.key /home/agent-admin/agent-app/api_keys/secret.key
wc -c /home/agent-admin/agent-app/api_keys/t_secret.key /home/agent-admin/agent-app/api_keys/secret.key'
```

Created the app-required `secret.key` file with the same content and permission
policy as `t_secret.key`.

Explanation:

- `cp .../t_secret.key .../secret.key`: creates the key filename required by
  the binary while preserving the assignment key file.
- `chown agent-admin:agent-core`: keeps the key owned by the runtime user and
  restricted core group.
- `chmod 640`: allows owner read/write and group read only.
- `wc -c`: verifies both key files have the same byte count.

Observed result:

```text
-rw-r----- 1 agent-admin agent-core 19 ... /home/agent-admin/agent-app/api_keys/secret.key
-rw-r----- 1 agent-admin agent-core 19 ... /home/agent-admin/agent-app/api_keys/t_secret.key
19 /home/agent-admin/agent-app/api_keys/t_secret.key
19 /home/agent-admin/agent-app/api_keys/secret.key
```

Final app start and verification:

```bash
docker exec agent-q1 bash -lc 'set -euo pipefail
pkill -u agent-admin -f /home/agent-admin/agent-app/agent-app 2>/dev/null || true
: > /var/log/agent-app/agent-app.out
chown agent-admin:agent-core /var/log/agent-app/agent-app.out
su - agent-admin -c "cd \$AGENT_HOME && nohup ./agent-app > /var/log/agent-app/agent-app.out 2>&1 & echo app_pid=\$!"
sleep 2
cat /var/log/agent-app/agent-app.out
ss -tulnp | grep ":15034"
ps -ef | grep -E "agent-app|agent-app-linux" | grep -v grep'
```

Observed result:

```text
app_pid=4969
[1/5] Checking User Account               [OK]
[2/5] Verifying Environment Variables     [OK]
[3/5] Checking Required Files             [OK]
[4/5] Checking Port Availability          [OK]
[5/5] Verifying Log Permission            [OK]
All Boot Checks Passed!
Agent READY
Agent listening at port 15034
tcp LISTEN 0 1 0.0.0.0:15034 0.0.0.0:*
./agent-app
```

Final verification summary:

- App runs as `agent-admin`, not `root`.
- All five boot checks are `[OK]`.
- Final boot output includes `Agent READY`.
- TCP `15034` is listening on `0.0.0.0`.
- The running process is `/home/agent-admin/agent-app/agent-app`.

Current note:

Step 7 required two compatibility corrections because the binary behavior
differs from the initial plan: `AGENT_KEY_PATH` must point to the key directory,
and the app requires `secret.key` inside that directory.

## Step 8: Install and Verify `monitor.sh`

Install the Bash monitoring script at `$AGENT_HOME/bin/monitor.sh`, apply the
required owner/group/mode policy, run it manually as `agent-admin`, and verify
that one structured line is appended to `/var/log/agent-app/monitor.log`.

### Implementation Plan

1. Create `monitor.sh` in the repository as the source artifact.
2. Validate Bash syntax with `bash -n`.
3. Copy the script into the running container.
4. Apply `agent-dev:agent-core` ownership and `750` mode.
5. Run the script as `agent-admin`.
6. Confirm process health, port health, firewall status, resource output, and
   monitor log accumulation.

### Commands and Work Performed

Created repository source file:

```text
/workspace/monitor.sh
```

The script implements:

- Health checks for the Agent app process and TCP `15034` LISTEN state.
- UFW/firewalld status check as a warning-only status item.
- CPU, memory, and root disk usage collection.
- Warning thresholds:
  - CPU > `20%`
  - MEM > `10%`
  - DISK_USED > `80%`
- Structured append to `/var/log/agent-app/monitor.log`.
- Script-local size rotation when `monitor.log` reaches `10MB`, preserving up
  to `10` rotated files.

Local syntax check and container installation:

```bash
bash -n monitor.sh
docker cp monitor.sh agent-q1:/home/agent-admin/agent-app/bin/monitor.sh
docker exec agent-q1 bash -lc 'set -euo pipefail
chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh
chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
bash -n /home/agent-admin/agent-app/bin/monitor.sh
ls -l /home/agent-admin/agent-app/bin/monitor.sh'
```

Observed result:

```text
-rwxr-x--- 1 agent-dev agent-core 4436 Jul  4 09:58 /home/agent-admin/agent-app/bin/monitor.sh
```

Explanation:

- `bash -n monitor.sh`: validates local Bash syntax before installation.
- `docker cp ...`: copies the repository script into `$AGENT_HOME/bin`.
- `chown agent-dev:agent-core`: sets the required script owner and group.
- `chmod 750`: allows owner full access and group read/execute only.
- `bash -n /home/.../monitor.sh`: validates the installed copy.
- `ls -l`: verifies final owner/group/mode.

Manual execution and log accumulation verification:

```bash
docker exec agent-q1 bash -lc 'set -euo pipefail
before=$(wc -l < /var/log/agent-app/monitor.log)
echo before_lines=$before
su - agent-admin -c "/home/agent-admin/agent-app/bin/monitor.sh"
after=$(wc -l < /var/log/agent-app/monitor.log)
echo after_lines=$after
tail -n 5 /var/log/agent-app/monitor.log
ps -p 5119 -o pid,user,stat,comm,args'
```

Observed result:

```text
before_lines=2
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent-app'... [OK] (PID: 5119)
Checking port 15034... [OK]
Firewall UFW... [OK]

[RESOURCE MONITORING]
CPU Usage : 1.1%
MEM Usage : 9.1%
DISK Used  : 2%

[INFO] Log appended: /var/log/agent-app/monitor.log
after_lines=3
[2026-07-04 09:57:43] PID:5118 CPU:1.3% MEM:5.9% DISK_USED:2%
[2026-07-04 09:58:45] PID:5118 CPU:0.9% MEM:8.6% DISK_USED:2%
[2026-07-04 10:00:18] PID:5119 CPU:1.1% MEM:9.1% DISK_USED:2%
  PID USER     STAT COMMAND         COMMAND
 5119 agent-a+ S    agent-app       ./agent-app
```

Final verification summary:

- `monitor.sh` is installed at `/home/agent-admin/agent-app/bin/monitor.sh`.
- Ownership is `agent-dev:agent-core`.
- Mode is `750`.
- Manual execution as `agent-admin` succeeds.
- Agent process health check succeeds with the actual app process PID `5119`.
- TCP `15034` LISTEN check succeeds.
- UFW active status is detected successfully.
- Resource values are printed.
- `monitor.log` increased from `2` lines to `3` lines.
- Latest log format matches the required pattern:
  `[YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%`.

Current note:

During verification, the first process-detection implementation selected a
shell wrapper PID when old zombie `agent-app` processes existed. The script was
updated to skip zombie processes and common shell wrappers so that the recorded
PID points to the actual app process.
## Step 9: Register Cron

Register `monitor.sh` under the `agent-admin` crontab so the monitoring script
runs once every minute inside the container.

### Commands and Work Performed

Installed cron:

docker exec agent-q1 bash -lc 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y cron'

Observed result:

- `cron` package was installed.
- Package post-install did not start the service because the container does not
  run a normal init system.

Started cron and registered the `agent-admin` crontab:

docker exec agent-q1 bash -lc 'set -euo pipefail
service cron start
cron_line="* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1"
tmp=$(mktemp)
crontab -u agent-admin -l 2>/dev/null | grep -vF "/home/agent-admin/agent-app/bin/monitor.sh" > "$tmp" || true
printf "%s\n" "$cron_line" >> "$tmp"
crontab -u agent-admin "$tmp"
rm -f "$tmp"
service cron status
crontab -u agent-admin -l'

Registered cron entry:

```cron
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1
```

Explanation:

- `service cron start`: starts the cron daemon manually inside the container.
- `crontab -u agent-admin`: installs the schedule for `agent-admin`, not root.
- `grep -vF ...`: removes any previous monitor entry before appending the new
  one, so the command is repeatable.
- `>> /var/log/agent-app/monitor-cron.out 2>&1`: keeps cron stdout/stderr in a
  separate output log.

Observed result:

```text
* cron is running
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1
```

Cron execution verification:

docker exec agent-q1 bash -lc 'set -euo pipefail
before=$(wc -l < /var/log/agent-app/monitor.log 2>/dev/null || echo 0)
echo before_lines=$before
sleep 70
after=$(wc -l < /var/log/agent-app/monitor.log 2>/dev/null || echo 0)
echo after_lines=$after
tail -n 5 /var/log/agent-app/monitor.log
printf "cron_out_lines="
wc -l < /var/log/agent-app/monitor-cron.out 2>/dev/null || echo 0
tail -n 20 /var/log/agent-app/monitor-cron.out 2>/dev/null || true'

Observed result:

```text
before_lines=3
after_lines=4
[2026-07-05 05:09:02] PID:5119 CPU:1.4% MEM:9.7% DISK_USED:2%
cron_out_lines=14
```

Final verification summary:

- Cron is installed in the container.
- Cron daemon is running.
- `agent-admin` crontab contains the required once-per-minute monitor entry.
- `/var/log/agent-app/monitor.log` grew from `3` lines to `4` lines after
  waiting for cron execution.
- `/var/log/agent-app/monitor-cron.out` captured monitor script stdout/stderr.
- Latest cron-run monitor record used the running app PID `5119`.

Current note:

Cron is started manually with `service cron start` because this Docker container
does not run systemd as PID 1. If the container is recreated or restarted, cron
must be started again unless an entrypoint starts it.
