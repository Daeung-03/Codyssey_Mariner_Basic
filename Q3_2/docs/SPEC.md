# Mini Git — 구현 명세 (SPEC)

---

## 1. 요구사항 분류

### 1.1 필수 기능 요구사항

| 카테고리 | 기능 |
|----------|------|
| 저장소 관리 | INIT, BRANCH, SWITCH, COMMIT |
| 커밋 로그/탐색 | LOG, LOG --sort-by, PATH, ANCESTORS |
| 검색 | SEARCH \<keyword\>, SEARCH --author=\<name\> |
| CLI | REPL 루프, 대소문자 무시, 따옴표 인자, 에러 표준화 |

### 1.2 제약사항

| 제약 | 설명 |
|------|------|
| 정렬 API 금지 | `sorted()`, `list.sort()` 사용 불가. 직접 구현 |
| 그래프 라이브러리 금지 | networkx 등 외부 그래프 라이브러리 사용 불가 |
| 파일 내용 추적 없음 | 커밋 메타데이터 중심 (변경 파일 diff 없음) |
| 네트워크 없음 | 로컬 메모리 내에서만 동작 |
| 영속성 불필요 | 세션 종료 시 데이터 소멸 허용 |
| Python 3.10+ | 타입 힌팅, match-case 등 사용 가능 |

### 1.3 실제 Git과의 차이점 (주의)

| 항목 | 실제 Git | Mini Git |
|------|----------|----------|
| 오브젝트 모델 | blob/tree/commit/tag 4종 | commit만 존재 |
| 해시 | SHA-1 (파일 내용 기반) | 세션 내 유일성만 보장 (내용 기반 아님) |
| 스테이징 | index(staging area) 존재 | 없음. COMMIT이 바로 생성 |
| 파일 추적 | 워킹 디렉토리 + blob | 없음 |
| 로그 순서 | 최신 커밋 우선 | 위상 정렬 (부모 먼저) |
| PATH 개념 | 존재하지 않음 | 학습용으로 BFS 최단경로 제공 |
| 브랜치 모델 | ref (커밋 포인터) | 동일하게 커밋 포인터로 구현 |

---

## 2. 기능별 동작 정책

### 2.1 INIT \<user_name\>

- 저장소가 이미 초기화된 경우: `"Already initialized"` 에러
- 성공 시:
  - main 브랜치 생성 (커밋 없는 상태, tip = None)
  - HEAD → main 브랜치를 가리킴
  - 현재 사용자(author) 설정
- 출력: `Initialized repository.` / `Current branch: main` / `Current user: <name>`

### 2.2 BRANCH \<branch_name\>

- 전제: 저장소가 초기화된 상태
- 커밋이 하나도 없는 상태: `"Cannot create branch: no commits yet"` 에러
- 동일 이름 브랜치 존재 시: `"Branch already exists: <name>"` 에러
- 성공 시: 현재 HEAD가 가리키는 커밋을 새 브랜치의 tip으로 설정
- 출력: `Created branch: <name>`

### 2.3 SWITCH \<branch_name\>

- 존재하지 않는 브랜치: `"Unknown branch: <name>"` 에러
- 현재 브랜치와 동일한 브랜치로 전환 시: `"Already on branch: <name>"` 출력
- 성공 시: HEAD를 해당 브랜치로 이동
- 출력: `Switched to branch: <name>`

### 2.4 COMMIT \<message\>

- 전제: 저장소 초기화 완료
- 동작:
  1. 새 커밋 노드 생성 (hash, message, author, timestamp, parents)
  2. parents = [현재 HEAD 커밋] (HEAD가 None이면 parents = [] → root commit)
  3. 현재 브랜치의 tip을 새 커밋으로 갱신
  4. 역색인 갱신 (keyword index, author index)
- hash 생성: 6자리 hex 문자열 (hashlib.sha1 기반, 입력 = author+message+timestamp+random)
  - 충돌 시 재생성
- 출력: `[<branch> <hash>] <message>`

### 2.5 LOG

- 현재 브랜치 HEAD에서 도달 가능한 모든 커밋을 위상 정렬 순서로 출력
  - 위상 정렬: 부모 커밋이 항상 자식 커밋보다 먼저 출력
