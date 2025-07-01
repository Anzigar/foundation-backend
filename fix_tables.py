#!/usr/bin/env python3
"""
Simple script to manually create missing tables using SQLAlchemy.
"""

import os
import sys
from sqlalchemy import create_engine, text

def get_database_url():
    """Get the synchronous database URL for table creation."""
    host = os.getenv('POSTGRES_HOST', 'database')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'website_db')
    
    return f'postgresql://{user}:{password}@{host}:{port}/{database}'

def main():
    """Create missing tables and add missing columns."""
    try:
        db_url = get_database_url()
        print(f"Connecting to: {db_url.replace(os.getenv('POSTGRES_PASSWORD', ''), '***')}")
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Create missing tables
            print("Creating missing tables...")
            
            # Create news_articles table with all required fields
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    excerpt VARCHAR(500),
                    image_url VARCHAR(255),
                    source VARCHAR(255),
                    tags VARCHAR(255),
                    published BOOLEAN DEFAULT FALSE,
                    is_published BOOLEAN DEFAULT FALSE,
                    featured BOOLEAN DEFAULT FALSE,
                    allow_comments BOOLEAN DEFAULT TRUE,
                    seo_title VARCHAR(255),
                    meta_description VARCHAR(255),
                    og_image_url VARCHAR(255),
                    contact_info TEXT,
                    author_name VARCHAR(100),
                    category VARCHAR(100),
                    venue VARCHAR(255),
                    location VARCHAR(255),
                    registration_link VARCHAR(255),
                    ticket_price VARCHAR(100),
                    event_start_date TIMESTAMP,
                    event_end_date TIMESTAMP,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category_ids JSONB DEFAULT '[]',
                    related_news_ids JSONB DEFAULT '[]'
                )
            """))
            
            # Create events table with all required fields
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published BOOLEAN DEFAULT FALSE,
                    is_published BOOLEAN DEFAULT FALSE,
                    featured BOOLEAN DEFAULT FALSE,
                    allow_comments BOOLEAN DEFAULT TRUE,
                    seo_title VARCHAR(255),
                    meta_description VARCHAR(255),
                    og_image_url VARCHAR(255),
                    tags VARCHAR(255),
                    author_name VARCHAR(100),
                    category_ids JSONB DEFAULT '[]',
                    related_events JSONB DEFAULT '[]'
                )
            """))
            
            # Create users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    full_name VARCHAR(100),
                    bio TEXT,
                    profile_image_url VARCHAR(255),
                    password_hash VARCHAR(255) NOT NULL,
                    social_links JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create projects table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    project_image VARCHAR(255),
                    project_image_preview VARCHAR(255),
                    image_title VARCHAR(255),
                    image_description TEXT,
                    github_link VARCHAR(255),
                    demo_link VARCHAR(255),
                    technologies JSONB DEFAULT '[]',
                    is_ongoing BOOLEAN DEFAULT TRUE,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    featured BOOLEAN DEFAULT FALSE,
                    public BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create contacts table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone_number VARCHAR(20),
                    subject VARCHAR(255),
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded BOOLEAN DEFAULT FALSE,
                    responded_at TIMESTAMP,
                    responded_by INTEGER REFERENCES users(id)
                )
            """))
            
            # Create project_images table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_images (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    title VARCHAR(255),
                    description TEXT,
                    image_url VARCHAR(255) NOT NULL,
                    "primary" BOOLEAN DEFAULT FALSE,
                    "order" INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create category tables
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS news_categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    slug VARCHAR(50) UNIQUE NOT NULL,
                    description VARCHAR(255)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS event_categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    slug VARCHAR(50) UNIQUE NOT NULL,
                    description VARCHAR(255)
                )
            """))
            
            # Create newsletter_subscribers table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    unsubscribed_at TIMESTAMP
                )
            """))
            
            # Add missing columns to blog_posts if they don't exist
            conn.execute(text("""
                ALTER TABLE blog_posts 
                ADD COLUMN IF NOT EXISTS author_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE
            """))
            
            conn.commit()
            print("✅ All tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
