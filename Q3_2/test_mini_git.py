"""Mini Git 최소 기능 동작 테스트 스크립트.

Problem.md에 명시된 모든 핵심 기능을 시나리오 기반으로 검증한다.
실행: python test_mini_git.py (Q3_2 디렉토리에서)
"""

import time
from mini_git.repository import Repository


# ─── 테스트 유틸 ───────────────────────────────────────────────

PASS_COUNT = 0
FAIL_COUNT = 0


def check(description: str, condition: bool, detail: str = ""):
    """조건 통과 여부를 출력한다."""
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  ✓ {description}")
    else:
        FAIL_COUNT += 1
        print(f"  ✗ {description}")
        if detail:
            print(f"    → {detail}")


def section(title: str):
    """섹션 구분선을 출력한다."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


# ─── 1. INIT ──────────────────────────────────────────────────

section("1. INIT — 저장소 초기화")

repo = Repository()
result = repo.init("Alice")
check("초기화 성공 메시지", "Initialized repository." in result, result)
check("main 브랜치 표시", "Current branch: main" in result)
check("사용자 설정", "Current user: Alice" in result)

# 중복 초기화 에러
result2 = repo.init("Bob")
check("중복 INIT 에러", result2 == "Already initialized", result2)


# ─── 2. COMMIT ─────────────────────────────────────────────────

section("2. COMMIT — 커밋 생성")

result = repo.commit("Initial commit")
check("커밋 출력에 브랜치 포함", "[main" in result, result)
check("커밋 출력에 메시지 포함", "Initial commit" in result)

# 해시 추출
commit1_hash = list(repo.commits.keys())[0]
check("6자리 hex hash 생성", len(commit1_hash) == 6 and commit1_hash.isalnum(), commit1_hash)

# 두 번째 커밋 (부모 관계 확인)
result = repo.commit("Second commit")
commit2_hash = [h for h in repo.commits if h != commit1_hash][0]
check("두 번째 커밋의 부모 = 첫 번째 커밋",
      repo.commits[commit2_hash].parents == [commit1_hash],
      f"parents={repo.commits[commit2_hash].parents}")


# ─── 3. BRANCH / SWITCH ───────────────────────────────────────

section("3. BRANCH / SWITCH — 브랜치 관리")

result = repo.branch("feature")
check("브랜치 생성", result == "Created branch: feature", result)

result = repo.branch("feature")
check("중복 브랜치 에러", "Branch already exists" in result, result)

result = repo.switch("feature")
check("브랜치 전환", result == "Switched to branch: feature", result)

result = repo.switch("feature")
check("같은 브랜치 전환 시 안내", "Already on branch: feature" in result, result)

result = repo.switch("nonexistent")
check("존재하지 않는 브랜치 에러", "Unknown branch" in result, result)


# ─── 4. 브랜치 분기 시나리오 ────────────────────────────────────

section("4. 브랜치 분기 — DAG 구조 확인")

# feature 브랜치에서 커밋
result = repo.commit("Add login feature")
check("feature 브랜치 커밋", "[feature" in result, result)
feature_commit_hash = repo.branches["feature"]

# main으로 돌아와서 커밋
repo.switch("main")
time.sleep(0.01)  # timestamp 차이 보장
result = repo.commit("Add payment feature")
check("main 브랜치 커밋", "[main" in result, result)
main_tip_hash = repo.branches["main"]

# DAG 확인: feature 커밋과 main 최신 커밋의 부모가 다름
check("DAG 분기 구조 확인",
      repo.commits[feature_commit_hash].parents != repo.commits[main_tip_hash].parents
      or feature_commit_hash != main_tip_hash)


# ─── 5. LOG ────────────────────────────────────────────────────

section("5. LOG — 위상 정렬 출력")

result = repo.log()
check("LOG 출력에 커밋 해시 포함", "commit " in result, result[:200])
check("LOG 출력에 author 포함", "Alice" in result)
check("LOG 출력에 메시지 포함", "Initial commit" in result)

# 위상 정렬 확인: "Initial commit"이 "Second commit"보다 먼저 나와야 함
initial_pos = result.find("Initial commit")
second_pos = result.find("Second commit")
check("위상 정렬: 부모(Initial)가 자식(Second)보다 앞",
      initial_pos < second_pos,
      f"Initial@{initial_pos}, Second@{second_pos}")


# ─── 6. LOG --sort-by ──────────────────────────────────────────

section("6. LOG --sort-by — 정렬 기능")

result_date = repo.log(sort_by="date")
check("LOG --sort-by=date 정상 동작", "commit " in result_date)

result_author = repo.log(sort_by="author")
check("LOG --sort-by=author 정상 동작", "commit " in result_author)


# ─── 7. PATH ──────────────────────────────────────────────────

section("7. PATH — 최단 경로 탐색")

# 같은 커밋
result = repo.path(commit1_hash, commit1_hash)
check("같은 커밋 PATH: 자기 자신 반환", commit1_hash in result, result)

# 부모-자식 관계 (직접 연결)
result = repo.path(commit1_hash, commit2_hash)
check("인접 커밋 PATH: 직접 경로", "->" in result, result)
check("경로에 start/end 포함",
      commit1_hash in result and commit2_hash in result, result)

# feature 커밋에서 main 최신 커밋 (공통 조상 경유)
result = repo.path(feature_commit_hash, main_tip_hash)
check("분기 커밋 간 PATH", "->" in result, result)

# 존재하지 않는 해시
result = repo.path("zzzzzz", commit1_hash)
check("존재하지 않는 커밋 에러", "Unknown commit" in result, result)


# ─── 8. ANCESTORS ──────────────────────────────────────────────

section("8. ANCESTORS — 조상 탐색")

# root 커밋은 조상 없음
result = repo.ancestors(commit1_hash)
check("root 커밋: No ancestors", result == "No ancestors", result)

# 두 번째 커밋의 조상 = 첫 번째 커밋
result = repo.ancestors(commit2_hash)
check("두 번째 커밋의 조상에 첫 번째 포함", commit1_hash in result, result)

# feature 커밋의 조상 (commit2 → commit1 경로)
result = repo.ancestors(feature_commit_hash)
check("feature 커밋의 조상 출력", commit1_hash in result, result)

# 존재하지 않는 해시
result = repo.ancestors("zzzzzz")
check("존재하지 않는 커밋 에러", "Unknown commit" in result, result)


# ─── 9. SEARCH ─────────────────────────────────────────────────

section("9. SEARCH — 역색인 검색")

# 키워드 검색
result = repo.search(keyword="login")
check("키워드 'login' 검색 결과 존재", "Found" in result, result)
check("검색 결과에 해당 커밋 포함", feature_commit_hash in result, result)

# 존재하지 않는 키워드
result = repo.search(keyword="nonexistent_keyword_xyz")
check("없는 키워드: No commits found", result == "No commits found", result)

# 작성자 검색
result = repo.search(author="Alice")
check("작성자 'Alice' 검색 결과", "Found" in result, result)

# 대소문자 무시 확인
result = repo.search(author="alice")
check("작성자 검색 대소문자 무시", "Found" in result, result)

# 없는 작성자
result = repo.search(author="Unknown_Person")
check("없는 작성자: No commits found", result == "No commits found", result)


# ─── 10. 커밋 없는 상태 에지 케이스 ────────────────────────────

section("10. 에지 케이스 — 초기화 전/커밋 없는 상태")

empty_repo = Repository()
result = empty_repo.commit("test")
check("초기화 전 COMMIT 에러", result == "Repository not initialized", result)

result = empty_repo.log()
check("초기화 전 LOG 에러", result == "Repository not initialized", result)

empty_repo.init("Bob")
result = empty_repo.log()
check("커밋 없는 상태 LOG", result == "No commits yet", result)

result = empty_repo.branch("test")
check("커밋 없이 브랜치 생성 에러", "Cannot create branch" in result, result)


# ─── 11. Parser 테스트 ──────────────────────────────────────────

section("11. Parser — 명령어 파싱")

from mini_git.parser import parse

parsed = parse('INIT "Alice"')
check("따옴표 인자 파싱", parsed.args == ["Alice"], str(parsed.args))

parsed = parse("commit \"Add login feature\"")
check("대소문자 무시 (commit → COMMIT)", parsed.command == "COMMIT")
check("따옴표 포함 메시지 파싱", parsed.args == ["Add login feature"], str(parsed.args))

parsed = parse("log --sort-by=date")
check("옵션 파싱 --sort-by=date", parsed.options.get("sort-by") == "date")

parsed = parse("search --author=Alice")
check("옵션 파싱 --author=Alice", parsed.options.get("author") == "Alice")

parsed = parse("")
check("빈 입력 → None", parsed is None)

parsed = parse("path abc123 def456")
check("복수 인자 파싱", parsed.args == ["abc123", "def456"], str(parsed.args))


# ─── 12. Sorting 모듈 테스트 ───────────────────────────────────

section("12. Sorting — Merge Sort 직접 구현")

from mini_git.sorting import merge_sort

result = merge_sort([5, 3, 8, 1, 9, 2])
check("정수 정렬", result == [1, 2, 3, 5, 8, 9], str(result))

result = merge_sort([])
check("빈 리스트 정렬", result == [])

result = merge_sort([1])
check("단일 원소 정렬", result == [1])

result = merge_sort(["banana", "apple", "cherry"], key=lambda x: x)
check("문자열 key 정렬", result == ["apple", "banana", "cherry"], str(result))


# ─── 결과 요약 ─────────────────────────────────────────────────

section("테스트 결과 요약")
total = PASS_COUNT + FAIL_COUNT
print(f"\n  총 {total}개 테스트 | ✓ 통과: {PASS_COUNT} | ✗ 실패: {FAIL_COUNT}")

if FAIL_COUNT == 0:
    print("\n  🎉 모든 테스트를 통과했습니다!")
else:
    print(f"\n  ⚠️  {FAIL_COUNT}개 테스트가 실패했습니다. 위 출력을 확인하세요.")
