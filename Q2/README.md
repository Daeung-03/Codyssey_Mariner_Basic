# 파일 기반 가계부 콘솔 프로그램 (budget_app)

학습용 과제(Q2) — 표준 라이브러리만 사용해 4계층(CLI / Service / Repository / Model) 구조로 구현한 콘솔 가계부.
제너레이터 스트리밍, 함수 데코레이터, JSONL 원자적 쓰기, 타입 힌트를 모두 적용한다.

---

## 목차

1. [빠른 시작](#빠른-시작)
2. [전체 명령 레퍼런스](#전체-명령-레퍼런스)
3. [기능별 정책](#기능별-정책)
4. [계층(모듈)별 구현 내용](#계층모듈별-구현-내용)
5. [구현 로직 Overview](#구현-로직-overview)
6. [저장 파일 구조](#저장-파일-구조)
7. [테스트 실행](#테스트-실행)

---

## 빠른 시작

```bash
cd Q2

# 도움말
python3 -m budget_app --help

# 거래 추가 (대화형)
python3 -m budget_app add

# 최근 거래 10건 조회
python3 -m budget_app list --limit 10

# 2024-01 월 요약
python3 -m budget_app summary --month 2024-01
```

기본 데이터 폴더: `./data`  
변경: `--data-dir <경로>` 옵션을 모든 명령 앞에 붙인다.

```bash
python3 -m budget_app --data-dir /tmp/mydata list
```

---

## 전체 명령 레퍼런스

| 명령 | 설명 |
|---|---|
| `add` | 거래 대화형 입력 |
| `list [--limit N]` | 거래 목록 (날짜 역순) |
| `search [필터...]` | 거래 검색 |
| `update --id TX-... [필드...]` | 거래 수정 |
| `delete --id TX-...` | 거래 삭제 |
| `summary --month YYYY-MM [--top N]` | 월별 수입/지출 요약 |
| `budget set --month YYYY-MM --amount N` | 월 예산 설정 |
| `category add` | 카테고리 추가 |
| `category list` | 카테고리 목록 |
| `category remove --name NAME [--reassign-to NAME]` | 카테고리 삭제 |
| `import --from FILE.csv` | CSV 일괄 가져오기 |
| `export --out FILE.csv --month YYYY-MM` | CSV 내보내기 (월별) |
| `export --out FILE.csv --from DATE --to DATE` | CSV 내보내기 (날짜 범위) |

---

## 기능별 정책

### 거래 관리 (Transaction)

#### add — 거래 추가

- 대화형 프롬프트로 6개 항목을 순서대로 입력받는다: 날짜, 타입, 카테고리, 금액, 메모, 태그
- 저장 성공 시 `[저장 완료] id=TX-NNNNNN` 출력
- **ID 생성 규칙**: 기존 거래 중 최대 시퀀스 번호 + 1, 6자리 0-패딩 (`TX-000001`)
  - 중간에 삭제된 레코드가 있어도 항상 `max_seq + 1`로 증가 (갭 허용)

**검증 규칙**

| 필드 | 규칙 | 오류 예시 |
|---|---|---|
| `date` | `YYYY-MM-DD` 포맷 + 실제 존재하는 날짜 | `2024-13-01`, `2023-02-29` |
| `type` | `income` 또는 `expense` 만 허용 | `transfer` |
| `category` | 등록된 카테고리에 존재해야 함 | 등록 전 카테고리명 |
| `amount` | 양의 정수 (1 이상) | `0`, `-500` |
| `memo` | 선택 항목, 빈 값 허용 (None으로 저장) | — |
| `tags` | 쉼표(`,`) 구분 문자열, 없으면 빈 리스트 | — |

#### list — 거래 목록

- 정렬: **날짜 역순 → 같은 날짜는 ID 역순** (최신 거래가 위)
- `--limit` 기본값 20; `--limit 0`이면 빈 목록 반환
- 거래가 없으면 `거래 내역이 없습니다` 출력 후 종료 코드 0

#### search — 거래 검색

- 모든 필터는 **AND 결합** (지정하지 않은 필터는 조건 없음)
- 결과 정렬: list와 동일 (날짜 역순 → ID 역순)

| 옵션 | 설명 |
|---|---|
| `--from YYYY-MM-DD` | 이 날짜 이상 (포함) |
| `--to YYYY-MM-DD` | 이 날짜 이하 (포함) |
| `--category NAME` | 카테고리 완전 일치 |
| `--type income\|expense` | 타입 완전 일치 |
| `--q KEYWORD` | 메모에 키워드 포함 (부분 일치, 대소문자 구분) |
| `--tag TAG` | 태그 목록에 해당 태그 포함 |

#### update — 거래 수정

- `--id`는 필수; 나머지 옵션 중 **최소 1개** 이상을 지정해야 한다
- 지정한 필드만 변경, 나머지는 기존 값 유지
- 변경 후 **동일한 검증 규칙** 재적용 (잘못된 날짜/카테고리 등은 거부)
- `--tags` 지정 시 기존 태그 목록 전체를 교체 (append 아님)
- 아무 필드도 지정하지 않으면 `[오류]`를 출력하고 종료 코드 1 반환

#### delete — 거래 삭제

- 해당 ID가 없으면 `NotFoundError` → `[오류]` + 종료 코드 1
- 삭제 성공 시 `[삭제 완료] id=TX-NNNNNN` 출력

---

### 카테고리 관리 (Category)

#### 기본 카테고리

데이터 폴더가 비어 있을 때 `CategoryService` 생성 시 아래 4개를 자동 등록한다.

```
food  transport  rent  etc
```

기존 카테고리가 1개라도 있으면 자동 등록을 건너뛴다.

#### category add

- 대화형 프롬프트 1회: 카테고리명 입력
- 이미 존재하는 이름이면 `ValidationError` (종료 코드 1)
- 성공 시 `[저장 완료] category=<name>` 출력

#### category list

- 등록 순서대로 출력 (`- <name>` 형식)

#### category remove

| 상황 | 동작 |
|---|---|
| 카테고리가 존재하지 않음 | `NotFoundError` → 종료 코드 1 |
| 카테고리를 사용하는 거래가 없음 | 즉시 삭제 |
| 사용 중인 거래가 있고 `--reassign-to` 미지정 | `CategoryInUseError` → `[힌트]`에 `--reassign-to` 안내 |
| `--reassign-to` 지정, 대상 카테고리 없음 | `NotFoundError` → 종료 코드 1, 원본 카테고리 유지 |
| `--reassign-to` 지정, 대상 카테고리 존재 | 해당 거래 전체를 새 카테고리로 재배정 후 삭제 |

---

### 예산 관리 (Budget)

#### budget set

- `--month YYYY-MM`, `--amount N` 필수
- 같은 월 예산이 이미 있으면 **덮어쓰기** (upsert)
- `amount ≤ 0` 또는 `month` 포맷 오류 시 종료 코드 1
- 성공 시 `[저장 완료] YYYY-MM 예산 N원` 출력

---

### 월별 요약 (Summary)

```bash
python3 -m budget_app summary --month 2024-01 --top 3
```

**출력 항목**

1. 해당 월 데이터 없을 경우 → `YYYY-MM: 데이터 없음` 출력 (이후 항목도 0으로 계속 출력)
2. `총 수입: N원`
3. `총 지출: N원`
4. `잔액: N원` (수입 - 지출)
5. 예산이 설정된 경우 → `예산: N원 (사용률 XX.X%)`
   - 지출 > 예산이면 추가로 `[경고] 예산을 초과했습니다` 출력
6. `지출 TOP <top>` 섹션 (지출 금액 내림차순, 동일 금액은 카테고리명 알파벳 순)
   - `1) <category> <amount>원` 형식

---

### import / export (CSV)

#### CSV 스키마 (고정)

| 컬럼 | 필수 | 설명 |
|---|---|---|
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` / `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양의 정수 |
| `memo` | N | 문자열 (없으면 빈 값) |
| `tags` | N | 쉼표(`,`) 구분 (없으면 빈 값) |

공통: UTF-8 인코딩, 첫 줄 헤더 포함.

#### import

- 행 단위로 검증; 유효하지 않은 행은 건너뛰고 계속 진행
- 완료 시 `[완료] imported=N, skipped=M` 출력
- 가져온 거래의 ID는 기존 최대 ID 이후부터 순차 부여

**skip 조건**: 날짜 포맷 오류, 불가능한 날짜, `type` 오류, 미등록 카테고리, `amount ≤ 0`, 파싱 오류(KeyError/ValueError)

#### export

- `--month YYYY-MM` 또는 `--from`/`--to` 중 **최소 하나** 필요; 없으면 종료 코드 1
- 결과 행 정렬: 날짜 오름차순 → 같은 날짜는 ID 오름차순
- 출력 파일에 헤더 포함; 해당 조건 거래가 0건이어도 헤더만 쓰고 정상 종료
- 완료 시 `[완료] <파일경로> (<N> records)` 출력

---

### 오류 처리 공통 정책

| 오류 유형 | 종료 코드 | 출력 |
|---|---|---|
| 사용자 입력 오류 (`ValidationError`, `NotFoundError`, `CategoryInUseError`) | 1 | `[오류] <message>` + (hint 있으면) `[힌트] <hint>` |
| 시스템 오류 (`StorageError`) | 2 | `[오류] <message>` + `[힌트] <hint>` |
| 예상 외 예외 (`Exception`) | 2 | `[오류] 예기치 못한 문제가 발생했습니다.` + `[힌트] logs/app.log 확인` 안내, 스택트레이스는 로그 파일에만 기록 |

- 스택트레이스는 절대 터미널에 출력하지 않는다.
- `logs/app.log`에 모든 명령 호출 인자, 소요 시간, 예외 스택트레이스가 기록된다.

---

## 계층(모듈)별 구현 내용

```
budget_app/
├── __init__.py          # 빈 패키지 마커
├── __main__.py          # python3 -m budget_app 진입점
├── models.py            # Model 계층
├── exceptions.py        # 예외 계층
├── decorators.py        # 횡단 관심사 데코레이터
├── repository.py        # Repository 계층
├── services.py          # Service 계층
└── cli.py               # CLI 계층
```

### `models.py` — Model 계층

도메인 엔티티만 담당. 순수 데이터 구조로 외부 의존성 없음.

| 클래스 | 필드 | 역할 |
|---|---|---|
| `Transaction` | `id`, `type`, `date`, `amount`, `category`, `memo?`, `tags[]` | 개별 수입/지출 거래 |
| `Category` | `name` | 카테고리 이름 |
| `Budget` | `month`, `amount` | 월 예산 |

모든 모델은 `to_dict() → dict`와 `from_dict(dict) → Self` 쌍을 제공한다.  
`Transaction.from_dict`는 `memo`, `tags` 누락 시 각각 `None`, `[]`로 기본값 처리한다.

---

### `exceptions.py` — 예외 계층

| 이름 | 부모 | 사용 상황 |
|---|---|---|
| `BudgetAppError` | `Exception` | 모든 앱 예외의 루트, `.message`/`.hint` 속성 |
| `ValidationError` | `BudgetAppError` | 날짜·금액·타입·카테고리 입력 오류 |
| `NotFoundError` | `BudgetAppError` | 존재하지 않는 ID·카테고리 참조 |
| `CategoryInUseError` | `BudgetAppError` | 사용 중인 카테고리 삭제 시도 |
| `StorageError` | `BudgetAppError` | 파일 I/O 실패 |

종료 코드 상수:
```python
EXIT_OK           = 0
EXIT_USER_ERROR   = 1   # ValidationError / NotFoundError / CategoryInUseError
EXIT_SYSTEM_ERROR = 2   # StorageError / 예상 외 예외
```

`USER_ERROR_TYPES = (ValidationError, NotFoundError, CategoryInUseError)` — `handle_errors`가 이 튜플로 분기.

---

### `decorators.py` — 횡단 관심사

명령 핸들러는 항상 아래 순서로 3개 데코레이터를 중첩 적용한다.

```python
@handle_errors   # 가장 바깥쪽: 예외 포획·종료 코드 결정
@log_call        # 중간: 호출 인자·결과 로깅
@measure_time    # 가장 안쪽: 실행 시간 측정
def cmd_xxx(args, ctx) -> int: ...
```

| 데코레이터 | 동작 |
|---|---|
| `measure_time` | `time.perf_counter()` 로 소요 시간 측정 → `INFO` 로그(`<name> took X.XXXXs`) |
| `log_call` | 함수 진입 시 `INFO CALL <name> args=... kwargs=...`, 반환 시 `INFO DONE <name> -> exit=N` |
| `handle_errors` | `USER_ERROR_TYPES` → 종료 1 + 터미널 출력; `BudgetAppError` → 종료 2; 그 외 `Exception` → 종료 2 + `logger.exception()` (스택트레이스를 로그에만 기록) |

로거 이름: `"budget_app"` — `main()` 에서 `logs/app.log`에 핸들러 부착.

---

### `repository.py` — Repository 계층

**파일 포맷**: JSONL (한 줄 = JSON 객체 하나).  
**쓰기 정책**: 모든 쓰기는 `_atomic_write_lines` 경유 → temp 파일(`*.jsonl.tmp`) 에 먼저 쓴 뒤 `os.replace()`로 원자적 교체.

| 클래스 | 파일 | 주요 메서드 |
|---|---|---|
| `TransactionRepository` | `transactions.jsonl` | `iter_transactions()`, `append()`, `replace()`, `remove()` |
| `CategoryRepository` | `categories.jsonl` | `iter_categories()`, `append()`, `remove()` |
| `BudgetRepository` | `budgets.jsonl` | `iter_budgets()`, `upsert()`, `get()` |

공통 동작:
- 생성자에서 파일·상위 디렉터리가 없으면 자동 생성 (`_ensure_file`)
- `iter_*()` 는 제너레이터 — 파일을 스트리밍 읽기 (lazy)
- `append/replace/remove` 는 전체 파일을 읽어 메모리에서 수정 후 원자적으로 덮어씀
- `OSError` 발생 시 `StorageError`로 래핑해서 상위로 전달

`BudgetRepository.upsert`: 같은 `month`가 있으면 교체, 없으면 추가 (1 레코드/월 보장).

---

### `services.py` — Service 계층

비즈니스 규칙과 입력 검증을 담당. Repository를 직접 의존하며, CLI 계층에 인터페이스를 제공한다.

**검증 함수** (독립 함수, 실패 시 `ValidationError`)

| 함수 | 규칙 |
|---|---|
| `validate_date(v)` | `YYYY-MM-DD` 포맷 + `datetime.date` 파싱 성공 |
| `validate_month(v)` | `YYYY-MM` 포맷 (정규식 `^\d{4}-\d{2}$`) |
| `validate_amount(v)` | `v > 0` |
| `validate_type(v)` | `v in ("income", "expense")` |

**서비스 클래스**

`CategoryService(repo)`:
- 생성 시 repo가 비어 있으면 `DEFAULT_CATEGORIES = ("food", "transport", "rent", "etc")` 자동 등록
- `add(name)`: 중복 이름 → `ValidationError`
- `remove(name, tx_repo, reassign_to=None)`: 사용 중 + reassign_to 없음 → `CategoryInUseError`; reassign_to 지정 시 관련 거래 전체 재배정 후 삭제

`BudgetService(repo)`:
- `set_budget(month, amount)`: `validate_month` + `validate_amount` 후 `repo.upsert`
- `get_budget(month)`: `repo.get(month)` 위임 (없으면 `None`)

`TransactionService(repo, category_service)`:
- `_next_id()`: 기존 TX 전체 스캔 후 `max_seq + 1` (TX-NNNNNN 포맷)
- `add(...)`: 4-필드 검증 → `Transaction` 생성 → `repo.append`
- `get(id)`: 선형 탐색, 없으면 `NotFoundError`
- `update(id, **fields)`: `get` → `dataclasses.replace` 로 변경 → 재검증 → `repo.replace`
- `delete(id)`: `get` (없으면 예외) → `repo.remove`
- `list(limit)`: 전체 로드 → `(date, id)` 역순 정렬 → slicing
- `search(**filters)`: AND 결합 필터 → `(date, id)` 역순 정렬
- `summary(month, top)`: 해당 월 거래 필터 → 수입/지출 합산 → 카테고리별 지출 집계 → top N 반환

---

### `cli.py` — CLI 계층

`argparse` 기반 서브커맨드 파서. 모든 명령 핸들러는 `(args: Namespace, ctx: Context) -> int` 시그니처.

**`Context`**: data_dir을 받아 3개 Repository + 3개 Service를 초기화하는 DI 컨테이너.

**`build_parser()`**: 10개 서브커맨드를 등록. `budget`/`category`는 2단계 중첩 서브파서.

**`dispatch(args, ctx)`**: `args.command` 분기
- `"budget"` → `BUDGET_HANDLERS[args.budget_command]`
- `"category"` → `CATEGORY_HANDLERS[args.category_command]`
- 나머지 → `COMMAND_HANDLERS[args.command]`

**`main(argv, log_dir)`**: 파서 실행 → 로그 설정(`logs/app.log`) → Context 생성 → dispatch 호출

---

## 구현 로직 Overview

### 데이터 흐름

```
사용자 입력(argv/stdin)
        │
        ▼
   cli.main()
   ├── argparse.parse_args()       # 옵션 파싱
   ├── logging.basicConfig()       # 로그 파일 설정
   └── Context(data_dir)           # DI 컨테이너 초기화
           │
           ▼
   dispatch(args, ctx)
           │
           ▼
   cmd_xxx(args, ctx)              # @handle_errors @log_call @measure_time
           │
           ▼
   Service.method(...)             # 검증 + 비즈니스 규칙
           │
           ▼
   Repository.iter/append/replace  # JSONL 파일 읽기/쓰기
           │
           ▼
   Model.from_dict / to_dict       # 직렬화/역직렬화
```

### 쓰기 경로 (원자적 교체)

```
현재 파일 전체 읽기 (iter_*)
        │
        ▼
메모리에서 목록 수정 (append/replace/remove)
        │
        ▼
*.jsonl.tmp 에 전체 쓰기
        │
        ▼
os.replace(tmp → 원본)    ← 이 순간 원자적으로 교체
```

temp 파일 쓰기가 실패해도 원본은 손상되지 않는다.

### 데코레이터 적용 순서와 호출 스택

```
handle_errors.__call__
  └─ log_call.__call__
       └─ measure_time.__call__
            └─ 실제 cmd_xxx 함수 본문
```

- `measure_time`은 `finally`에서 시간을 기록 → 예외가 전파돼도 항상 기록
- `log_call`은 `DONE` 로그를 반환값 기록 후 전파 → 예외 시 DONE 로그 미기록
- `handle_errors`가 최외곽에서 모든 예외를 포획해 종료 코드로 변환

### ID 생성 전략

```
기존 TX 전체 스캔 → 최대 시퀀스(N) 추출
→ TX-{N+1:06d}
```

- 삭제 후 재추가해도 번호는 감소하지 않는다 (단조 증가)
- import 시에도 동일 로직 적용 → 기존 거래와 번호 충돌 없음

### search 필터 (AND 결합)

```python
matches(t) =
  (date_from is None or t.date >= date_from)
  AND (date_to is None or t.date <= date_to)
  AND (category is None or t.category == category)
  AND (type is None or t.type == type)
  AND (query is None or query in (t.memo or ""))
  AND (tag is None or tag in t.tags)
```

날짜 비교는 `YYYY-MM-DD` 문자열 사전순이 ISO 8601과 일치하므로 숫자 변환 없이 비교한다.

---

## 저장 파일 구조

```
Q2/
├── data/
│   ├── transactions.jsonl   # 거래 (JSONL)
│   ├── categories.jsonl     # 카테고리 (JSONL)
│   └── budgets.jsonl        # 예산 (JSONL)
└── logs/
    └── app.log              # 데코레이터 실행 로그
```

JSONL 예시:

```jsonl
{"id": "TX-000001", "type": "expense", "date": "2024-01-15", "amount": 15000, "category": "food", "memo": "점심", "tags": ["meal"]}
{"id": "TX-000002", "type": "income", "date": "2024-01-31", "amount": 3000000, "category": "etc", "memo": null, "tags": []}
```

---

## 테스트 실행

```bash
cd Q2

# 전체 테스트
python3 -m unittest discover -s tests -v

# 특정 모듈만
python3 -m unittest tests.test_scenarios_transaction -v
python3 -m unittest tests.test_scenarios_category -v
python3 -m unittest tests.test_scenarios_budget -v
python3 -m unittest tests.test_scenarios_import_export -v
python3 -m unittest tests.test_scenarios_storage -v
python3 -m unittest tests.test_scenarios_error_handling -v
```

**테스트 파일 구성**

| 파일 | 테스트 대상 |
|---|---|
| `test_models.py` | Model 직렬화/역직렬화 |
| `test_exceptions.py` | 예외 계층, 종료 코드 상수 |
| `test_decorators.py` | 데코레이터 단위 |
| `test_repository.py` | TransactionRepository CRUD |
| `test_repository_category_budget.py` | CategoryRepository, BudgetRepository |
| `test_services_category_budget.py` | 검증 함수, CategoryService, BudgetService |
| `test_services_transaction_write.py` | TransactionService 쓰기 경로 |
| `test_services_transaction_read.py` | TransactionService 읽기 경로 |
| `test_cli_transactions.py` | CLI add/list/search/update/delete |
| `test_cli_summary_budget_category.py` | CLI summary/budget/category |
| `test_cli_import_export.py` | CLI import/export |
| `test_scenarios_transaction.py` | 거래 전체 생명주기·경계값 시나리오 |
| `test_scenarios_category.py` | 카테고리 관리 시나리오 |
| `test_scenarios_budget.py` | 예산·요약 시나리오 |
| `test_scenarios_import_export.py` | import/export 시나리오 |
| `test_scenarios_storage.py` | 저장소 원자적 쓰기·JSONL 정합성 |
| `test_scenarios_error_handling.py` | 오류 처리 정책 시나리오 |
