-- migrate:up
-- タグテーブルの作成
CREATE TABLE tags (
    id uuid PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
    name character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone DEFAULT 'infinity'
);
INSERT INTO tags (id, name)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'ウェイトケア'),
  ('22222222-2222-2222-2222-222222222222', '美食・食欲ケア'),
  ('33333333-3333-3333-3333-333333333333', '皮膚・被毛ケア'),
  ('44444444-4444-4444-4444-444444444444', '尿路ケア'),
  ('55555555-5555-5555-5555-555555555555', '消化器ケア'),
  ('66666666-6666-6666-6666-666666666666', '関節ケア');

-- migrate:down
DROP TABLE IF EXISTS tags;
