# Q1 Assignment Plan

## 1. Goal

Build and document the assignment environment using a Linux Docker container from a macOS host.

The macOS host is used only for repository editing, Docker control, and artifact management. Linux-specific assignment work such as users/groups, SSH configuration, firewall policy, cron, permissions, ACL, and `/var/log` verification must be performed inside the Docker container.

Required submission artifacts:

1. Execution report document
2. Bash automation script: `monitor.sh`

Optional artifacts can be added only after the required scope is complete.

## 2. Assumptions

- Host OS: macOS.
- Target runtime: Ubuntu 22.04-based Docker container.
- Docker image should include or install `openssh-server`, `ufw` or `firewalld`, `cron`, `acl`, `procps`, `iproute2`, and basic shell utilities.
- Provided app is under `agent-app/`.
- App runtime account is `agent-admin`.
- Monitoring script author/owner is `agent-dev`.
- Cron execution account is `agent-admin`.
- Main app port is TCP `15034`.
- SSH port is TCP `20022`.
- `AGENT_HOME` is `/home/agent-admin/agent-app`.
- Container port mapping should expose host `20022 -> container 20022` and host `15034 -> container 15034`.

## 3. Implementation Outputs

### Required Output 1: Execution Report

Recommended file name:

- `REPORT.md`

Purpose:

- Record every setup command, configuration choice, verification result, and evidence checklist required by `Problem.md`.

Required sections:

- Host and container environment summary
- Docker image/container build and run policy
- SSH policy and verification
- Firewall policy and verification
- Account/group policy and verification
- Directory/permission/ACL policy and verification
- App environment variables and key file verification
- App boot result and listening port verification
- `monitor.sh` implementation summary
- Manual `monitor.sh` run evidence
- `monitor.log` accumulation evidence
- Cron registration and automatic execution evidence
- Log rotation or retention policy evidence

Evidence policy:

- Include command used, expected result, and actual result.
- Prefer copied terminal output snippets over prose-only explanations.
- Mask secrets if any real secret is introduced.
- The assignment key string `agent_api_key_test` may be shown because it is part of the required test fixture.
- Distinguish host-side Docker commands from container-side Linux commands.
- Note any container-specific limitation, especially if UFW cannot enforce packet filtering without extra Linux capabilities.

### Required Output 2: `monitor.sh`

Target path inside container:

- `$AGENT_HOME/bin/monitor.sh`

Repository working path:

- `monitor.sh` or `bin/monitor.sh`

Purpose:

- Check Agent app health, collect resource usage, print warnings, append one structured log line to `/var/log/agent-app/monitor.log`, and support scheduled execution by cron.

Runtime policy:

- Language: Bash only.
- Root execution is not required.
- Script should be executable by `agent-admin` through `agent-core` group membership.
- Exit `1` only when required health checks fail.
- Resource threshold and firewall warnings must not stop execution.

Ownership and permission policy:

- Owner: `agent-dev`
- Group: `agent-core`
- Mode: `750`

Health check policy:

- Process check: confirm provided app process is running.
- Process name candidates should include the actual provided executable name and, if needed, `agent_app.py`.
- Port check: confirm TCP `15034` is in `LISTEN` state.
- If either process or port check fails, print failure detail and exit `1`.

Firewall check policy:

- Support either UFW or firewalld.
- If neither is active, print `[WARNING]`.
- Do not exit non-zero only because firewall is inactive.

Resource collection policy:

- CPU usage: system CPU usage percentage.
- Memory usage: system memory usage percentage.
- Disk usage: root partition used percentage.
- Warn when:
  - CPU > `20%`
  - MEM > `10%`
  - DISK_USED > `80%`

Log policy:

- Log file: `/var/log/agent-app/monitor.log`
- Format:

```text
[YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%
```

- Append exactly one log line per successful run.
- Ensure the log directory exists or fail with a clear error if permissions prevent writing.
- Keep up to `10` rotated files of `10MB` each.
- Prefer `logrotate` if available and configurable; otherwise implement a simple Bash rotation policy.

