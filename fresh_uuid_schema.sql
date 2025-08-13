-- Fresh database schema with UUID primary keys for security
-- Foundation Backend - All tables use uid as UUID primary key

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Events table
CREATE TABLE IF NOT EXISTS events (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    excerpt VARCHAR(500),
    location VARCHAR(255),
    venue_details TEXT,
    start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    end_date TIMESTAMP WITHOUT TIME ZONE,
    event_date TIMESTAMP WITHOUT TIME ZONE,
    image_url VARCHAR(255),
    ticket_price VARCHAR(100),
    registration_link VARCHAR(255),
    contact_info TEXT,
    tags VARCHAR(255),
    published BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    allow_comments BOOLEAN DEFAULT TRUE,
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    author_name VARCHAR(100),
    category_ids JSONB DEFAULT '[]'::jsonb,
    related_events JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Blog posts table
CREATE TABLE IF NOT EXISTS blog_posts (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    excerpt VARCHAR(500),
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    author_name VARCHAR(100),
    image_url VARCHAR(255),
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    tags VARCHAR(255),
    category_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- News articles table
CREATE TABLE IF NOT EXISTS news_articles (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    excerpt VARCHAR(500),
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    author_name VARCHAR(100),
    image_url VARCHAR(255),
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    tags VARCHAR(255),
    category_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    excerpt VARCHAR(500),
    content TEXT,
    status VARCHAR(50) DEFAULT 'active',
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    image_url VARCHAR(255),
    github_url VARCHAR(255),
    demo_url VARCHAR(255),
    technologies JSONB DEFAULT '[]'::jsonb,
    category_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    phone VARCHAR(50),
    organization VARCHAR(255),
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Categories table (shared across all content types)
CREATE TABLE IF NOT EXISTS categories (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL, -- 'event', 'blog', 'news', 'project'
    color VARCHAR(7), -- Hex color code
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Event registrations table
CREATE TABLE IF NOT EXISTS event_registrations (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_uid UUID REFERENCES events(uid) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Comments table (for blogs and news)
CREATE TABLE IF NOT EXISTS comments (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_uid UUID NOT NULL, -- References blog_posts.uid or news_articles.uid
    content_type VARCHAR(50) NOT NULL, -- 'blog' or 'news'
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    parent_uid UUID REFERENCES comments(uid) ON DELETE CASCADE,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_slug ON events(slug);
CREATE INDEX IF NOT EXISTS idx_events_published ON events(published);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_featured ON events(featured);

CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(published);
CREATE INDEX IF NOT EXISTS idx_blog_posts_featured ON blog_posts(featured);

CREATE INDEX IF NOT EXISTS idx_news_articles_slug ON news_articles(slug);
CREATE INDEX IF NOT EXISTS idx_news_articles_published ON news_articles(published);
CREATE INDEX IF NOT EXISTS idx_news_articles_featured ON news_articles(featured);

CREATE INDEX IF NOT EXISTS idx_projects_slug ON projects(slug);
CREATE INDEX IF NOT EXISTS idx_projects_published ON projects(published);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_content_type ON categories(content_type);

CREATE INDEX IF NOT EXISTS idx_event_registrations_event_uid ON event_registrations(event_uid);
CREATE INDEX IF NOT EXISTS idx_comments_content_uid ON comments(content_uid);
CREATE INDEX IF NOT EXISTS idx_comments_content_type ON comments(content_type);

-- Success message
SELECT 'Fresh UUID schema created successfully. All tables use uid as UUID primary key for security.' as result;
