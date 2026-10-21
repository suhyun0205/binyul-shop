-- 소소기프트 판촉물 카테고리에 맞는 상품으로 전면 교체
-- Supabase 대시보드 > SQL Editor에서 실행하세요.

delete from cart_items;
delete from products;

insert into products (slug, name, category, image_url, badge, old_price, price, discount_rate, rating, review_count, wish_count, tags, detail_url) values
('notebook-spiral', '스프링 무지노트', 'office', 'images/products/office-notebook.jpg', '신상제품', 3000, 2400, 20, 0, 0, 0, '#문구 #단체선물', null),
('pouch-pattern', '패턴 지퍼 파우치', 'office', 'images/products/office-pencilcase.jpg', null, 8000, 6400, 20, 0, 0, 0, '#문구 #파우치', null),
('tumbler-clear', '클리어 보냉 텀블러', 'tumbler', 'images/products/tumbler-1.png', '신상제품', 12000, 9600, 20, 0, 0, 0, '#텀블러 #단체구매', null),
('ecobag-canvas', '투톤 캔버스 토트백', 'bag', 'images/products/bag-1.jpg', '신상제품', 9000, 7200, 20, 0, 0, 0, '#에코백 #친환경', null),
('bag-foldable', '접이식 장바구니', 'bag', 'images/products/bag-2.jpg', null, 7000, 5600, 20, 0, 0, 0, '#가방 #휴대용', null),
('umbrella-auto2', '2단 자동 우산', 'umbrella', 'images/products/umbrella-1.jpg', null, 18000, 14400, 20, 0, 0, 0, '#우산 #단체선물', null),
('umbrella-mini3', '미니 3단 우산', 'umbrella', 'images/products/umbrella-2.jpg', null, 14000, 11200, 20, 0, 0, 0, '#우산 #휴대용', null),
('polo-shirt-team', '단체 카라 티셔츠', 'apparel', 'images/products/apparel-2.jpg', '신상제품', 16000, 12800, 20, 0, 0, 0, '#단체복 #티셔츠', null),
('cap-ball', '볼캡 모자', 'cap', 'images/products/cap-1.png', null, 11000, 8800, 20, 0, 0, 0, '#모자 #단체선물', null),
('usb-32gb', 'USB 메모리 32GB', 'electronics', 'images/products/electronics-2.jpg', null, 13000, 10400, 20, 0, 0, 0, '#USB #사무용품', null),
('cuttingboard-wood', '원목 도마', 'kitchen', 'images/products/kitchen-1.jpg', null, 10000, 8000, 20, 0, 0, 0, '#주방 #원목', null),
('handsanitizer-mini', '휴대용 손소독제', 'health', 'images/products/health-1.jpg', '신상제품', 4000, 3200, 20, 0, 0, 0, '#위생 #휴대용', null),
('giftbox-ribbon', '리본 선물포장 세트', 'season', 'images/products/season-1.jpg', null, 6000, 4800, 20, 0, 0, 0, '#선물포장 #기획상품', null);
