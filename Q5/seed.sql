INSERT INTO users (email, password_hash, name, phone, address, status)
VALUES
    ('user1@example.com', 'hash_001', 'Kim Min', '010-1000-0001', 'Seoul Mapo-gu 1', 'active'),
    ('user2@example.com', 'hash_002', 'Lee Joon', '010-1000-0002', 'Seoul Songpa-gu 2', 'active'),
    ('user3@example.com', 'hash_003', 'Park Su', '010-1000-0003', 'Busan Haeundae-gu 3', 'active'),
    ('user4@example.com', 'hash_004', 'Choi Ji', '010-1000-0004', 'Incheon Namdong-gu 4', 'active'),
    ('user5@example.com', 'hash_005', 'Jung Won', '010-1000-0005', 'Daegu Suseong-gu 5', 'active'),
    ('user6@example.com', 'hash_006', 'Han Seo', '010-1000-0006', 'Daejeon Yuseong-gu 6', 'active'),
    ('user7@example.com', 'hash_007', 'Yoon Hye', '010-1000-0007', 'Gwangju Buk-gu 7', 'active'),
    ('user8@example.com', 'hash_008', 'Kang Do', '010-1000-0008', 'Ulsan Nam-gu 8', 'active'),
    ('user9@example.com', 'hash_009', 'Shin Ah', '010-1000-0009', 'Sejong Hansol-dong 9', 'active'),
    ('user10@example.com', 'hash_010', 'Oh Rin', '010-1000-0010', 'Jeju Jeju-si 10', 'inactive');

INSERT INTO products (product_name, sku, price, stock_quantity, status)
VALUES
    ('Wireless Mouse', 'SKU-001', 25000, 120, 'active'),
    ('Mechanical Keyboard', 'SKU-002', 89000, 80, 'active'),
    ('USB-C Cable', 'SKU-003', 9000, 300, 'active'),
    ('Laptop Stand', 'SKU-004', 32000, 70, 'active'),
    ('Monitor 27inch', 'SKU-005', 249000, 35, 'active'),
    ('Bluetooth Speaker', 'SKU-006', 56000, 90, 'active'),
    ('Webcam FHD', 'SKU-007', 74000, 60, 'active'),
    ('External SSD 1TB', 'SKU-008', 159000, 40, 'active'),
    ('Desk Lamp', 'SKU-009', 28000, 110, 'active'),
    ('Ergonomic Chair', 'SKU-010', 299000, 20, 'active');

INSERT INTO carts (user_id)
VALUES
    (1), (2), (3), (4), (5), (6), (7), (8), (9), (10);

INSERT INTO cart_items (cart_id, product_id, quantity, unit_price)
VALUES
    (1, 1, 1, 25000),
    (1, 3, 2, 9000),
    (2, 2, 1, 89000),
    (3, 4, 1, 32000),
    (4, 5, 1, 249000),
    (5, 6, 1, 56000),
    (6, 7, 1, 74000),
    (7, 8, 1, 159000),
    (8, 9, 2, 28000),
    (9, 10, 1, 299000),
    (10, 3, 3, 9000),
    (10, 1, 1, 25000);

INSERT INTO orders (user_id, order_number, order_status, shipping_address, shipping_request, total_price, ordered_at)
VALUES
    (1, 'ORD-20260518-0001', 'paid', 'Seoul Mapo-gu 1', 'Leave at door', 43000, CURRENT_TIMESTAMP - INTERVAL '10 days'),
    (2, 'ORD-20260518-0002', 'paid', 'Seoul Songpa-gu 2', NULL, 89000, CURRENT_TIMESTAMP - INTERVAL '9 days'),
    (3, 'ORD-20260518-0003', 'shipping', 'Busan Haeundae-gu 3', 'Call on arrival', 32000, CURRENT_TIMESTAMP - INTERVAL '8 days'),
    (4, 'ORD-20260518-0004', 'paid', 'Incheon Namdong-gu 4', NULL, 249000, CURRENT_TIMESTAMP - INTERVAL '7 days'),
    (5, 'ORD-20260518-0005', 'pending', 'Daegu Suseong-gu 5', NULL, 56000, CURRENT_TIMESTAMP - INTERVAL '6 days'),
    (6, 'ORD-20260518-0006', 'paid', 'Daejeon Yuseong-gu 6', NULL, 74000, CURRENT_TIMESTAMP - INTERVAL '5 days'),
    (7, 'ORD-20260518-0007', 'cancelled', 'Gwangju Buk-gu 7', 'Weekend delivery', 159000, CURRENT_TIMESTAMP - INTERVAL '4 days'),
    (8, 'ORD-20260518-0008', 'paid', 'Ulsan Nam-gu 8', NULL, 56000, CURRENT_TIMESTAMP - INTERVAL '3 days'),
    (9, 'ORD-20260518-0009', 'paid', 'Sejong Hansol-dong 9', 'No call', 299000, CURRENT_TIMESTAMP - INTERVAL '2 days'),
    (10, 'ORD-20260518-0010', 'pending', 'Jeju Jeju-si 10', NULL, 27000, CURRENT_TIMESTAMP - INTERVAL '1 days');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, item_total_price)
VALUES
    (1, 1, 1, 25000, 25000),
    (1, 3, 2, 9000, 18000),
    (2, 2, 1, 89000, 89000),
    (3, 4, 1, 32000, 32000),
    (4, 5, 1, 249000, 249000),
    (5, 6, 1, 56000, 56000),
    (6, 7, 1, 74000, 74000),
    (7, 8, 1, 159000, 159000),
    (8, 9, 2, 28000, 56000),
    (9, 10, 1, 299000, 299000),
    (10, 3, 3, 9000, 27000),
    (10, 1, 1, 25000, 25000);

INSERT INTO payments (order_id, payment_method, payment_status, amount, paid_at, cancelled_at)
VALUES
    (1, 'card', 'paid', 43000, CURRENT_TIMESTAMP - INTERVAL '10 days', NULL),
    (2, 'card', 'paid', 89000, CURRENT_TIMESTAMP - INTERVAL '9 days', NULL),
    (3, 'bank_transfer', 'paid', 32000, CURRENT_TIMESTAMP - INTERVAL '8 days', NULL),
    (4, 'card', 'paid', 249000, CURRENT_TIMESTAMP - INTERVAL '7 days', NULL),
    (5, 'kakao_pay', 'pending', 56000, NULL, NULL),
    (6, 'card', 'paid', 74000, CURRENT_TIMESTAMP - INTERVAL '5 days', NULL),
    (7, 'card', 'cancelled', 159000, NULL, CURRENT_TIMESTAMP - INTERVAL '3 days'),
    (8, 'card', 'paid', 56000, CURRENT_TIMESTAMP - INTERVAL '3 days', NULL),
    (9, 'bank_transfer', 'paid', 299000, CURRENT_TIMESTAMP - INTERVAL '2 days', NULL),
    (10, 'card', 'pending', 27000, NULL, NULL);
