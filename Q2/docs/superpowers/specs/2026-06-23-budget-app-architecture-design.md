# Q2: 파일 기반 가계부 콘솔 프로그램 — 아키텍처 & 정책 설계

- 대상 브랜치: `Q2`
- 원문: `Q2/Q2.md`
- 목적: **서비스 완성이 아니라 학습.** 제너레이터 스트리밍 / 데코레이터 분리 / JSONL 포맷 / 원자적 쓰기를
  "안 썼다면 어떻게 됐을지"와 대조하며 설명할 수 있는 구조로 설계한다.
- 범위: Q2.md 2번 항목의 핵심 10개 기능만 다룬다. 5번 보너스 과제(백업, 반복 내역, 테이블 포맷 정렬)는
  이번 설계 범위에서 제외한다. (단, 보너스 중 "저장 원자성 강화"는 핵심 기능에 이미 정책으로 포함했다.)

## 1. 확정된 정책 결정 (요약)

| 항목 | 결정 | 근거 |
|---|---|---|
| 저장 포맷 | JSONL (CSV 아님) | 제너레이터 스트리밍 설명을 위해 선택 |
| 아키텍처 스타일 | 4계층 분리 (CLI / Service / Repository / Model) | 과제 본문이 명시적으로 권장, 계층별 책임 설명이 가장 쉬움 |
| update 입력 방식 | 옵션 기반 (`--id` + 변경할 필드만) | search/list/delete 등과 입력 방식 일관, 자동화·테스트 용이 |
| 카테고리 초기 상태 | 빈 파일이면 기본 카테고리(food/transport/rent/etc) 자동 생성 | 학습자가 막힘 없이 바로 add를 사용할 수 있음 |
| 원자적 쓰기 범위 | add/update/delete/import/category/budget — **모든 쓰기 작업에 일괄 적용** | "쓰기 정책은 하나"라는 단일 설명으로 통일 (성능보다 설명 가능성 우선) |
| 카테고리 삭제(사용중) | 기본은 차단. `--reassign-to <다른카테고리>`를 함께 줄 때만 일괄 대체 후 삭제 | 안 A(차단)/안 B(대체 요구) 중 택1이 아니라 둘을 한 옵션으로 통합 |
| import/export 교환 포맷 | CSV (내부 저장은 JSONL) | 과제 본문이 CSV 고정 스키마를 직접 명시 — 선택이 아닌 요구사항 |

## 2. 모듈 구조

```
budget_app/
├── __main__.py     # 진입점: python -m budget_app
├── cli.py          # argparse 서브커맨드 + 대화형 input() + 명령 디스패치 + 데코레이터 부착
├── decorators.py   # handle_errors / log_call / measure_time
├── exceptions.py   # 예외 계층 + 종료코드 매핑
├── models.py       # dataclass: Transaction, Category, Budget
├── repository.py   # JSONL 스트리밍 read + 원자적 write — TransactionRepository / CategoryRepository / BudgetRepository
└── services.py     # 검증 + 비즈니스 규칙 — TransactionService / CategoryService / BudgetService

data/                # 기본 저장 폴더 (--data-dir로 변경 가능)
├── transactions.jsonl
├── categories.jsonl
└── budgets.jsonl

logs/
└── app.log          # log_call이 기록하는 운영 로그 (과제의 "3개 이상 데이터 파일" 요구와는 무관한 부가 파일)
```

### 계층별 책임

| 계층 | 책임 | 하지 않는 일 |
|---|---|---|
| CLI | 인자 파싱/대화형 입력 수집, Service 호출, 데코레이터 부착, 결과 출력 | 검증·계산·파일 접근 안 함 |
| Service | 입력 검증, 비즈니스 규칙(예산율, TOP N, 카테고리 사용중 체크), ID 발급 | JSONL 포맷·argparse를 모름 |
| Repository | JSONL 스트리밍 읽기, 원자적 쓰기(temp+rename) | "양수 금액인지" 같은 규칙을 모름 |
| Model | 데이터 모양만 정의(dataclass + type hint) | 동작 없음 |

### 데이터 흐름 예시 (add)

`cli.cmd_add()` (대화형 입력 수집) → `services.TransactionService.add()` (검증 + ID 발급)
→ `repository.TransactionRepository.append()` (원자적 쓰기) → CLI가 결과 출력

이 구조에서 "Service가 없다면?" — CLI에 검증 로직이 흩어져서 `import`(CSV 경로)와 `add`(대화형 경로)
양쪽에서 검증 코드를 중복 작성해야 한다. `update`/`import`도 같은 검증 함수를 재사용한다.

