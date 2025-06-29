-- Foundation Backend Database Schema
-- Manual table creation script for production deployment
-- Run this script if Alembic migrations fail

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    bio TEXT,
    profile_image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create blog_categories table
CREATE TABLE IF NOT EXISTS blog_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Create index for blog_categories slug
CREATE INDEX IF NOT EXISTS ix_blog_categories_slug ON blog_categories (slug);

-- Create media table
CREATE TABLE IF NOT EXISTS media (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_key VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(255) NOT NULL,
    thumbnail_url VARCHAR(255),
    file_type VARCHAR(50),
    file_size INTEGER,
    mime_type VARCHAR(100),
    tags JSON,
    folder VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create blog_posts table
CREATE TABLE IF NOT EXISTS blog_posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    excerpt TEXT,
    content TEXT NOT NULL,
    author_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES blog_categories(id),
    featured_image_id INTEGER REFERENCES media(id),
    meta_title VARCHAR(60),
    meta_description VARCHAR(160),
    tags JSON,
    status VARCHAR(20) DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for blog_posts
CREATE INDEX IF NOT EXISTS ix_blog_posts_slug ON blog_posts (slug);
CREATE INDEX IF NOT EXISTS ix_blog_posts_status ON blog_posts (status);
CREATE INDEX IF NOT EXISTS ix_blog_posts_published_at ON blog_posts (published_at);

-- Create news_articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    excerpt TEXT,
    content TEXT NOT NULL,
    author_id INTEGER REFERENCES users(id),
    featured_image_id INTEGER REFERENCES media(id),
    meta_title VARCHAR(60),
    meta_description VARCHAR(160),
    tags JSON,
    status VARCHAR(20) DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for news_articles
CREATE INDEX IF NOT EXISTS ix_news_articles_slug ON news_articles (slug);
CREATE INDEX IF NOT EXISTS ix_news_articles_status ON news_articles (status);
CREATE INDEX IF NOT EXISTS ix_news_articles_published_at ON news_articles (published_at);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    content TEXT,
    location VARCHAR(255),
    event_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    registration_url VARCHAR(500),
    max_attendees INTEGER,
    featured_image_id INTEGER REFERENCES media(id),
    organizer_id INTEGER REFERENCES users(id),
    meta_title VARCHAR(60),
    meta_description VARCHAR(160),
    tags JSON,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for events
CREATE INDEX IF NOT EXISTS ix_events_slug ON events (slug);
CREATE INDEX IF NOT EXISTS ix_events_status ON events (status);
CREATE INDEX IF NOT EXISTS ix_events_event_date ON events (event_date);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    content TEXT,
    status VARCHAR(20) DEFAULT 'active',
    project_url VARCHAR(500),
    github_url VARCHAR(500),
    demo_url VARCHAR(500),
    featured_image_id INTEGER REFERENCES media(id),
    tech_stack JSON,
    tags JSON,
    start_date DATE,
    end_date DATE,
    meta_title VARCHAR(60),
    meta_description VARCHAR(160),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for projects
CREATE INDEX IF NOT EXISTS ix_projects_slug ON projects (slug);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status);

-- Create contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    subject VARCHAR(200),
    message TEXT NOT NULL,
    phone VARCHAR(20),
    company VARCHAR(100),
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for contacts
CREATE INDEX IF NOT EXISTS ix_contacts_status ON contacts (status);
CREATE INDEX IF NOT EXISTS ix_contacts_created_at ON contacts (created_at);

-- Create alembic_version table for migration tracking
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert current migration version if not exists
INSERT INTO alembic_version (version_num) 
VALUES ('production_2025')
ON CONFLICT (version_num) DO NOTHING;

-- Grant permissions (adjust as needed for your user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

COMMIT;
