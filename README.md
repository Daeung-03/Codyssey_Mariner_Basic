# Q5 - SQL로 만드는 온라인 쇼핑 데이터베이스 (PostgreSQL, CLI)

`Problem.md`의 요구사항을 기준으로 온라인 쇼핑 도메인 DB를 설계/구현한 결과물입니다.  
백엔드 프레임워크 없이 PostgreSQL + `psql` CLI로만 실행합니다.

## 1) 과제 결과물 구성

- `schema.sql` : 스키마 생성 스크립트 (PK/FK/제약조건 포함)
- `seed.sql` : 샘플 데이터 입력 스크립트
- `queries.sql` : 핵심 SQL 15개 (설명 주석 포함)
- `results/` : 실행 결과 텍스트
  - `01_schema_output.txt`
  - `02_seed_output.txt`
  - `03_queries_output.txt`
  - `04_row_counts.txt`
- `shopping.sql` : `schema.sql`과 동일한 최종 스키마 파일

## 2) 환경

- DBMS: PostgreSQL 14+
- 실행 도구: `psql` CLI

## 3) 실행 방법 (CLI)

```bash
# 1. DB 생성 (최초 1회)
createdb q5_shopping

# 2. 스키마 생성
psql -v ON_ERROR_STOP=1 -d q5_shopping -f schema.sql

# 3. 샘플 데이터 입력
psql -v ON_ERROR_STOP=1 -d q5_shopping -f seed.sql

# 4. 핵심 쿼리 실행
psql -v ON_ERROR_STOP=1 -d q5_shopping -f queries.sql
```

결과를 파일로 저장하려면:

```bash
mkdir -p results
psql -v ON_ERROR_STOP=1 -d q5_shopping -f schema.sql  > results/01_schema_output.txt
psql -v ON_ERROR_STOP=1 -d q5_shopping -f seed.sql    > results/02_seed_output.txt
psql -v ON_ERROR_STOP=1 -d q5_shopping -f queries.sql > results/03_queries_output.txt
```

## 4) 데이터 모델 요약

### 테이블

1. `users`
2. `products`
3. `carts`
4. `cart_items`
5. `orders`
6. `order_items`
7. `payments`

### 관계 (1:N 중심)

- `users (1) -> (N) orders`
- `orders (1) -> (N) order_items`
- `products (1) -> (N) order_items`
- `carts (1) -> (N) cart_items`
- `products (1) -> (N) cart_items`
- `orders (1) -> (1) payments` (`payments.order_id UNIQUE`)

## 5) 요구사항 충족 체크

### 스키마/제약조건

- 최소 4개 테이블: **충족 (7개)**
- PK: **전 테이블 적용**
- FK 2개 이상: **충족**
- NOT NULL 1개 이상: **충족**
- UNIQUE 1개 이상: **충족** (`users.email`, `products.sku`, `orders.order_number` 등)
- FK 무결성: **충족** (부모 없는 참조 불가)
- 컬럼 타입 적절성: **충족** (`VARCHAR`, `INTEGER`, `TIMESTAMP` 등)

### 샘플 데이터

- 각 테이블 10행 이상: **충족**
- 부모 → 자식 순서로 입력: **충족**
- FK로 실제 연결된 데이터: **충족**

### 핵심 쿼리 15개

- 기본 조회 4개 이상: **Q1~Q4**
- 조인 4개 이상: **Q5~Q8** (INNER 2개 이상 + LEFT 1개 이상 포함)
- 집계 3개 이상: **Q9~Q11** (COUNT, SUM, AVG + GROUP BY)
- 서브쿼리 1개 이상: **Q12**
- 수정/삭제 2개 이상: **Q14(UPDATE), Q15(DELETE)**
- 인덱스 1개 이상 + 이유: **Q13** (`idx_orders_order_number`, 주문번호 조회 성능 목적)

## 6) 참고 사항

- PostgreSQL 기준으로 작성되었습니다.
- `updated_at`은 트리거 없이 관리하도록 설계했기 때문에, 데이터 수정 시 `updated_at = CURRENT_TIMESTAMP`를 함께 갱신합니다.
- 과제 제약에 맞춰 View/Procedure/Trigger는 사용하지 않았습니다.
- Diagram: https://www.erdcloud.com/d/nPowgd5cfKcpjoBwB