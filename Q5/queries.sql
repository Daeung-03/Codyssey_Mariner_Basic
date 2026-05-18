-- Q1. 상태가 active인 사용자 최신 가입순 5명 조회 (WHERE + ORDER BY + LIMIT)
SELECT user_id, email, name, created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 5;

-- Q2. 재고가 50개 이상인 상품을 가격 높은 순으로 조회 (WHERE + ORDER BY)
SELECT product_id, product_name, price, stock_quantity
FROM products
WHERE stock_quantity >= 50
ORDER BY price DESC;

-- Q3. 최근 7일 내 주문 조회 (WHERE + ORDER BY)
SELECT order_id, order_number, order_status, ordered_at
FROM orders
WHERE ordered_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY ordered_at DESC;

-- Q4. 결제 대기 상태의 결제 건 조회 (WHERE + ORDER BY)
SELECT payment_id, order_id, payment_method, payment_status, amount
FROM payments
WHERE payment_status = 'pending'
ORDER BY payment_id;

-- Q5. 주문과 사용자 정보를 함께 조회 (INNER JOIN)
SELECT o.order_id, o.order_number, u.name AS user_name, o.total_price, o.order_status
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id
ORDER BY o.order_id;

-- Q6. 주문 상세에서 상품명과 수량/금액 조회 (INNER JOIN)
SELECT oi.order_item_id, oi.order_id, p.product_name, oi.quantity, oi.item_total_price
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.product_id
ORDER BY oi.order_id, oi.order_item_id;

-- Q7. 사용자별 주문 목록 조회, 주문이 없는 사용자도 포함 (LEFT JOIN)
SELECT u.user_id, u.name, o.order_id, o.order_status
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
ORDER BY u.user_id, o.order_id;

-- Q8. 장바구니별 상품 내역 조회 (INNER JOIN 3개)
SELECT c.cart_id, u.name AS user_name, p.product_name, ci.quantity, ci.unit_price
FROM cart_items ci
INNER JOIN carts c ON ci.cart_id = c.cart_id
INNER JOIN users u ON c.user_id = u.user_id
INNER JOIN products p ON ci.product_id = p.product_id
ORDER BY c.cart_id, ci.cart_item_id;

-- Q9. 사용자별 주문 건수 집계 (COUNT + GROUP BY)
SELECT u.user_id, u.name, COUNT(o.order_id) AS order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.name
ORDER BY order_count DESC, u.user_id;

-- Q10. 상품별 판매 총수량 집계 (SUM + GROUP BY)
SELECT p.product_id, p.product_name, COALESCE(SUM(oi.quantity), 0) AS sold_quantity
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
ORDER BY sold_quantity DESC, p.product_id;

-- Q11. 사용자별 평균 주문금액 집계 (AVG + GROUP BY)
SELECT u.user_id, u.name, ROUND(AVG(o.total_price), 2) AS avg_order_price
FROM users u
JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.name
ORDER BY avg_order_price DESC;

-- Q12. 전체 평균 주문금액보다 큰 주문 조회 (서브쿼리)
SELECT order_id, order_number, total_price
FROM orders
WHERE total_price > (SELECT AVG(total_price) FROM orders)
ORDER BY total_price DESC;

-- Q13. 주문번호로 탐색 성능 향상을 위한 인덱스 생성 (이유: 주문 단건 조회/정렬 빈도 높음)
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders (order_number);

-- Q14. 결제 완료된 주문 상태를 paid로 동기화 (UPDATE)
UPDATE orders
SET order_status = 'paid',
    updated_at = CURRENT_TIMESTAMP
WHERE order_id IN (
    SELECT order_id
    FROM payments
    WHERE payment_status = 'paid'
);

-- Q15. 수량이 1개이고 오래된 장바구니 항목 1건 삭제 (DELETE)
DELETE FROM cart_items
WHERE cart_item_id = (
    SELECT cart_item_id
    FROM cart_items
    WHERE quantity = 1
    ORDER BY created_at ASC
    LIMIT 1
);
