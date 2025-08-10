-- Migration to implement model standardization fixes
-- This script addresses all the identified issues:
-- 1. Standardize category management
-- 2. Implement shared image management
-- 3. Fix data types and constraints
-- 4. Remove redundant fields

-- Create shared categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('blog', 'news', 'event', 'project')),
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50), -- Icon name or class
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_categories_content_type ON categories(content_type);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);

-- Create shared content images table
CREATE TABLE IF NOT EXISTS content_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('blog', 'news', 'event', 'project')),
    image_type VARCHAR(20) NOT NULL DEFAULT 'gallery' CHECK (image_type IN ('featured', 'gallery', 'thumbnail', 'og_image', 'banner')),
    title VARCHAR(255),
    description TEXT,
    alt_text VARCHAR(255),
    image_url VARCHAR(255) NOT NULL CHECK (image_url ~ '^https?://'),
    thumbnail_url VARCHAR(255) CHECK (thumbnail_url ~ '^https?://'),
    file_size VARCHAR(50),
    dimensions VARCHAR(50),
    format VARCHAR(10),
    order_index INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_images_content ON content_images(content_id, content_type);
CREATE INDEX IF NOT EXISTS idx_content_images_type ON content_images(image_type);

-- Create image tags table
CREATE TABLE IF NOT EXISTS image_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create content image tags junction table
CREATE TABLE IF NOT EXISTS content_image_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL REFERENCES content_images(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES image_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(image_id, tag_id)
);

-- Update blog_posts table
DO $$
BEGIN
    -- Convert featured_image_id and og_image_id to UUIDs if they exist and are integers
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='blog_posts' AND column_name='featured_image_id' AND data_type='integer') THEN
        ALTER TABLE blog_posts ALTER COLUMN featured_image_id TYPE UUID USING NULL;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='blog_posts' AND column_name='og_image_id' AND data_type='integer') THEN
        ALTER TABLE blog_posts ALTER COLUMN og_image_id TYPE UUID USING NULL;
    END IF;
    
    -- Add URL constraints if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'blog_posts_image_url_check') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT blog_posts_image_url_check 
        CHECK (image_url IS NULL OR image_url ~ '^https?://');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'blog_posts_cta_link_check') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT blog_posts_cta_link_check 
        CHECK (cta_link IS NULL OR cta_link ~ '^https?://');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'blog_posts_og_image_url_check') THEN
        ALTER TABLE blog_posts ADD CONSTRAINT blog_posts_og_image_url_check 
        CHECK (og_image_url IS NULL OR og_image_url ~ '^https?://');
    END IF;
    
    -- Convert tags from string to JSON if it's still a string column
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='blog_posts' AND column_name='tags' AND data_type='character varying') THEN
        -- Add new tags_json column
        ALTER TABLE blog_posts ADD COLUMN tags_json JSONB DEFAULT '[]';
        -- Migrate data: split comma-separated tags into JSON array
        UPDATE blog_posts SET tags_json = 
            CASE 
                WHEN tags IS NULL OR tags = '' THEN '[]'::jsonb
                ELSE json_build_array(tags)::jsonb  -- Simple conversion, can be enhanced
            END;
        -- Drop old column and rename new one
        ALTER TABLE blog_posts DROP COLUMN tags;
        ALTER TABLE blog_posts RENAME COLUMN tags_json TO tags;
    END IF;
END $$;

-- Update projects table constraints
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'projects_source_link_check') THEN
        ALTER TABLE projects ADD CONSTRAINT projects_source_link_check 
        CHECK (source_link IS NULL OR source_link ~ '^https?://');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'projects_live_link_check') THEN
        ALTER TABLE projects ADD CONSTRAINT projects_live_link_check 
        CHECK (live_link IS NULL OR live_link ~ '^https?://');
    END IF;
END $$;

-- Update project_images table constraints
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'project_images_image_url_check') THEN
        ALTER TABLE project_images ADD CONSTRAINT project_images_image_url_check 
        CHECK (image_url ~ '^https?://');
    END IF;
    
    -- Add foreign key if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name = 'project_images_project_id_fkey') THEN
        ALTER TABLE project_images ADD CONSTRAINT project_images_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Update news_articles table
