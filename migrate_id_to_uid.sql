-- Migration to rename 'id' column to 'uid' for all tables
-- This script will rename the primary key columns from 'id' to 'uid'

BEGIN;

-- 1. News Articles
-- First, drop the primary key constraint
ALTER TABLE news_articles DROP CONSTRAINT IF EXISTS news_articles_pkey;

-- Rename the column
ALTER TABLE news_articles RENAME COLUMN id TO uid;

-- Recreate the primary key constraint
ALTER TABLE news_articles ADD PRIMARY KEY (uid);

-- 2. Events
-- First, drop the primary key constraint
ALTER TABLE events DROP CONSTRAINT IF EXISTS events_pkey;

-- Rename the column
ALTER TABLE events RENAME COLUMN id TO uid;

-- Recreate the primary key constraint
ALTER TABLE events ADD PRIMARY KEY (uid);

-- 3. Projects
-- First, drop the primary key constraint
ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_pkey;

-- Rename the column
ALTER TABLE projects RENAME COLUMN id TO uid;

-- Recreate the primary key constraint
ALTER TABLE projects ADD PRIMARY KEY (uid);

-- Update foreign key references in project_images
ALTER TABLE project_images RENAME COLUMN project_id TO project_uid;

-- Update the foreign key constraint
ALTER TABLE project_images DROP CONSTRAINT IF EXISTS project_images_project_id_fkey;
ALTER TABLE project_images ADD CONSTRAINT project_images_project_uid_fkey 
    FOREIGN KEY (project_uid) REFERENCES projects(uid);

-- 4. Project Images
-- First, drop the primary key constraint
ALTER TABLE project_images DROP CONSTRAINT IF EXISTS project_images_pkey;

-- Rename the column
ALTER TABLE project_images RENAME COLUMN id TO uid;

-- Recreate the primary key constraint
ALTER TABLE project_images ADD PRIMARY KEY (uid);

-- 5. Blog Posts (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blog_posts') THEN
        -- Drop the primary key constraint
        ALTER TABLE blog_posts DROP CONSTRAINT IF EXISTS blog_posts_pkey;
        
        -- Rename the column
        ALTER TABLE blog_posts RENAME COLUMN id TO uid;
        
        -- Recreate the primary key constraint
        ALTER TABLE blog_posts ADD PRIMARY KEY (uid);
    END IF;
END $$;

-- Update indexes
DROP INDEX IF EXISTS ix_news_articles_id;
DROP INDEX IF EXISTS ix_events_id;
DROP INDEX IF EXISTS ix_projects_id;
DROP INDEX IF EXISTS ix_project_images_id;
DROP INDEX IF EXISTS ix_blog_posts_id;

CREATE INDEX IF NOT EXISTS ix_news_articles_uid ON news_articles (uid);
CREATE INDEX IF NOT EXISTS ix_events_uid ON events (uid);
CREATE INDEX IF NOT EXISTS ix_projects_uid ON projects (uid);
CREATE INDEX IF NOT EXISTS ix_project_images_uid ON project_images (uid);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blog_posts') THEN
        CREATE INDEX IF NOT EXISTS ix_blog_posts_uid ON blog_posts (uid);
    END IF;
END $$;

COMMIT;