## 3. 데이터 모델 & 저장 정책

```python
@dataclass
class Transaction:
    id: str                  # "TX-000012"
    type: Literal["income", "expense"]
    date: str                # "YYYY-MM-DD"
    amount: int               # 양수
    category: str
    memo: str | None = None
    tags: list[str] = field(default_factory=list)

@dataclass
class Category:
    name: str                 # 유일

@dataclass
class Budget:
    month: str                # "YYYY-MM"
    amount: int
```

**JSONL 라인 예시**

```jsonl
# transactions.jsonl
{"id": "TX-000012", "type": "expense", "date": "2024-01-15", "amount": 15000, "category": "food", "memo": "점심", "tags": ["meal"]}

# categories.jsonl
{"name": "food"}

# budgets.jsonl
{"month": "2024-01", "amount": 500000}
```

**ID 발급 정책**: 별도 카운터 파일을 두지 않는다. `add`/`import` 시
`TransactionRepository.iter_transactions()`(아래 4-2의 동일한 제너레이터)로 파일을 끝까지 스트리밍하며
기존 ID의 최대 숫자를 추적해 `TX-{max+1:06d}`를 발급한다. 카운터 파일을 따로 만들지 않는 이유는
"읽기는 항상 같은 스트리밍 경로를 거친다"는 일관성을 깨지 않기 위함이다.

**기본 카테고리**: `categories.jsonl`이 비어 있는 최초 실행 시 `food, transport, rent, etc`를 자동 생성한다.

## 4. 핵심 학습 포인트 4가지 — Why / Without 비교 / 정책

### 4-1. JSONL vs 단일 JSON 배열 파일

| | 단일 JSON 배열 (`[{...}, {...}]`) | JSONL (줄마다 객체 하나) |
|---|---|---|
| 읽기 | `json.load()`로 파일 전체를 한 번에 파싱해야 첫 레코드라도 접근 가능 | 한 줄씩 읽고 그 줄만 `json.loads()` |
| 1건 추가 | 배열 전체를 메모리에 올려 닫는 `]`까지 다시 써야 함 | 끝에 한 줄 추가 (단, 본 설계는 일관성을 위해 4-4의 temp+rename 적용) |
| 손상 내구성 | 문법 오류 1곳 = 파일 전체 파싱 불가 | 깨진 줄만 스킵 가능, 다른 줄은 영향 없음 |

**정책**: `transactions.jsonl` / `categories.jsonl` / `budgets.jsonl` 모두 JSONL. JSONL은 4-2(제너레이터
스트리밍)의 전제조건이다 — 배열 포맷이었다면 `json.load()` 한 번에 전체를 메모리로 올려야 해서
스트리밍 자체가 불가능했다.

### 4-2. 제너레이터 스트리밍

```python
# repository.py — 모든 읽기는 이 형태를 거친다
def iter_transactions(self) -> Iterator[Transaction]:
    with open(self.path, encoding="utf-8") as f:
        for line in f:
            yield Transaction.from_dict(json.loads(line))
```

**Without 비교**: `yield` 대신 `return [... for line in f]`였다면 `list --limit 3`도 파일의 모든 줄을
파싱한 뒤에야 앞 3개를 자를 수 있다.

**정책 (스트리밍의 경계를 정직하게 명시)**: `list`/`search`는 "최신순" 요구사항 때문에
- 스트리밍 구간: 파일을 한 줄씩 읽으며 검색 조건(날짜/카테고리/타입/키워드/태그)을 그 줄만 보고 즉시 판단.
  조건에 안 맞는 줄은 끝까지 `Transaction` 객체로 만들지 않는다.
- 비-스트리밍 구간: 조건을 만족한 결과(보통 전체보다 훨씬 적음)만 모아 날짜 역순 정렬 + `--limit`/`--top` 적용.

완전한 스트리밍이 아니라 "파싱+필터링은 스트리밍, 정렬은 materialize 후"라는 한계를 그대로 보여주는 것이
오히려 좋은 학습 포인트다.

**`list`와 `search`의 차이를 정직하게 구분**: `search`는 필터 조건이 있어 후보 집합이 실제로 줄어든다
(스트리밍이 메모리 절약에 직접 기여). 반면 `list`는 필터 조건이 없으므로 모든 레코드가 그대로
materialize 대상이 된다 — 이때 제너레이터가 주는 이점은 "후보를 줄이는 것"이 아니라 "파일을 한 줄씩
읽으며 텍스트를 한 번에 통째로 메모리에 올리지 않는 것"으로 한정된다. 이 구분을 명시해야 "제너레이터를
쓰면 항상 메모리를 아낀다"는 과장된 설명을 피할 수 있다.

