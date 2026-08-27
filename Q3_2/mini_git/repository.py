"""Repository 모듈 — Mini Git의 Facade.

모든 상태(commits, branches, HEAD, index)를 보유하며,
외부(REPL)는 이 클래스만 호출한다.
"""

from __future__ import annotations

from datetime import datetime

from mini_git.graph import (
    collect_reachable,
    find_ancestors,
    find_shortest_path,
    topological_sort,
)
from mini_git.index import InvertedIndex
from mini_git.models import Commit, generate_commit_hash
from mini_git.sorting import merge_sort


class Repository:
    """Mini Git 저장소 상태 관리 및 명령 실행."""

    def __init__(self) -> None:
        self.initialized: bool = False
        self.author: str = ""
        self.commits: dict[str, Commit] = {}  # CommitStore
        self.branches: dict[str, str | None] = {}  # BranchTable
        self.head_branch: str = ""  # 현재 브랜치 이름
        self.index: InvertedIndex = InvertedIndex()

    # ─── 명령 메서드 ──────────────────────────────────────────────

    def init(self, user_name: str) -> str:
        """INIT <user_name>"""
        if self.initialized:
            return "Already initialized"

        self.initialized = True
        self.author = user_name
        self.branches["main"] = None
        self.head_branch = "main"

        lines = [
            "Initialized repository.",
            "Current branch: main",
            f"Current user: {user_name}",
        ]
        return "\n".join(lines)

    def branch(self, branch_name: str) -> str:
        """BRANCH <branch_name>"""
        if not self.initialized:
            return "Repository not initialized"

        head_commit = self.branches[self.head_branch]
        if head_commit is None:
            return "Cannot create branch: no commits yet"

        if branch_name in self.branches:
            return f"Branch already exists: {branch_name}"

        self.branches[branch_name] = head_commit
        return f"Created branch: {branch_name}"

    def switch(self, branch_name: str) -> str:
        """SWITCH <branch_name>"""
        if not self.initialized:
            return "Repository not initialized"

        if branch_name not in self.branches:
            return f"Unknown branch: {branch_name}"

        if branch_name == self.head_branch:
            return f"Already on branch: {branch_name}"

        self.head_branch = branch_name
        return f"Switched to branch: {branch_name}"

    def commit(self, message: str) -> str:
        """COMMIT <message>"""
        if not self.initialized:
            return "Repository not initialized"

        now = datetime.now()
        commit_hash = generate_commit_hash(
            self.author, message, now, set(self.commits.keys())
        )

        head_commit = self.branches[self.head_branch]
        parents = [head_commit] if head_commit is not None else []

        new_commit = Commit(
            hash=commit_hash,
            message=message,
            author=self.author,
            timestamp=now,
            parents=parents,
        )

        self.commits[commit_hash] = new_commit
        self.branches[self.head_branch] = commit_hash
        self.index.add_commit(commit_hash, message, self.author)

        return f"[{self.head_branch} {commit_hash}] {message}"

    def log(self, sort_by: str | None = None) -> str:
        """LOG 또는 LOG --sort-by=date|author"""
        if not self.initialized:
            return "Repository not initialized"

        # HEAD 커밋 결정
        head_commit = self.branches[self.head_branch]
        if head_commit is None:
            # 현재 브랜치에 커밋 없으면 main 확인
            head_commit = self.branches.get("main")

        if head_commit is None:
            return "No commits yet"

        reachable = collect_reachable(head_commit, self.commits)

        if sort_by == "date":
            sorted_commits = merge_sort(reachable, key=lambda c: c.timestamp)
        elif sort_by == "author":
            sorted_commits = merge_sort(reachable, key=lambda c: c.author.lower())
        else:
            sorted_commits = topological_sort(reachable)

        return self._format_log(sorted_commits)

    def path(self, hash1: str, hash2: str) -> str:
        """PATH <commit1> <commit2>"""
        if not self.initialized:
            return "Repository not initialized"

        if hash1 not in self.commits:
            return f"Unknown commit: {hash1}"
        if hash2 not in self.commits:
            return f"Unknown commit: {hash2}"

        result = find_shortest_path(hash1, hash2, self.commits)

        if result is None:
            return "No path"

        return "Path: " + " -> ".join(result)

    def ancestors(self, commit_hash: str) -> str:
        """ANCESTORS <commit_hash>"""
        if not self.initialized:
            return "Repository not initialized"

        if commit_hash not in self.commits:
            return f"Unknown commit: {commit_hash}"

        ancestor_list = find_ancestors(commit_hash, self.commits)

        if not ancestor_list:
            return "No ancestors"

        return "\n".join(ancestor_list)

    def search(self, keyword: str | None = None, author: str | None = None) -> str:
        """SEARCH <keyword> 또는 SEARCH --author=<name>"""
        if not self.initialized:
            return "Repository not initialized"

        if author is not None:
            results = self.index.search_author(author)
        elif keyword is not None:
            results = self.index.search_keyword(keyword)
        else:
            return "Invalid args"

        if not results:
            return "No commits found"

        lines = [f"Found {len(results)} commit(s):"]
        for h in results:
            commit = self.commits[h]
            lines.append(f"- {h}: {commit.message}")

        return "\n".join(lines)

    # ─── 내부 헬퍼 ────────────────────────────────────────────────

    def _format_log(self, commit_list: list[Commit]) -> str:
        """로그 출력 포맷 생성."""
        lines: list[str] = []
        for c in commit_list:
            ts = c.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"commit {c.hash} ({c.author}, {ts})")
            lines.append(f"  {c.message}")
        return "\n".join(lines)
