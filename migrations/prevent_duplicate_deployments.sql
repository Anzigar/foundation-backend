-- Migration to prevent duplicate deployments across all content types
-- This script adds deployment tracking and unique constraints

-- Add deployment tracking columns to blog_posts
DO $$
BEGIN
    -- Add deployment tracking columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='blog_posts' AND column_name='published_at') THEN
        ALTER TABLE blog_posts ADD COLUMN published_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='blog_posts' AND column_name='last_published_at') THEN
        ALTER TABLE blog_posts ADD COLUMN last_published_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='blog_posts' AND column_name='deployment_count') THEN
        ALTER TABLE blog_posts ADD COLUMN deployment_count INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='blog_posts' AND column_name='is_deployed') THEN
        ALTER TABLE blog_posts ADD COLUMN is_deployed BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='blog_posts' AND column_name='deployed_at') THEN
        ALTER TABLE blog_posts ADD COLUMN deployed_at TIMESTAMP;
    END IF;
    
    -- Add unique constraint for blog posts
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name='uq_blog_post_title_published') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT uq_blog_post_title_published 
        UNIQUE (title, is_published);
    END IF;
END $$;

-- Add deployment tracking columns to projects
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='projects' AND column_name='is_deployed') THEN
        ALTER TABLE projects ADD COLUMN is_deployed BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='projects' AND column_name='deployed_at') THEN
        ALTER TABLE projects ADD COLUMN deployed_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='projects' AND column_name='deployment_count') THEN
        ALTER TABLE projects ADD COLUMN deployment_count INTEGER DEFAULT 0;
    END IF;
    
    -- Add unique constraint for projects
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name='uq_project_title_deployed') THEN
        ALTER TABLE projects ADD CONSTRAINT uq_project_title_deployed 
        UNIQUE (title, is_deployed);
    END IF;
END $$;

-- Add deployment tracking columns to news_articles
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='news_articles' AND column_name='is_deployed') THEN
        ALTER TABLE news_articles ADD COLUMN is_deployed BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='news_articles' AND column_name='deployed_at') THEN
        ALTER TABLE news_articles ADD COLUMN deployed_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='news_articles' AND column_name='deployment_count') THEN
        ALTER TABLE news_articles ADD COLUMN deployment_count INTEGER DEFAULT 0;
    END IF;
    
    -- Add unique constraint for news articles
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name='uq_news_title_deployed') THEN
        ALTER TABLE news_articles ADD CONSTRAINT uq_news_title_deployed 
        UNIQUE (title, is_deployed);
    END IF;
END $$;

-- Add deployment tracking columns to events
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='events' AND column_name='is_deployed') THEN
        ALTER TABLE events ADD COLUMN is_deployed BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='events' AND column_name='deployed_at') THEN
        ALTER TABLE events ADD COLUMN deployed_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='events' AND column_name='deployment_count') THEN
        ALTER TABLE events ADD COLUMN deployment_count INTEGER DEFAULT 0;
    END IF;
    
    -- Add unique constraints for events
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name='uq_event_title_deployed') THEN
        ALTER TABLE events ADD CONSTRAINT uq_event_title_deployed 
        UNIQUE (title, is_deployed);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name='uq_event_title_date') THEN
        ALTER TABLE events ADD CONSTRAINT uq_event_title_date 
        UNIQUE (title, start_date);
    END IF;
END $$;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_deployment ON blog_posts(is_deployed, deployed_at);
CREATE INDEX IF NOT EXISTS idx_projects_deployment ON projects(is_deployed, deployed_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_deployment ON news_articles(is_deployed, deployed_at);
CREATE INDEX IF NOT EXISTS idx_events_deployment ON events(is_deployed, deployed_at);

-- Create view for all deployed content
CREATE OR REPLACE VIEW deployed_content AS
SELECT 
    'blog' as content_type,
    id,
    title,
    slug,
    is_deployed,
    deployed_at,
    deployment_count,
    created_at,
    updated_at
FROM blog_posts 
WHERE is_deployed = true

UNION ALL

SELECT 
    'project' as content_type,
    id,
    title,
    slug,
    is_deployed,
    deployed_at,
    deployment_count,
    created_at,
    updated_at
FROM projects 
WHERE is_deployed = true

UNION ALL

SELECT 
    'news' as content_type,
    id,
    title,
    slug,
    is_deployed,
    deployed_at,
    deployment_count,
    created_at,
    updated_at
FROM news_articles 
WHERE is_deployed = true

UNION ALL

SELECT 
    'event' as content_type,
    id,
    title,
    slug,
    is_deployed,
    deployed_at,
    deployment_count,
    created_at,
    updated_at
FROM events 
WHERE is_deployed = true

ORDER BY deployed_at DESC;

RAISE NOTICE 'Deployment prevention migration completed successfully!';
RAISE NOTICE 'All content types now have unique deployment constraints.';
RAISE NOTICE 'Use deployment endpoints to deploy/undeploy content safely.';
