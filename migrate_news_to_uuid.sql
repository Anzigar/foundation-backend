-- Migration to change news_articles.id from integer to UUID
-- This script will:
-- 1. Add a new UUID column called 'uid'
-- 2. Populate it with generated UUIDs
-- 3. Update all references
-- 4. Drop the old integer id column
-- 5. Rename uid to id

BEGIN;

-- Step 1: Add UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Step 2: Add new UUID column
ALTER TABLE news_articles ADD COLUMN uid UUID DEFAULT uuid_generate_v4();

-- Step 3: Populate existing rows with UUIDs
UPDATE news_articles SET uid = uuid_generate_v4() WHERE uid IS NULL;

-- Step 4: Make uid NOT NULL
ALTER TABLE news_articles ALTER COLUMN uid SET NOT NULL;

-- Step 5: Drop the old primary key constraint
ALTER TABLE news_articles DROP CONSTRAINT news_articles_pkey;

-- Step 6: Drop the old id column and sequence
DROP SEQUENCE IF EXISTS news_articles_id_seq CASCADE;
ALTER TABLE news_articles DROP COLUMN id;

-- Step 7: Rename uid to id
ALTER TABLE news_articles RENAME COLUMN uid TO id;

-- Step 8: Set new primary key
ALTER TABLE news_articles ADD PRIMARY KEY (id);

-- Step 9: Create index on id
CREATE INDEX IF NOT EXISTS ix_news_articles_id ON news_articles (id);

COMMIT;