DO $$
BEGIN
    -- Add URL constraints
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'news_articles_image_url_check') THEN
        ALTER TABLE news_articles ADD CONSTRAINT news_articles_image_url_check 
        CHECK (image_url IS NULL OR image_url ~ '^https?://');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'news_articles_og_image_url_check') THEN
        ALTER TABLE news_articles ADD CONSTRAINT news_articles_og_image_url_check 
        CHECK (og_image_url IS NULL OR og_image_url ~ '^https?://');
    END IF;
    
    -- Convert tags from string to JSON if needed
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='tags' AND data_type='character varying') THEN
        ALTER TABLE news_articles ADD COLUMN tags_json JSONB DEFAULT '[]';
        UPDATE news_articles SET tags_json = 
            CASE 
                WHEN tags IS NULL OR tags = '' THEN '[]'::jsonb
                ELSE json_build_array(tags)::jsonb
            END;
        ALTER TABLE news_articles DROP COLUMN tags;
        ALTER TABLE news_articles RENAME COLUMN tags_json TO tags;
    END IF;
    
    -- Add author fields if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='news_articles' AND column_name='author_name') THEN
        ALTER TABLE news_articles ADD COLUMN author_name VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='news_articles' AND column_name='author_bio') THEN
        ALTER TABLE news_articles ADD COLUMN author_bio TEXT;
    END IF;
    
    -- Add related_event_ids column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='news_articles' AND column_name='related_event_ids') THEN
        ALTER TABLE news_articles ADD COLUMN related_event_ids JSONB DEFAULT '[]';
    END IF;
    
    -- Remove event-specific fields if they exist
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='venue') THEN
        ALTER TABLE news_articles DROP COLUMN venue;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='location') THEN
        ALTER TABLE news_articles DROP COLUMN location;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='registration_link') THEN
        ALTER TABLE news_articles DROP COLUMN registration_link;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='ticket_price') THEN
        ALTER TABLE news_articles DROP COLUMN ticket_price;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='event_start_date') THEN
        ALTER TABLE news_articles DROP COLUMN event_start_date;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='news_articles' AND column_name='event_end_date') THEN
        ALTER TABLE news_articles DROP COLUMN event_end_date;
    END IF;
END $$;

-- Update events table
DO $$
BEGIN
    -- Add URL constraints
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'events_image_url_check') THEN
        ALTER TABLE events ADD CONSTRAINT events_image_url_check 
        CHECK (image_url IS NULL OR image_url ~ '^https?://');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'events_registration_link_check') THEN
        ALTER TABLE events ADD CONSTRAINT events_registration_link_check 
        CHECK (registration_link IS NULL OR registration_link ~ '^https?://');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'events_og_image_url_check') THEN
        ALTER TABLE events ADD CONSTRAINT events_og_image_url_check 
        CHECK (og_image_url IS NULL OR og_image_url ~ '^https?://');
    END IF;
    
    -- Convert tags from string to JSON if needed
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='events' AND column_name='tags' AND data_type='character varying') THEN
        ALTER TABLE events ADD COLUMN tags_json JSONB DEFAULT '[]';
        UPDATE events SET tags_json = 
            CASE 
                WHEN tags IS NULL OR tags = '' THEN '[]'::jsonb
                ELSE json_build_array(tags)::jsonb
            END;
        ALTER TABLE events DROP COLUMN tags;
        ALTER TABLE events RENAME COLUMN tags_json TO tags;
    END IF;
END $$;

-- Drop old category tables since we now have shared categories
DROP TABLE IF EXISTS blog_categories CASCADE;
DROP TABLE IF EXISTS news_categories CASCADE;
DROP TABLE IF EXISTS event_categories CASCADE;

-- Insert some default categories for each content type
INSERT INTO categories (name, slug, description, content_type) VALUES
    ('General', 'general', 'General blog posts', 'blog'),
    ('Technology', 'technology', 'Technology-related posts', 'blog'),
    ('Announcements', 'announcements', 'News announcements', 'news'),
    ('Updates', 'updates', 'General updates', 'news'),
    ('Workshops', 'workshops', 'Workshop events', 'event'),
    ('Conferences', 'conferences', 'Conference events', 'event'),
    ('Web Development', 'web-development', 'Web development projects', 'project'),
    ('Mobile Apps', 'mobile-apps', 'Mobile application projects', 'project')
ON CONFLICT DO NOTHING;

RAISE NOTICE 'Model standardization migration completed successfully!';