### 4-3. 데코레이터

```python
# decorators.py — 적용 순서 고정
@handle_errors    # 가장 바깥쪽 — 아래 모든 데코레이터/본문의 예외를 받아야 함
@log_call          # 중간 — 호출 인자/결과를 logs/app.log에 기록
@measure_time      # 가장 안쪽 — 실제 실행 시간만 측정
def cmd_add(args: Namespace) -> int: ...
```

**Without 비교**: 이 셋이 없으면 `cmd_add`, `cmd_update`, `cmd_delete` 등 10개 명령 함수 각각에
`try/except` + 로그 출력 + `time.perf_counter()` 측정 코드를 10번 복붙해야 한다.

**정책**:
- 데코레이터는 CLI 계층의 명령 핸들러 함수에만 적용한다 (Service/Repository에는 적용하지 않음 — 적용
  범위가 섞이면 "어디서 예외가 잡히는지" 설명이 꼬인다).
- 순서가 고정인 이유: 데코레이터는 먼저 쓴 것이 가장 바깥에서 감싸므로, `handle_errors`가 1번째여야
  `log_call`/`measure_time` 내부에서 난 예외도 잡을 수 있다.

### 4-4. 원자적 쓰기 (temp + rename)

**Without 비교**: 파일을 직접 열어 덮어쓰는 도중 프로세스가 죽거나 디스크가 가득 차면 파일이 반쪽만
쓰인 상태로 남는다 — 다음 실행 때 JSONL 파싱이 중간 줄에서 깨진다.

**정책**: 모든 쓰기 작업(add/update/delete/import/category */budget set)은
1. 같은 디렉터리에 임시 파일(`transactions.jsonl.tmp`)을 새로 쓰고
2. `os.replace(tmp, real)`로 원자적 교체

로 통일한다. `add`도 "기존 내용 스트리밍 + 새 레코드 1줄 추가"를 임시 파일에 써서 교체하는 방식으로
구현한다 — append 한 줄만 쓰는 것보다 비효율적이지만, "쓰기 정책은 항상 하나"라는 일관된 설명을
우선한다 (성능보다 설명 가능성을 택한 트레이드오프).

## 5. 명령어별 정책표

| 명령 | 입력 방식 | 핵심 검증/규칙 (Service) | 정상 출력 | 엣지케이스 |
|---|---|---|---|---|
| **add** | 대화형만 (날짜/타입/카테고리/금액/메모/태그) | 날짜 형식, type∈{income,expense}, amount>0, category 존재 | `[저장 완료] id=TX-000012` | 미등록 카테고리 → 안내 후 재입력 유도 |
| **list** | `--limit N` (기본 20) | 없음 | 최신순 N건 | 데이터 없음 → "거래 내역이 없습니다" |
| **search** | `--from/--to/--category/--type/--q/--tag` (AND 결합) | 날짜 형식, type 값 검증 | 조건 매칭 최신순 | 매칭 0건 → "조건에 맞는 거래가 없습니다" |
| **summary** | `--month YYYY-MM`(필수), `--top N`(기본 3) | month 형식 | 총수입/총지출/잔액 + TOP N + 예산 사용률 | 해당 월 데이터 없음 → "데이터 없음" 명시(예산 있으면 사용률 0%로 별도 표시) |
| **budget set** | `--month --amount` (별도 "조회" 명령 없음 — 조회는 `summary` 출력에 통합) | amount>0, month 형식 | `[저장 완료] {month} 예산 {amount}원` | 기존 월 예산 있으면 upsert(교체) |
| **category add/list/remove** | add: 대화형, list: 없음, remove: `--name` (+선택 `--reassign-to <다른카테고리>`) | add: 중복명 차단, remove: 사용중 체크 | 목록/추가/삭제 결과 | 사용중 카테고리 삭제 시도 → 차단. `--reassign-to <다른카테고리>` 지정 시에만 일괄 대체 후 삭제 |
| **update** | `--id` + 변경할 필드만 옵션으로 | 지정된 필드만 add와 동일 검증 로직 재사용 | 수정 성공 메시지 | 없는 id → 실패 메시지, 필드 0개 지정 → "변경할 필드를 지정하세요" |
| **delete** | `--id` | 존재 여부만 | 삭제 성공 메시지 | 없는 id → 실패 메시지 |
| **import** | `--from <csv>` | 각 행에 add와 동일 검증 (실패 행은 skip, 전체 중단 안 함) | `[완료] imported=5, skipped=0` | 스키마 누락 컬럼 → 해당 행 skip |
| **export** | `--out <csv>` + (`--month` 또는 `--from/--to`) 중 최소 1개 필수 | 조건 미지정 시 오류 | `[완료] export.csv (12 records)` | 조건 없이 호출 → ValidationError |

