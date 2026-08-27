# Mini Git — CLI 기반 버전 관리 시스템

Git의 핵심 자료구조(DAG 커밋 그래프)를 직접 구현한 CLI 프로그램.
커밋, 브랜치, 그래프 탐색, 역색인 검색, 정렬까지 외부 라이브러리 없이 순수 Python으로 구현했다.

---

## 과제 요약

| 항목 | 내용 |
|------|------|
| 목표 | Git 내부 구조(DAG, 위상정렬, BFS, 역색인)를 직접 구현하며 학습 |
| 핵심 제약 | `sorted()`, `list.sort()` 금지 / 그래프 라이브러리 금지 |
| 실행 환경 | Python 3.10+ |
| 데이터 영속성 | 없음 (메모리 내 동작, 종료 시 소멸) |

---

## 구현 요약

```
Q3_2/
├── main.py                 ← 엔트리 포인트 (REPL)
├── mini_git/
│   ├── models.py           ← Commit 데이터 모델, SHA-1 해시 생성
│   ├── repository.py       ← Facade — 모든 명령 처리 및 상태 관리
│   ├── graph.py            ← 위상 정렬(Kahn), BFS 최단경로, 조상 탐색
│   ├── index.py            ← 역색인 (keyword/author → commit hash)
│   ├── sorting.py          ← Merge Sort 직접 구현
│   └── parser.py           ← CLI 명령 파싱 (따옴표, 옵션 처리)
├── test_mini_git.py        ← 자동화 테스트 (52개 항목)
└── docs/
    ├── PROBLEM.md
    ├── SPEC.md
    └── IMPLEMENTATION.md
```

### 주요 알고리즘

| 기능 | 알고리즘 | 시간복잡도 |
|------|----------|-----------|
| LOG (위상 정렬) | Kahn's Algorithm | O(V + E) |
| PATH (최단 경로) | BFS + 사전순 최소 경로 선택 | O(V + E) |
| ANCESTORS | BFS (부모 방향) | O(V + E) |
| SEARCH | 역색인 조회 | O(1) |
| LOG --sort-by | Merge Sort (직접 구현) | O(n log n) |

---

## 실행 방법

```bash
cd Q3_2
python main.py
```

---

## 빠른 테스트 가이드

프로그램을 실행하면 `mini-git>` 프롬프트가 나타난다. 아래 명령을 순서대로 입력해보자.

### 1단계: 저장소 초기화 + 첫 커밋

```
mini-git> init "Alice"
mini-git> commit "Initial commit"
```

### 2단계: 작성자 변경 + 브랜치 분기

```
mini-git> commit "Alice initial work"
mini-git> user "Bob"
mini-git> branch feature
mini-git> switch feature
mini-git> commit "Add login feature"
mini-git> switch main
mini-git> user "Alice"
mini-git> commit "Add payment feature"
```

### 3단계: 로그 확인

```
mini-git> log
mini-git> log --sort-by=date
mini-git> log --sort-by=author
```

### 4단계: 경로 탐색

LOG에서 확인한 해시를 사용한다 (예: `a1b2c3`, `d4e5f6`).

```
mini-git> path <첫번째해시> <마지막해시>
```

### 5단계: 조상 탐색

```
mini-git> ancestors <최신커밋해시>
```

### 6단계: 검색

```
mini-git> search "login"
mini-git> search --author=Alice
```

### 7단계: 종료

```
mini-git> exit
```

---

## 자동화 테스트 실행

```bash
python test_mini_git.py
```

52개 항목을 자동으로 검증한다. 모든 기능(INIT, COMMIT, BRANCH, SWITCH, LOG, PATH, ANCESTORS, SEARCH, Parser, Sorting)을 커버한다.

---

## 지원 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `init <user>` | 저장소 초기화 |
| `user <name>` | 현재 작성자 변경 |
| `commit <message>` | 새 커밋 생성 |
| `branch <name>` | 브랜치 생성 |
| `switch <name>` | 브랜치 전환 |
| `log` | 위상 정렬 순서로 커밋 출력 |
| `log --sort-by=date\|author` | 정렬 기준 변경 |
| `path <hash1> <hash2>` | 두 커밋 간 최단 경로 |
| `ancestors <hash>` | 모든 조상 커밋 출력 |
| `search <keyword>` | 키워드로 커밋 검색 |
| `search --author=<name>` | 작성자로 커밋 검색 |
| `exit` / `quit` | 프로그램 종료 |