- 현재 브랜치에 커밋이 없으면 main 브랜치의 커밋을 출력
- main에도 커밋이 없는 경우 (INIT 직후): `"No commits yet"` 출력
- 출력 포맷 (커밋당 1줄):
  ```
  commit <hash> (<author>, <YYYY-MM-DD HH:MM:SS>)
    <message>
  ```

### 2.6 LOG --sort-by=date|author

- 현재 브랜치에서 도달 가능한 커밋을 수집 후 정렬 기준 적용
- `date`: timestamp 오름차순 (동률 시 순서 자유)
- `author`: author 이름 오름차순 사전순 (동률 시 순서 자유)
- 정렬 알고리즘: 직접 구현 (Merge Sort 사용 — 안정 정렬, O(n log n) 보장)

### 2.7 PATH \<commit1\> \<commit2\>

- 커밋 그래프를 무방향 그래프로 간주하여 BFS로 최단 경로 탐색
- 동일 커밋을 두 번 입력한 경우: 자기 자신만 출력 (`Path: <hash>`)
- 경로 없음: `"No path"` 출력
- 경로가 여러 개일 때: 경로를 `hash1->hash2->...` 문자열로 만들어 사전순(hash 문자열 전체 비교) 가장 작은 것 선택
- 존재하지 않는 hash 입력 시: `"Unknown commit: <hash>"` 에러
- 출력: `Path: <hash1> -> <hash2> -> ...`

### 2.8 ANCESTORS \<commit_hash\>

- 해당 커밋에서 부모 방향으로 도달 가능한 모든 조상 커밋 출력
- 탐색: BFS 또는 DFS (부모 방향으로만)
- 해당 커밋 자신은 포함하지 않음
- root commit (조상 없음): `"No ancestors"` 출력
- 존재하지 않는 hash: `"Unknown commit: <hash>"` 에러
- 출력: 조상 커밋 hash 목록 (한 줄에 하나)

### 2.9 SEARCH \<keyword\>

- 역색인(keyword index)에서 키워드 조회
- 키워드는 소문자로 정규화하여 검색
- 결과 없음: `"No commits found"` 출력
- 출력:
  ```
  Found <n> commit(s):
  - <hash>: <message>
  ```

### 2.10 SEARCH --author=\<name\>

- 역색인(author index)에서 작성자 조회
- author 비교는 대소문자 무시
- 결과/출력 형식은 SEARCH \<keyword\>와 동일

### 2.11 REPL / 종료

- 프롬프트: `mini-git> `
- `exit` 또는 `quit`로 종료 (대소문자 무시)
- 빈 입력: 무시하고 다시 프롬프트

---

## 3. 에러 메시지 표준

| 상황 | 메시지 |
|------|--------|
| 초기화 전 명령 실행 | `Repository not initialized` |
| INIT 중복 | `Already initialized` |
| 알 수 없는 명령어 | `Unknown command: <cmd>` |
| 인자 부족/초과 | `Invalid args` |
| 존재하지 않는 브랜치 | `Unknown branch: <name>` |
| 존재하지 않는 커밋 | `Unknown commit: <hash>` |
| 브랜치 중복 생성 | `Branch already exists: <name>` |
| 커밋 없이 브랜치 생성 | `Cannot create branch: no commits yet` |
| 현재 브랜치로 SWITCH | `Already on branch: <name>` |
| 커밋 없을 때 LOG | `No commits yet` |
| 조상 없는 커밋 ANCESTORS | `No ancestors` |

---

## 4. 자료구조 매핑

### 4.1 핵심 자료형

```
Commit (dataclass)
├── hash: str             — 6자리 hex, 세션 내 유일
├── message: str          — 커밋 메시지 원문
├── author: str           — 작성자
├── timestamp: datetime   — 생성 시각
└── parents: list[str]    — 부모 커밋 hash 목록 (0~N개)

CommitStore (해시맵)
└── dict[str, Commit]     — hash → Commit 빠른 조회

BranchTable
└── dict[str, str | None] — branch_name → tip commit hash (또는 None)

InvertedIndex
├── keyword_index: dict[str, list[str]]  — 소문자 토큰 → commit hash 목록
└── author_index: dict[str, list[str]]   — 소문자 author → commit hash 목록
```

