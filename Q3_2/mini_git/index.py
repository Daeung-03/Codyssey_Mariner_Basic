"""역색인(Inverted Index) 모듈.

SEARCH <keyword> 및 SEARCH --author=<name> 명령을 O(1) 조회로 지원한다.
"""

from __future__ import annotations


class InvertedIndex:
    """커밋 메시지 키워드 및 작성자 역색인.

    - keyword_index: 소문자 토큰 → commit hash 목록
    - author_index: 소문자 author → commit hash 목록
    """

    def __init__(self) -> None:
        self.keyword_index: dict[str, list[str]] = {}
        self.author_index: dict[str, list[str]] = {}

    def add_commit(self, commit_hash: str, message: str, author: str) -> None:
        """커밋을 인덱스에 등록한다.

        Args:
            commit_hash: 커밋 hash.
            message: 커밋 메시지 원문 (토큰화하여 keyword_index에 등록).
            author: 작성자 이름 (소문자로 정규화하여 author_index에 등록).
        """
        # 키워드 인덱싱 — 메시지를 공백 기준으로 분리 후 소문자 정규화
        tokens = message.lower().split()
        for token in tokens:
            if token not in self.keyword_index:
                self.keyword_index[token] = []
            self.keyword_index[token].append(commit_hash)

        # 작성자 인덱싱
        author_key = author.lower()
        if author_key not in self.author_index:
            self.author_index[author_key] = []
        self.author_index[author_key].append(commit_hash)

    def search_keyword(self, keyword: str) -> list[str]:
        """키워드로 커밋 hash 목록을 조회한다.

        Args:
            keyword: 검색 키워드 (소문자로 정규화하여 비교).

        Returns:
            매칭된 commit hash 리스트. 결과 없으면 빈 리스트.
        """
        return self.keyword_index.get(keyword.lower(), [])

    def search_author(self, author: str) -> list[str]:
        """작성자로 커밋 hash 목록을 조회한다.

        Args:
            author: 작성자 이름 (대소문자 무시).

        Returns:
            매칭된 commit hash 리스트. 결과 없으면 빈 리스트.
        """
        return self.author_index.get(author.lower(), [])
