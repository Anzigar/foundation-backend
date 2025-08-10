-- Migration to remove category_id column from blog_posts table
-- Run this to update existing database schema

-- Remove category_id column from blog_posts table if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT column_name 
               FROM information_schema.columns 
               WHERE table_name='blog_posts' AND column_name='category_id') THEN
        ALTER TABLE blog_posts DROP COLUMN category_id;
        RAISE NOTICE 'category_id column removed from blog_posts table';
    ELSE
        RAISE NOTICE 'category_id column does not exist in blog_posts table';
    END IF;
END $$;

-- Ensure category_ids JSON column exists (for managing categories as an array)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT column_name 
                   FROM information_schema.columns 
                   WHERE table_name='blog_posts' AND column_name='category_ids') THEN
        ALTER TABLE blog_posts ADD COLUMN category_ids JSONB DEFAULT '[]';
        RAISE NOTICE 'category_ids JSONB column added to blog_posts table';
    ELSE
        RAISE NOTICE 'category_ids column already exists in blog_posts table';
    END IF;
END $$;
