"""Mini Git 도메인 모델."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime


# 전역 카운터 — 동일 초에 같은 메시지라도 유일한 hash 생성 보장
_hash_counter: int = 0


def generate_commit_hash(
    author: str,
    message: str,
    timestamp: datetime,
    existing_hashes: set[str],
) -> str:
    """6자리 hex 커밋 hash를 생성한다.

    hashlib.sha1 기반, 충돌 시 카운터를 증가시켜 재생성.
    """
    global _hash_counter

    while True:
        _hash_counter += 1
        raw = f"{author}{message}{timestamp}{_hash_counter}".encode()
        h = hashlib.sha1(raw).hexdigest()[:6]
        if h not in existing_hashes:
            return h


@dataclass
class Commit:
    """커밋 메타데이터를 보관하는 도메인 모델.

    Attributes:
        hash: 6자리 hex 문자열, 세션 내 유일.
        message: 커밋 메시지 원문.
        author: 작성자 이름.
        timestamp: 커밋 생성 시각.
        parents: 부모 커밋 hash 목록 (0~N개).
    """

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: list[str] = field(default_factory=list)