Cron policy:

- Register under `agent-admin` crontab.
- Schedule:

```cron
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/monitor-cron.out 2>&1
```

- Verify after 1-2 minutes that `monitor.log` line count increased.

### Required Output 3: Docker Runtime Files

Recommended files:

- `Dockerfile`
- `docker-compose.yml` or documented `docker run` command
- `scripts/setup-container.sh`

Purpose:

- Create a reproducible Ubuntu container where the Linux assignment can be configured and verified from a macOS host.

Docker policy:

- Base image: `ubuntu:22.04`.
- Keep the container long-running for interactive verification.
- Publish ports:
  - `20022:20022`
  - `15034:15034`
- Mount or copy the repository/app into the container.
- Prefer explicit setup scripts over undocumented manual steps.

Container capability policy:

- SSH and cron work in a normal container.
- UFW/firewalld may require elevated container capabilities such as `NET_ADMIN`.
- If firewall activation is blocked by Docker isolation, document the limitation and verify Docker host port publishing plus firewall configuration files/status as far as the container allows.

## 4. Docker-Based Configuration Plan

### Step 0: Build and Start Linux Container

Policy:

- Use Docker from macOS to create the Ubuntu assignment environment.
- Keep Linux assignment changes inside the container or in versioned setup scripts.
- Avoid applying SSH, firewall, account, or cron changes to macOS.

Recommended container name:

- `agent-q1`

Verification from macOS host:

```bash
docker ps
docker exec -it agent-q1 bash
```

### Step 1: Select App Binary

- Choose the binary matching the container architecture:
  - `agent-app-linux-x86` for x86_64
  - `agent-app-linux-arm64` for ARM64
- Place or reference it under `$AGENT_HOME`.
- Make it executable.
- On Apple Silicon, decide based on the container architecture, not the macOS host alone.

Verification:

```bash
uname -m
ls -l "$AGENT_HOME"
```

### Step 2: Configure SSH

Policy:

- SSH listens on port `20022`.
- Root remote login is disabled.
- Container exposes SSH through Docker port mapping `20022:20022`.

Verification:

```bash
grep -E '^(Port|PermitRootLogin)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf
ss -tulnp | grep ':20022'
```

Host-side verification:

```bash
ssh -p 20022 agent-admin@localhost
```

### Step 3: Configure Firewall

Policy:

- Use one firewall implementation: UFW or firewalld.
- Allow inbound TCP `20022`.
- Allow inbound TCP `15034`.
- Deny other inbound ports by default.

Recommended choice:

- UFW, because it is common and simple on Ubuntu 22.04.
- If UFW cannot fully activate inside Docker without `NET_ADMIN`, run the container with the needed capability or document the Docker limitation in `REPORT.md`.

Verification:

```bash
sudo ufw status verbose
```

Docker exposure verification from macOS host:

```bash
docker port agent-q1
```

### Step 4: Create Accounts and Groups

Accounts:

- `agent-admin`
- `agent-dev`
- `agent-test`

Groups:

- `agent-common`: `agent-admin`, `agent-dev`, `agent-test`
- `agent-core`: `agent-admin`, `agent-dev`

Verification:

```bash
id agent-admin
id agent-dev
id agent-test
getent group agent-common
getent group agent-core
```

### Step 5: Create Directories and Permissions

Directories:

- `$AGENT_HOME`
- `$AGENT_HOME/upload_files`
- `$AGENT_HOME/api_keys`
- `$AGENT_HOME/bin`
- `/var/log/agent-app`

Policy:

- `upload_files`: group `agent-common`, read/write for common users.
- `api_keys`: group `agent-core`, read/write for core users only.
- `/var/log/agent-app`: group `agent-core`, read/write for core users only.
- `bin`: group `agent-core`, executable by core users only.

Recommended modes:

- `$AGENT_HOME`: `750`, owner `agent-admin`, group `agent-core`
- `$AGENT_HOME/upload_files`: `770`, owner `agent-admin`, group `agent-common`
- `$AGENT_HOME/api_keys`: `770`, owner `agent-admin`, group `agent-core`
- `$AGENT_HOME/bin`: `750`, owner `agent-admin`, group `agent-core`
- `/var/log/agent-app`: `770`, owner `agent-admin`, group `agent-core`

Verification:

```bash
ls -ld "$AGENT_HOME" "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_HOME/bin" /var/log/agent-app
getfacl "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" /var/log/agent-app
```

### Step 6: Configure App Environment

Required environment variables:

```bash
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys/t_secret.key
export AGENT_LOG_DIR=/var/log/agent-app
```

Key file policy:

- Path: `$AGENT_HOME/api_keys/t_secret.key`
- Content: `agent_api_key_test`
- Owner: `agent-admin`
- Group: `agent-core`
- Mode: `640`

Verification:

```bash
printenv | grep '^AGENT_'
ls -l "$AGENT_HOME/api_keys/t_secret.key"
```

### Step 7: Run App and Verify Boot

Policy:

- Run as `agent-admin`.
- Do not run as root.
- Confirm all 5 boot checks are `[OK]`.
- Confirm final output includes `Agent READY`.
- Confirm TCP `15034` is listening on `0.0.0.0`.

Verification:

```bash
whoami
ss -tulnp | grep ':15034'
```

### Step 8: Install and Verify `monitor.sh`

Policy:

- Place at `$AGENT_HOME/bin/monitor.sh`.
- Owner `agent-dev`, group `agent-core`, mode `750`.
- Manual execution must print health/resource result and append one log line.

Verification:

```bash
ls -l "$AGENT_HOME/bin/monitor.sh"
"$AGENT_HOME/bin/monitor.sh"
tail -n 5 /var/log/agent-app/monitor.log
```

### Step 9: Register Cron

Policy:

- Use `agent-admin` crontab.
- Execute every minute.
- Confirm log grows after 1-2 minutes.
- Ensure the cron daemon is running inside the container. Containers do not start cron automatically unless the image entrypoint or manual command starts it.

Verification:

```bash
service cron status
crontab -l
wc -l /var/log/agent-app/monitor.log
sleep 70
wc -l /var/log/agent-app/monitor.log
tail -n 5 /var/log/agent-app/monitor.log
```

## 5. Deferred Optional Outputs

Implement only after required scope passes:

- `report.sh`: summarize average/max/min CPU, memory, disk usage from `monitor.log`.
- Archive policy script or logrotate rule for 7-day compression, archive move, and 30-day deletion.

## 6. Risks and Decisions

| Topic | Decision | Risk | Mitigation |
| --- | --- | --- | --- |
| Runtime | Use Docker container from macOS | Docker is not a full VM | Document container boundaries and keep Linux evidence inside container |
| Firewall | Prefer UFW | UFW may need `NET_ADMIN` or may not enforce normally inside Docker | Run with capability or document limitation; also verify Docker port publishing |
| App filename | Support provided binary names and `agent_app.py` candidate | Process matching may miss renamed app | Keep process name configurable |
| Log retention | Prefer logrotate, fallback to Bash rotation | No permission to install logrotate rule | Script-local rotation can satisfy size policy |
| ACL | Use Unix groups first, ACL only if needed | ACL evidence is requested | Capture `getfacl` output even when no custom ACL entries are used |
| Cron output | Redirect stdout/stderr to separate cron output log | Cron daemon is not automatic in containers | Start cron in entrypoint or explicitly during setup |

## 7. Next Implementation Order

1. Create `monitor.sh` in repository.
2. Validate syntax with `bash -n`.
3. Create Docker runtime files.
4. Create `REPORT.md` template.
5. Build and start the Ubuntu container from macOS.
6. Execute setup commands inside the container.
7. Paste command outputs and evidence into `REPORT.md`.
8. Register cron and verify log accumulation.
9. Review required checklist against `Problem.md`.