명령어는 대소문자를 구분하지 않는다. 공백 포함 인자는 따옴표로 감싼다.

---

## INTERVIEW

### 항목 1: 구현 완료 검증

아래 명령어를 순서대로 입력하여 기능 동작을 확인한다.

```bash
cd Q3_2
python main.py
```

#### INIT → BRANCH → SWITCH → COMMIT 동작 검증

```
mini-git> init "Alice"
```
예상 결과:
```
Initialized repository.
Current branch: main
Current user: Alice
```

```
mini-git> commit "First"
```
예상 결과:
```
[main <hash>] First
```

```
mini-git> branch dev
```
예상 결과:
```
Created branch: dev
```

```
mini-git> switch dev
mini-git> commit "Dev work"
```
예상 결과:
```
Switched to branch: dev
[dev <hash>] Dev work
```

#### LOG (부모가 자식보다 먼저 출력)

```
mini-git> log
```
예상 결과:
```
commit <hash1> (Alice, ...)
  First
commit <hash2> (Alice, ...)
  Dev work
```
→ 부모인 "First"가 자식인 "Dev work"보다 먼저 출력된다.

#### PATH (최단 경로 / No path)

```
mini-git> path <hash1> <hash2>
```
예상 결과:
```
Path: <hash1> -> <hash2>
```

연결되지 않은 커밋이 있는 경우: `No path`

#### ANCESTORS

```
mini-git> ancestors <hash2>
```
예상 결과:
```
<hash1>
```
→ "Dev work"의 부모 "First"가 출력된다.

#### SEARCH / SEARCH --author / LOG --sort-by

```
mini-git> search "dev"
```
예상 결과:
```
Found 1 commit(s):
- <hash2>: Dev work
```

```
mini-git> search --author=Alice
```
예상 결과:
```
Found 2 commit(s):
- <hash1>: First
- <hash2>: Dev work
```

```
mini-git> log --sort-by=date
mini-git> log --sort-by=author
```
→ 각각 timestamp 오름차순, author 이름 사전순으로 정렬된 로그 출력.

---

### 항목 2: 설계 및 구조 설명

#### Q. 커밋 저장소/브랜치/HEAD/사용자 정보를 어떤 구조로 분리했는가?

`mini_git/repository.py` — `Repository` 클래스에서 다음과 같이 분리:

| 필드 | 역할 |
|------|------|
| `self.commits: dict[str, Commit]` | CommitStore — hash를 키로 커밋 객체를 저장 |
| `self.branches: dict[str, str \| None]` | BranchTable — 브랜치명 → tip 커밋 hash 매핑 |
| `self.head_branch: str` | HEAD — 현재 활성 브랜치 이름 |
| `self.author: str` | 현재 사용자 이름 |
| `self.index: InvertedIndex` | 역색인 — 검색 담당 |

각 책임이 명확히 분리되어 있으며, 알고리즘 로직(`graph.py`, `sorting.py`)은 Repository 상태에 직접 의존하지 않고 인자로 데이터를 받아 처리한다.

#### Q. 커밋 hash로 빠르게 조회하기 위해 어떤 키-값 구조를 사용했는가?

`mini_git/repository.py` — `self.commits`는 Python `dict[str, Commit]`으로 구현. hash(6자리 hex)를 키로 O(1) 조회를 보장한다.

중복/충돌 방지: `mini_git/models.py`의 `generate_commit_hash()`에서 `hashlib.sha1` + 전역 증가 카운터로 hash를 생성하되, 기존 hash 집합(`existing_hashes`)과 비교하여 충돌 시 카운터를 증가시켜 재생성한다.

#### Q. 역색인을 어떤 시점에, 어떤 방식으로 갱신하는가?

`mini_git/index.py` — `InvertedIndex.add_commit()` 메서드.

갱신 시점: `Repository.commit()` 실행 시, 새 커밋이 CommitStore에 등록된 직후 `self.index.add_commit(hash, message, author)`를 호출한다 (`repository.py` 97행).

