-- migrate:up
-- タグIDカラムの追加
ALTER TABLE products 
ADD COLUMN tag_id uuid;

ALTER TABLE products
ADD CONSTRAINT fk_products_tag
FOREIGN KEY (tag_id)
REFERENCES tags(id);

UPDATE products
SET tag_id = '11111111-1111-1111-1111-111111111111'
WHERE id = 'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1';

UPDATE products
SET tag_id = '22222222-2222-2222-2222-222222222222'
WHERE id = 'aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2';

UPDATE products
SET tag_id = '33333333-3333-3333-3333-333333333333'
WHERE id = 'bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbb1';

UPDATE products
SET tag_id = '44444444-4444-4444-4444-444444444444'
WHERE id = 'bbbbbbb2-bbbb-bbbb-bbbb-bbbbbbbbbbb2';

UPDATE products
SET tag_id = '55555555-5555-5555-5555-555555555555'
WHERE id = 'ccccccc1-cccc-cccc-cccc-ccccccccccc1';

UPDATE products
SET tag_id = '66666666-6666-6666-6666-666666666666'
WHERE id = 'ccccccc2-cccc-cccc-cccc-ccccccccccc2';

-- migrate:down
ALTER TABLE products
DROP CONSTRAINT IF EXISTS fk_products_tag;
ALTER TABLE products
DROP COLUMN IF EXISTS tag_id;