**공통 정책**
- `update`/`delete`/`import`의 검증 로직은 `add`와 같은 Service 함수를 재사용한다. CLI 입력 경로
  (대화형/옵션/CSV)가 달라도 검증 규칙은 한 곳에만 존재한다.
- `export`는 `iter_transactions()`로 조건에 맞는 레코드를 스트리밍 필터링하며 `csv.writer`로 한 줄씩
  바로 쓴다 (필터링된 결과를 한 번에 메모리에 모으지 않음).
- `import`는 `csv.DictReader`로 CSV를 한 행씩 읽으며(스트리밍) 각 행을 `TransactionService.add()`에
  그대로 전달한다.

## 6. import/export 교환 포맷이 CSV인 이유 (JSONL과의 역할 분리)

내부 영구 저장(`transactions.jsonl` 등)은 JSONL이지만, import/export는 Q2.md 135~151행이 직접
못 박은 CSV 고정 스키마를 따른다 — 이는 설계 선택이 아니라 과제 요구사항이다.

| | CSV (교환 포맷) | JSONL (내부 저장 포맷) |
|---|---|---|
| 장점 | 엑셀/구글시트로 바로 열어 편집 가능, 헤더 1줄만 있으면 됨(같은 데이터량 대비 용량이 더 작음) | 줄마다 타입이 보존됨(숫자/리스트 구분), 선택 필드는 키를 생략하면 됨 → 스키마가 유연 |
| 단점 | 모든 값이 문자열이라 파싱 시 직접 캐스팅 필요, `tags`처럼 리스트성 데이터는 쉼표 구분 문자열로 욱여넣어야 함 | 사람이 엑셀처럼 열어 수정하기 불편, 키 이름이 줄마다 반복돼 CSV보다 용량이 큼 |

정리: **CSV = 사람·외부 시스템과 주고받기 좋음, JSONL = 앱이 스스로 저장·스트리밍하기 좋음.**
같은 "한 줄=한 레코드" 구조라도 소비자가 사람(스프레드시트)이냐 프로그램이냐에 따라 적합한 포맷이 다르다.

## 7. 예외 / 종료 코드 정책

```
exceptions.py
BudgetAppError (base)
├── ValidationError      # 입력 형식/값 오류 → exit 1
├── NotFoundError         # id/month/category 없음 → exit 1
├── CategoryInUseError    # 사용중 카테고리 삭제 시도(--reassign-to 없이) → exit 1
└── StorageError          # 파일 I/O 문제 → exit 2
(미예상 Exception)         # → exit 2
```

- **출력 정책**: `[오류] {원인}` + `[힌트] {해결 방법}` 형식만 stdout에 출력한다. 스택트레이스는 화면에
  노출하지 않는다.
- **로그 분리**: 스택트레이스/상세 정보는 `log_call` 데코레이터가 `logs/app.log`에 기록한다. 이 로그
  파일은 과제의 "3개 이상 데이터 파일" 요구사항과는 무관한 운영 로그다.
- **종료 코드**: 정상 0 / 사용자가 고칠 수 있는 오류(Validation/NotFound/CategoryInUse) 1 / 시스템·예상치
  못한 오류(Storage/기타) 2.
- 이 정책은 4-3(데코레이터)의 실제 적용 사례다 — 데코레이터가 없었다면 각 명령 함수 안에서 사용자 출력과
  로깅이 뒤섞여 책임이 분리되지 않았을 것이다.

## 8. 제약 사항 (과제 원문 그대로)

- Python 3.10 이상, 표준 라이브러리만 사용 (pip install 금지)
- 저장 파일은 3개 이상(transactions/categories/budgets)으로 분리, 포맷은 JSONL로 통일
- CLI 옵션 표기는 `--`로 통일, 모든 명령은 `--help` 지원 (argparse 기본 기능으로 충족)
- 오류 시 스택트레이스 출력 금지, 오류 종료 코드는 0이 아니어야 함

## 9. 범위 외 (이번 설계에 포함하지 않음)

- 백업 기능, 반복 내역 자동 생성, 콘솔 테이블 정렬 포맷터 — Q2.md 5번 보너스 과제. 4계층 구조상
  `repository.py`/`services.py`에 메서드를 추가하는 정도로 확장 가능하나, 핵심 학습 목표(제너레이터/
  데코레이터/JSONL/원자적 쓰기)에 집중하기 위해 이번 범위에서 제외한다.
