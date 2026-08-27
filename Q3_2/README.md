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