갱신 방식:
1. 메시지를 공백 split → 소문자 정규화 → 각 토큰을 `keyword_index[token].append(hash)`
2. 작성자를 소문자 정규화 → `author_index[author_key].append(hash)`

#### Q. 그래프 탐색 로직을 어떻게 재사용 가능하게 구성했는가?

`mini_git/graph.py` — 모든 함수가 순수 함수로 작성됨:

- `collect_reachable(start_hash, commits)` → LOG, ANCESTORS 모두에서 커밋 수집에 활용
- `topological_sort(commit_list)` → LOG 명령의 기본 정렬
- `find_shortest_path(start, end, commits)` → PATH 명령
- `find_ancestors(commit_hash, commits)` → ANCESTORS 명령

Repository 인스턴스에 의존하지 않고 `dict[str, Commit]`만 인자로 받으므로, 단위 테스트에서도 독립적으로 검증 가능하다.

#### Q. docstring/주석 작성 기준

모든 모듈에 모듈 docstring, 모든 public 클래스/함수에 Google 스타일 docstring을 작성했다. 기준:
- 모듈 최상단: 모듈의 책임과 역할 요약
- 함수/메서드: 동작 요약 + Args + Returns
- 복잡한 알고리즘 내부: 인라인 주석으로 단계 설명 (예: `graph.py`의 위상 정렬 in-degree 계산 부분)

---

### 항목 3: 알고리즘 원리 설명

#### Q. 커밋 그래프가 왜 DAG여야 하는가?

DAG(Directed Acyclic Graph)는 사이클이 없는 방향 그래프이다. Git에서 커밋의 `parents`는 시간적으로 과거를 가리키므로 방향이 존재하며, "미래의 커밋이 과거 커밋의 부모가 되는" 순환은 논리적으로 불가능하다.

사이클이 생기면:
- 위상 정렬이 불가능해져 LOG 출력 순서를 결정할 수 없다
- ANCESTORS 탐색이 무한 루프에 빠진다
- 커밋 이력의 "시간 순서"라는 의미가 파괴된다

확인 위치: `mini_git/graph.py` — `topological_sort()`의 Kahn's Algorithm은 DAG에서만 정상 동작하며, 사이클이 있으면 일부 노드가 결과에 포함되지 않는다.

#### Q. LOG에서 "부모가 먼저" 조건을 어떻게 만족시키는가?

`mini_git/graph.py` — `topological_sort()` 함수에서 Kahn's Algorithm을 적용한다.

1. 간선 방향을 "부모→자식"으로 설정
2. 각 노드의 in-degree(자신을 향하는 간선 수) 계산
3. in-degree가 0인 노드(= root 커밋, 부모가 없는 가장 오래된 커밋)부터 큐에 넣고 출력
4. 출력한 노드의 자식들의 in-degree를 1씩 감소 → 0이 되면 큐에 추가
5. 결과: 부모가 반드시 자식보다 먼저 출력됨

#### Q. PATH에서 BFS를 선택한 이유와 간선을 무방향으로 정의한 이유

`mini_git/graph.py` — `find_shortest_path()` 함수.

BFS 선택 이유: 모든 간선의 가중치가 동일(1)하므로, BFS가 최단 경로를 보장하는 가장 효율적인 알고리즘이다 (O(V+E)).

무방향 정의 이유: 커밋 그래프의 간선은 원래 자식→부모 단방향이다. 하지만 "두 커밋 사이의 관계"를 탐색할 때는 자식→부모 뿐 아니라 부모→자식 방향으로도 이동할 수 있어야 경로가 존재한다. 예를 들어 형제 브랜치의 두 커밋은 공통 조상을 경유해야만 연결되므로, 양방향 간선이 필요하다.

#### Q. 정렬 알고리즘의 시간복잡도와 안정 정렬 여부

`mini_git/sorting.py` — Merge Sort 직접 구현.

| 항목 | 값 |
|------|-----|
| 평균 시간복잡도 | O(n log n) |
| 최악 시간복잡도 | O(n log n) |
| 공간복잡도 | O(n) |
| 안정 정렬 여부 | Yes (동일 키의 원소 순서 보존) |

안정 정렬 보장 근거: `_merge()` 함수에서 `left_key <= right_key`일 때 왼쪽 원소를 먼저 선택하므로, 동일 키를 가진 원소들의 상대적 순서가 유지된다.

