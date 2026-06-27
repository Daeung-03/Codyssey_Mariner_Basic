# 파일 기반 가계부 콘솔 프로그램 (budget_app)

학습용 과제(Q2) — 제너레이터 스트리밍, 데코레이터 분리, JSONL 영구 저장, 타입 힌트를 적용한
4계층(CLI/Service/Repository/Model) 구조의 콘솔 가계부. 설계 배경은
`../docs/superpowers/specs/2026-06-23-budget-app-architecture-design.md` 참고.

## 실행 방법

```bash
cd Q2
python3 -m budget_app --help
python3 -m budget_app add
python3 -m budget_app list --limit 10
python3 -m budget_app summary --month 2024-01 --top 3
```

기본 데이터 폴더는 `./data`이며 `--data-dir <경로>`로 변경할 수 있습니다.

## 저장 파일 위치/형식

- `data/transactions.jsonl`, `data/categories.jsonl`, `data/budgets.jsonl` — 한 줄에 JSON 객체 하나(JSONL)
- `logs/app.log` — 데코레이터가 기록하는 실행 로그(호출 인자, 소요 시간, 예외 스택트레이스)

## 주요 명령 예시

```bash
python3 -m budget_app add
python3 -m budget_app list --limit 5
python3 -m budget_app search --category food --from 2024-01-01 --to 2024-01-31
python3 -m budget_app update --id TX-000001 --amount 20000
python3 -m budget_app delete --id TX-000001
python3 -m budget_app category add
python3 -m budget_app category remove --name food --reassign-to etc
python3 -m budget_app budget set --month 2024-01 --amount 500000
python3 -m budget_app import --from import.csv
python3 -m budget_app export --out export.csv --month 2024-01
```

## import/export CSV 스키마

| column | required | 설명 |
| --- | --- | --- |
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

공통: UTF-8, 헤더 포함. `import`는 행 단위로 검증하며 유효하지 않은 행은 건너뛰고 계속 진행합니다
(`imported`/`skipped` 건수를 출력). `export`는 `--month` 또는 `--from`/`--to` 중 최소 하나가 필요합니다.
