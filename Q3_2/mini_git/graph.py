"""그래프 알고리즘 모듈.

위상 정렬(LOG), BFS 최단 경로(PATH), 조상 탐색(ANCESTORS)을 제공한다.
Repository 상태에 직접 의존하지 않고, 인자로 데이터를 받아 처리하는 순수 함수.
"""

from __future__ import annotations

from collections import deque

from mini_git.models import Commit
from mini_git.sorting import merge_sort


def collect_reachable(start_hash: str, commits: dict[str, Commit]) -> list[Commit]:
    """start_hash에서 부모 방향으로 도달 가능한 모든 커밋을 BFS로 수집한다.

    Args:
        start_hash: 시작 커밋 hash.
        commits: 전체 CommitStore (hash → Commit).

    Returns:
        도달 가능한 Commit 리스트 (start 포함).
    """
    visited: set[str] = set()
    queue: deque[str] = deque([start_hash])
    result: list[Commit] = []

    while queue:
        h = queue.popleft()
        if h in visited:
            continue
        visited.add(h)
        commit = commits[h]
        result.append(commit)
        for parent_hash in commit.parents:
            if parent_hash not in visited:
                queue.append(parent_hash)

    return result


def topological_sort(commit_list: list[Commit]) -> list[Commit]:
    """Kahn's Algorithm으로 위상 정렬한다. 부모가 자식보다 먼저 출력된다.

    간선 방향: 부모 → 자식 (부모가 먼저 나오도록).
    in-degree = 해당 커밋을 가리키는 부모→자식 간선 중 "자식 입장에서 들어오는 간선 수".

    Args:
        commit_list: 정렬 대상 커밋 리스트.

    Returns:
        위상 정렬된 Commit 리스트.
    """
    hash_set = {c.hash for c in commit_list}
    commit_map = {c.hash: c for c in commit_list}

    # children[parent_hash] = [child_hash, ...]
    children: dict[str, list[str]] = {c.hash: [] for c in commit_list}
    in_degree: dict[str, int] = {c.hash: 0 for c in commit_list}

    for commit in commit_list:
        for parent_hash in commit.parents:
            if parent_hash in hash_set:
                children[parent_hash].append(commit.hash)
                in_degree[commit.hash] += 1

    # in-degree 0인 노드(root 커밋들)부터 시작
    queue: deque[str] = deque()
    for h, deg in in_degree.items():
        if deg == 0:
            queue.append(h)

    result: list[Commit] = []
    while queue:
        h = queue.popleft()
        result.append(commit_map[h])
        for child_hash in children[h]:
            in_degree[child_hash] -= 1
            if in_degree[child_hash] == 0:
                queue.append(child_hash)

    return result


def find_shortest_path(
    start_hash: str,
    end_hash: str,
    commits: dict[str, Commit],
) -> list[str] | None:
    """BFS로 두 커밋 간 최단 경로를 찾는다 (무방향 그래프).

    동일 거리 경로가 여럿이면 hash 문자열 사전순 최소 경로를 반환한다.

    Args:
        start_hash: 출발 커밋 hash.
        end_hash: 도착 커밋 hash.
        commits: 전체 CommitStore.

    Returns:
        hash 리스트 형태의 경로. 경로 없으면 None.
    """
    if start_hash == end_hash:
        return [start_hash]

    # 무방향 인접 리스트 구축
    adjacency: dict[str, list[str]] = {h: [] for h in commits}
    for h, commit in commits.items():
        for parent_hash in commit.parents:
            if parent_hash in commits:
                adjacency[h].append(parent_hash)
                adjacency[parent_hash].append(h)

    # BFS — 모든 최단 경로를 추적하기 위해 부모 목록 기록
    dist: dict[str, int] = {start_hash: 0}
    parents_map: dict[str, list[str]] = {start_hash: []}
    queue: deque[str] = deque([start_hash])

    while queue:
        current = queue.popleft()
        current_dist = dist[current]

        for neighbor in adjacency[current]:
            if neighbor not in dist:
                dist[neighbor] = current_dist + 1
                parents_map[neighbor] = [current]
                queue.append(neighbor)
            elif dist[neighbor] == current_dist + 1:
                parents_map[neighbor].append(current)

    if end_hash not in dist:
        return None

    # 모든 최단 경로를 복원한 후 사전순 최소 선택
    all_paths: list[list[str]] = []
    _reconstruct_paths(end_hash, start_hash, parents_map, [end_hash], all_paths)

    # 경로를 "hash1->hash2->..." 문자열로 변환하여 사전순 비교
    best_path: list[str] | None = None
    best_key: str = ""
    for path in all_paths:
        key = "->".join(path)
        if best_path is None or key < best_key:
            best_path = path
            best_key = key

    return best_path


def _reconstruct_paths(
    current: str,
    start: str,
    parents_map: dict[str, list[str]],
    path: list[str],
    all_paths: list[list[str]],
) -> None:
    """BFS 부모 맵으로부터 모든 최단 경로를 재귀적으로 복원한다."""
    if current == start:
        all_paths.append(list(reversed(path)))
        return

    for parent in parents_map[current]:
        path.append(parent)
        _reconstruct_paths(parent, start, parents_map, path, all_paths)
        path.pop()


def find_ancestors(commit_hash: str, commits: dict[str, Commit]) -> list[str]:
    """해당 커밋에서 부모 방향으로 도달 가능한 모든 조상 커밋 hash를 반환한다.

    자기 자신은 포함하지 않는다.

    Args:
        commit_hash: 대상 커밋 hash.
        commits: 전체 CommitStore.

    Returns:
        조상 커밋 hash 리스트.
    """
    visited: set[str] = set()
    queue: deque[str] = deque()

    # 시작 커밋의 부모부터 탐색
    for parent_hash in commits[commit_hash].parents:
        queue.append(parent_hash)

    result: list[str] = []

    while queue:
        h = queue.popleft()
        if h in visited:
            continue
        visited.add(h)
        result.append(h)
        for parent_hash in commits[h].parents:
            if parent_hash not in visited:
                queue.append(parent_hash)

    return result
