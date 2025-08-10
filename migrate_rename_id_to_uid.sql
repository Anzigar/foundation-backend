-- Migration to rename 'id' column to 'uid' in all tables
-- This script will rename the primary key columns from 'id' to 'uid'

BEGIN;

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. News Articles Table
ALTER TABLE news_articles RENAME COLUMN id TO uid;

-- 2. Events Table  
ALTER TABLE events RENAME COLUMN id TO uid;

-- 3. Projects Table
ALTER TABLE projects RENAME COLUMN id TO uid;

-- 4. Blog Posts Table
ALTER TABLE blog_posts RENAME COLUMN id TO uid;

-- 5. Update any foreign key references (if they exist)
-- Note: You may need to update other tables that reference these IDs

-- 6. Update any indexes that reference the old column name
-- Note: PostgreSQL automatically updates index names when columns are renamed

COMMIT;

-- Verify the changes
\d news_articles;
\d events;
\d projects;
\d blog_posts;
