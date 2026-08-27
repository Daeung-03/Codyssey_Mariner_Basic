# Mini Git 구현 기록

## 프로젝트 목표

Git의 핵심 자료구조(DAG, 해시맵, 역색인)를 직접 구현하여 CLI 기반 Mini Git을 완성한다.

---

## Phase 1: 설계 (현재 단계)

### 목표

PROBLEM.md의 요구사항을 구현 가능한 수준의 명세로 변환한다.

### 작업 내용

1. 요구사항 분류 (필수/제약/주의점)
2. 모호한 정책에 대해 유저와 Q&A → 확정
3. 기능별 자료구조 매핑
4. Domain 모델 및 아키텍처 설계
5. SPEC.md 작성

### 과제 해석 (유저 결정 사항)

아래는 PROBLEM.md에서 명시되지 않았거나 모호했던 부분에 대해 유저가 직접 결정한 정책이다.

| # | 질문 | 결정 |
|---|------|------|
| 1 | LOG 출력 범위 | 현재 브랜치 HEAD에서 도달 가능한 커밋만 출력. 브랜치 내 커밋이 없으면 main 커밋을 보여줌 |
| 2 | INIT 중복 호출 | 에러 메시지 출력 ("Already initialized") |
| 3 | BRANCH 중복 생성 | 에러 처리 ("Branch already exists: \<name\>") |
| 4 | 첫 COMMIT (HEAD가 null) | parents를 빈 리스트로 처리 (root commit) |
| 5 | PATH 사전순 비교 기준 | hash 문자열 전체를 비교 기준으로 사용 |
| 6 | 보너스 과제 (Merge, Diff, 정렬 비교) | 포함하지 않음. 필수 기능만 구현 |
| 7 | timestamp 출력 포맷 | `YYYY-MM-DD HH:MM:SS`로 통일 |
| 8 | BRANCH (커밋 없을 때) | 에러 처리 — 실제 Git과 동일하게 최소 1커밋 필요 |
| 9 | LOG (main에도 커밋 없을 때) | "No commits yet" 출력 |
| 10 | PATH (같은 커밋 2번 입력) | 자기 자신만 출력 (`Path: <hash>`) |
| 11 | ANCESTORS (root commit) | "No ancestors" 출력 |
| 12 | SWITCH (현재 브랜치로 전환) | "Already on branch: \<name\>" 출력 |

### 산출물

- `docs/SPEC.md` — 구현 명세 및 설계 문서
- `docs/IMPLEMENTATION.md` — 본 문서 (과정 기록)

---

## Phase 2: 구현

### 완료

- `mini_git/models.py` — `Commit` dataclass + `generate_commit_hash()` 유틸 작성
- `mini_git/sorting.py` — Merge Sort 직접 구현 (안정 정렬, key 함수 지원)
- `mini_git/index.py` — InvertedIndex 클래스 (키워드/작성자 역색인, O(1) 조회)
- `mini_git/graph.py` — 위상 정렬(Kahn's), BFS 최단 경로, 조상 탐색 (순수 함수)

---

## Phase 3: 검증 (다음 단계)

> (미작성 — 테스트 시 업데이트 예정)