### 4.2 기능-자료구조 매핑

| 기능 | 사용 자료구조 | 알고리즘 |
|------|---------------|----------|
| COMMIT | CommitStore, BranchTable, InvertedIndex | 해시 생성, 인덱스 갱신 |
| LOG | CommitStore, BranchTable | 위상 정렬 (Kahn's algorithm) |
| LOG --sort-by | CommitStore | Merge Sort (직접 구현) |
| PATH | CommitStore (무방향 인접리스트 구축) | BFS + 경로 복원 |
| ANCESTORS | CommitStore | BFS/DFS (부모 방향) |
| SEARCH | InvertedIndex, CommitStore | 인덱스 조회 O(1) |

---

## 5. 도메인 모델 및 아키텍처

### 5.1 모듈 구조

```
Q3_2/
├── main.py                 — 엔트리 포인트 (REPL 루프)
├── mini_git/
│   ├── __init__.py
│   ├── models.py           — Commit dataclass
│   ├── repository.py       — Repository 클래스 (상태 관리, 명령 실행)
│   ├── graph.py            — 그래프 알고리즘 (위상정렬, BFS, 조상탐색)
│   ├── index.py            — InvertedIndex 클래스
│   ├── sorting.py          — 정렬 알고리즘 직접 구현 (Merge Sort)
│   └── parser.py           — CLI 명령 파싱 (토큰화, 옵션 추출)
└── docs/
    ├── PROBLEM.md
    ├── SPEC.md
    └── IMPLEMENTATION.md
```

### 5.2 계층 구조

```
[REPL (main.py)]
    │
    ▼ 명령 문자열
[Parser] ─── 파싱 결과 (command, args, options)
    │
    ▼
[Repository] ─── 상태 보유 (commits, branches, HEAD, index)
    │
    ├──▶ [Graph] ─── 위상정렬, BFS, 조상탐색
    ├──▶ [InvertedIndex] ─── 검색 인덱스
    └──▶ [Sorting] ─── 정렬 유틸
```

### 5.3 설계 원칙

- **단일 책임**: 각 모듈은 하나의 관심사만 담당
- **Repository가 Facade 역할**: 외부(REPL)는 Repository만 호출
- **알고리즘 분리**: graph.py, sorting.py는 Repository 상태에 직접 의존하지 않고, 인자로 데이터를 받아 처리
- **테스트 용이성**: 알고리즘 모듈은 순수 함수로 작성하여 독립 테스트 가능

---

## 6. 커밋 Hash 생성 전략

- `hashlib.sha1(f"{author}{message}{timestamp}{counter}".encode()).hexdigest()[:6]`
- counter는 전역 증가 카운터 → 동일 초에 같은 메시지라도 유일성 보장
- 만약 충돌 발생 시 counter 증가 후 재생성

---

## 7. 위상 정렬 전략 (LOG)

- Kahn's Algorithm 적용
- 대상: HEAD에서 도달 가능한 커밋 집합 (BFS로 수집)
- in-degree 계산: 자식→부모 방향이 간선이므로, "자식 수"를 in-degree로 사용
  - 부모가 먼저 출력되려면: 부모의 in-degree = 해당 부모를 참조하는 자식 수
  - in-degree가 0인 노드(자식이 없는 노드가 아닌, 가장 오래된 root)부터 출력
- 정확히는: 간선 방향을 "부모→자식"으로 뒤집어 위상정렬 수행

---

## 8. PATH 최단경로 전략

- 대상 커밋 집합: 저장소 전체 커밋 (무방향 그래프)
- 인접 리스트 구축: 각 커밋의 parents 관계를 양방향으로 등록
- BFS로 최단 경로 탐색
- 동일 거리 경로가 여럿일 때: 모든 최단 경로를 추적 후, `hash1->hash2->...` 문자열로 변환하여 사전순 최소 선택
  - 구현 방식: BFS 시 각 레벨에서 다음 노드 선택 시 정렬(직접 구현 정렬 사용)하여 사전순 우선 탐색