#### Q. 역색인이 순회 검색보다 빠른 이유

`mini_git/index.py` — `InvertedIndex` 클래스.

- 역색인 조회: `keyword_index.get(keyword)` → O(1) (dict 해시맵 조회) + O(k) (결과 k개 반환)
- 순회 검색: 전체 커밋 N개를 순회하며 메시지에 keyword가 포함되는지 확인 → O(N × M) (M = 평균 메시지 길이)

커밋 수 N이 증가해도 역색인은 상수 시간에 후보를 가져오므로, 대규모 저장소에서 성능 차이가 극대화된다.

---

### 항목 4: 확장 사고력

#### Q. 커밋 수가 10배 늘어났을 때 병목 지점과 개선 방향

예측 병목:
1. **PATH (BFS 전체 경로 복원)**: 최단 경로가 다수일 때 `_reconstruct_paths()`가 지수적으로 증가 가능 → 개선: 경로 복원 시 사전순 pruning 적용 (최소 접두사보다 큰 경로는 탐색 중단)
2. **LOG 위상 정렬**: O(V+E)이므로 선형 증가. 큰 문제 없음
3. **메모리**: 모든 커밋을 dict에 보관하므로 선형 증가 → 개선: LRU 캐시 또는 디스크 기반 저장소

개선 방향: PATH의 모든 최단 경로 열거를 "탐색 중 사전순 우선 BFS"로 대체하면 첫 번째 발견 경로가 곧 사전순 최소이므로 경로 열거 비용을 제거할 수 있다.

#### Q. PATH 간선 정의를 "부모 방향만 허용"으로 바꾸면?

결과 변화: 자식→부모 방향으로만 이동 가능하므로, 자식에서 부모로의 경로만 존재하게 된다. 형제 브랜치의 커밋끼리는 경로가 없어지고, 부모에서 자식으로도 도달 불가능해진다.

구현 변경 (`mini_git/graph.py` — `find_shortest_path()`):
- 인접 리스트 구축 시 양방향 등록 대신 `adjacency[h].append(parent_hash)`만 유지 (역방향 `adjacency[parent_hash].append(h)` 제거)
- 나머지 BFS 로직은 동일

#### Q. LOG --sort-by=author에 "부모-자식 선후 유지" 조건이 추가된다면?

전략: **위상 정렬 내에서 동일 레벨 노드를 author 기준으로 정렬**

1. Kahn's Algorithm 수행 중, 큐에서 다음 노드를 꺼낼 때 단순 FIFO 대신 author 기준 우선순위를 적용
2. 구체적으로: `deque`를 `priority queue`(min-heap)로 교체하거나, 매 단계 큐의 후보를 merge_sort로 정렬 후 선택
3. 이렇게 하면 위상 순서(부모 먼저)를 보장하면서도, 동일 위상 레벨 내에서는 author 사전순이 반영된다

확인 위치: `mini_git/graph.py`의 `topological_sort()` 함수의 큐 처리 부분을 수정하면 된다.

#### Q. 해시 생성 방식을 카운터 기반 ↔ 난수 기반으로 바꿀 때 영향

현재 방식 (`mini_git/models.py`): 전역 카운터 기반 (결정론적 요소 + SHA-1)

| 관점 | 카운터 기반 (현재) | 난수 기반 |
|------|-------------------|-----------|
| 테스트 재현성 | 동일 입력 순서 → 동일 hash → 테스트 예측 가능 | 실행마다 hash 변경 → assert에 구체적 hash 사용 불가 |
| 디버깅 | hash가 예측 가능하여 로그 추적 용이 | 매번 다른 hash → 재현 어려움 |
| 충돌 확률 | 카운터 단조 증가로 충돌 거의 없음 | 난수 충돌 가능성 존재 (6자리 hex = 16^6 ≈ 16M 가지) |
| 보안/유추 방지 | hash를 예측할 수 있어 보안 민감 환경에 부적합 | 예측 불가로 보안 측면 우수 |

현재 구현은 학습/테스트 목적에 적합한 카운터 기반을 선택했으며, `existing_hashes` 집합으로 충돌을 추가 방어한다.
