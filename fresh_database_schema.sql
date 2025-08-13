-- Fresh database schema with UUID primary keys for security
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Events table with UUID primary key
CREATE TABLE events (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    excerpt VARCHAR(500),
    location VARCHAR(255),
    venue_details TEXT,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    event_date TIMESTAMP,
    image_url VARCHAR(255),
    ticket_price VARCHAR(100),
    registration_link VARCHAR(255),
    contact_info TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    allow_comments BOOLEAN DEFAULT TRUE,
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    tags VARCHAR(255),
    author_name VARCHAR(100),
    category_ids JSONB DEFAULT '[]'::jsonb,
    related_events JSONB DEFAULT '[]'::jsonb
);

-- Blog posts table with UUID primary key
CREATE TABLE blog_posts (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt VARCHAR(500),
    author_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    tags VARCHAR(255),
    category_ids JSONB DEFAULT '[]'::jsonb
);

-- News articles table with UUID primary key
CREATE TABLE news_articles (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt VARCHAR(500),
    author_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    tags VARCHAR(255),
    category_ids JSONB DEFAULT '[]'::jsonb
);

-- Projects table with UUID primary key
CREATE TABLE projects (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    content TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    seo_title VARCHAR(255),
    meta_description VARCHAR(255),
    og_image_url VARCHAR(255),
    tags VARCHAR(255),
    category_ids JSONB DEFAULT '[]'::jsonb
);

-- Contacts table with UUID primary key
CREATE TABLE contacts (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'new'
);

-- Event registrations table with UUID primary key and foreign key
CREATE TABLE event_registrations (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_uid UUID NOT NULL REFERENCES events(uid) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_events_slug ON events(slug);
CREATE INDEX idx_events_published ON events(published);
CREATE INDEX idx_events_start_date ON events(start_date);
CREATE INDEX idx_events_featured ON events(featured);

CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_published ON blog_posts(published);

CREATE INDEX idx_news_articles_slug ON news_articles(slug);
CREATE INDEX idx_news_articles_published ON news_articles(published);

CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_published ON projects(published);

CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_event_registrations_event_uid ON event_registrations(event_uid);

COMMIT;
