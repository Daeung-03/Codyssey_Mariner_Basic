"""Mini Redis CLI — REPL 인터페이스.

shlex로 입력을 토큰화하고, 명령을 디스패치하며,
Redis 스타일 문자열로 결과를 출력한다.

실행: python -m mini_redis.cli
"""

import json
import shlex
import sys
from typing import List, Optional

from mini_redis.core import MiniRedis, OutOfMemoryError

PROMPT = "mini-redis> "


# ═══════════════════════════════════════════════════════
# 출력 포맷 헬퍼
# ═══════════════════════════════════════════════════════


def _format_ok() -> str:
    return "OK"


def _format_nil() -> str:
    return "(nil)"


def _format_integer(n: int) -> str:
    return f"(integer) {n}"


def _format_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _format_keys(keys: List[str]) -> str:
    if not keys:
        return "(empty array)"
    lines = []
    for i, key in enumerate(keys, start=1):
        lines.append(f"{i}) {json.dumps(key, ensure_ascii=False)}")
    return "\n".join(lines)


def _format_info(used: int, maxmem: int, evicted: int) -> str:
    return f"used_memory:{used}\nmaxmemory:{maxmem}\nevicted_keys:{evicted}"


def _format_error(msg: str) -> str:
    return f"(error) {msg}"


# ═══════════════════════════════════════════════════════
# 정수 파싱 헬퍼
# ═══════════════════════════════════════════════════════


def _parse_int(value: str) -> Optional[int]:
    """정수 변환을 시도하고 실패하면 None을 반환한다."""
    try:
        return int(value)
    except (ValueError, OverflowError):
        return None


# ═══════════════════════════════════════════════════════
# 명령 핸들러
# ═══════════════════════════════════════════════════════


def _handle_set(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 2:
        return _format_error("ERR wrong number of arguments for 'SET' command")
    key, value = args
    try:
        redis.set(key, value)
        return _format_ok()
    except OutOfMemoryError:
        return _format_error("OOM command not allowed when used_memory > 'maxmemory'")


def _handle_get(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 1:
        return _format_error("ERR wrong number of arguments for 'GET' command")
    result = redis.get(args[0])
    if result is None:
        return _format_nil()
    return _format_string(result)


def _handle_del(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 1:
        return _format_error("ERR wrong number of arguments for 'DEL' command")
    return _format_integer(redis.delete(args[0]))


def _handle_exists(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 1:
        return _format_error("ERR wrong number of arguments for 'EXISTS' command")
    return _format_integer(redis.exists(args[0]))


def _handle_dbsize(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 0:
        return _format_error("ERR wrong number of arguments for 'DBSIZE' command")
    return _format_integer(redis.dbsize())


def _handle_keys(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 0:
        return _format_error("ERR wrong number of arguments for 'KEYS' command")
    return _format_keys(redis.keys())


def _handle_expire(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 2:
        return _format_error("ERR wrong number of arguments for 'EXPIRE' command")
    seconds = _parse_int(args[1])
    if seconds is None:
        return _format_error("ERR value is not an integer or out of range")
    return _format_integer(redis.expire(args[0], seconds))


def _handle_ttl(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 1:
        return _format_error("ERR wrong number of arguments for 'TTL' command")
    return _format_integer(redis.ttl(args[0]))


def _handle_config(redis: MiniRedis, args: List[str]) -> str:
    # CONFIG SET maxmemory <bytes>
    if len(args) < 1:
        return _format_error("ERR wrong number of arguments for 'CONFIG' command")

    sub = args[0].upper()
    if sub != "SET":
        return _format_error(f"ERR unknown subcommand '{args[0]}'")

    if len(args) != 3:
        return _format_error("ERR wrong number of arguments for 'CONFIG SET' command")

    param = args[1].upper()
    if param != "MAXMEMORY":
        return _format_error(f"ERR unknown config parameter '{args[1]}'")

    bytes_val = _parse_int(args[2])
    if bytes_val is None or bytes_val < 0:
        return _format_error("ERR value is not an integer or out of range")

    redis.config_set_maxmemory(bytes_val)
    return _format_ok()


def _handle_info(redis: MiniRedis, args: List[str]) -> str:
    if len(args) != 1 or args[0].upper() != "MEMORY":
        return _format_error("ERR wrong number of arguments for 'INFO' command")
    used, maxmem, evicted = redis.info_memory()
    return _format_info(used, maxmem, evicted)


# ═══════════════════════════════════════════════════════
# 디스패치 테이블
# ═══════════════════════════════════════════════════════

_COMMANDS = {
    "SET": _handle_set,
    "GET": _handle_get,
    "DEL": _handle_del,
    "EXISTS": _handle_exists,
    "DBSIZE": _handle_dbsize,
    "KEYS": _handle_keys,
    "EXPIRE": _handle_expire,
    "TTL": _handle_ttl,
    "CONFIG": _handle_config,
    "INFO": _handle_info,
}


# ═══════════════════════════════════════════════════════
# REPL
# ═══════════════════════════════════════════════════════


def execute_command(redis: MiniRedis, line: str) -> Optional[str]:
    """한 줄 입력을 파싱·실행하고 출력 문자열을 반환한다.

    exit/quit이면 None을 반환하여 종료를 알린다.
    """
    line = line.strip()
    if not line:
        return ""

    try:
        tokens = shlex.split(line)
    except ValueError:
        return _format_error("ERR syntax error")

    if not tokens:
        return ""

    cmd = tokens[0].upper()

    if cmd in ("EXIT", "QUIT"):
        return None

    handler = _COMMANDS.get(cmd)
    if handler is None:
        return _format_error(f"ERR unknown command '{tokens[0]}'")

    return handler(redis, tokens[1:])


def main() -> None:
    """REPL 진입점."""
    redis = MiniRedis()

    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        result = execute_command(redis, line)
        if result is None:
            break
        if result:
            print(result)


if __name__ == "__main__":
    main()
