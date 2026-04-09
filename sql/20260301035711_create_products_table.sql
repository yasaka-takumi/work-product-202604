-- migrate:up
CREATE TABLE product_categories (
    id uuid PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
    name character varying NOT NULL,
    created_at timestamp NOT NULL DEFAULT current_timestamp,
    updated_at timestamp NOT NULL DEFAULT current_timestamp,
    deleted_at timestamp
);

CREATE TABLE products (
    id uuid PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
    category_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    price integer NOT NULL,
    image_url character varying(500),
    ingredients text NOT NULL,
    created_at timestamp NOT NULL DEFAULT current_timestamp,
    updated_at timestamp NOT NULL DEFAULT current_timestamp,
    deleted_at timestamp,
    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id)
        REFERENCES product_categories(id)
);

INSERT INTO product_categories (id, name)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'フード'),
  ('22222222-2222-2222-2222-222222222222', 'おもちゃ'),
  ('33333333-3333-3333-3333-333333333333', 'ケア用品');

INSERT INTO products (id, category_id, name, description, price, image_url, ingredients)
VALUES
  (
    'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
    '11111111-1111-1111-1111-111111111111',
    'Premium Dog Food',
    'Nutritious dry food for adult dogs.',
    2480,
    '/images/150x150.jpg',
    'chicken meal, rice, vitamins, minerals'
  ),
  (
    'aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
    '11111111-1111-1111-1111-111111111111',
    'Cat Wet Food',
    'Soft texture wet food for cats.',
    320,
    '/images/160x160.jpg',
    'tuna, broth, taurine'
  ),
  (
    'bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbb1',
    '22222222-2222-2222-2222-222222222222',
    'Rubber Ball',
    'Durable toy ball for active play.',
    780,
    '/images/150x150.jpg',
    'natural rubber'
  ),
  (
    'bbbbbbb2-bbbb-bbbb-bbbb-bbbbbbbbbbb2',
    '22222222-2222-2222-2222-222222222222',
    'Feather Wand',
    'Interactive wand toy for cats.',
    980,
    '/images/160x160.jpg',
    'plastic, feather, steel wire'
  ),
  (
    'ccccccc1-cccc-cccc-cccc-ccccccccccc1',
    '33333333-3333-3333-3333-333333333333',
    'Pet Shampoo',
    'Gentle shampoo for sensitive skin.',
    1280,
    '/images/150x150.jpg',
    'water, mild surfactant, aloe extract'
  ),
  (
    'ccccccc2-cccc-cccc-cccc-ccccccccccc2',
    '33333333-3333-3333-3333-333333333333',
    'Ear Cleaning Wipes',
    'Disposable wipes for routine ear care.',
    890,
    '/images/160x160.jpg',
    'nonwoven fabric, purified water, preservative'
  );

-- migrate:down
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS product_categories;
