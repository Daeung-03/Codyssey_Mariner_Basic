"""CLI 명령 파싱 모듈.

사용자 입력 문자열을 (command, args, options) 형태로 변환한다.
따옴표로 감싼 인자를 지원하며, 대소문자를 무시한다.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field


@dataclass
class ParsedCommand:
    """파싱 결과를 담는 구조체.

    Attributes:
        command: 명령어 (대문자 정규화).
        args: 위치 인자 리스트.
        options: 옵션 딕셔너리 (예: {"sort-by": "date", "author": "alice"}).
    """

    command: str
    args: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)


def parse(input_line: str) -> ParsedCommand | None:
    """사용자 입력 한 줄을 파싱한다.

    Args:
        input_line: 원시 입력 문자열.

    Returns:
        ParsedCommand 또는 빈 입력이면 None.
    """
    stripped = input_line.strip()
    if not stripped:
        return None

    try:
        tokens = shlex.split(stripped)
    except ValueError:
        # 따옴표 미닫힘 등 — 토큰을 공백 분리로 폴백
        tokens = stripped.split()

    if not tokens:
        return None

    command = tokens[0].upper()
    args: list[str] = []
    options: dict[str, str] = {}

    for token in tokens[1:]:
        if token.startswith("--"):
            # --key=value 또는 --key
            if "=" in token:
                key, value = token[2:].split("=", 1)
                options[key.lower()] = value
            else:
                options[token[2:].lower()] = ""
        else:
            args.append(token)

    return ParsedCommand(command=command, args=args, options=options)
