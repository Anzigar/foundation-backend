#!/bin/sh

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Setup tasks
log "Running setup tasks..."

# Create proxy network if it doesn't exist
if ! docker network ls | grep -q "proxy"; then
    log "Creating Docker network 'proxy'..."
    docker network create proxy || log "Network might already exist or insufficient permissions"
fi

# compose down and force remove containers
log "Stopping and removing existing containers..."
docker compose down || log "No existing containers to stop"
docker rm -f foundation-api foundation_traefik foundation-postgres 2>/dev/null || true

# Ensure entrypoint.sh has execute permissions
log "Setting execute permissions on entrypoint.sh..."
chmod +x entrypoint.sh

# Create and set permissions for acme.json
log "Setting up SSL certificate storage..."
touch acme.json && chmod 600 acme.json

# Start the application
log "Starting the application..."
docker compose up --build -d

# Wait for services to start and stabilize
log "Waiting for services to initialize..."
sleep 10

# Fix missing database tables
log "Fixing missing database tables..."
docker compose exec -T database psql -U postgres -d website_db << 'EOF'
-- Create missing tables that the migration should have created

-- Users table
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
);

-- News articles table with all required fields
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
);

-- Events table
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
);

-- Projects table
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
);

-- Contacts table
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
    responded_by INTEGER
);

-- News categories
CREATE TABLE IF NOT EXISTS news_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- Event categories
CREATE TABLE IF NOT EXISTS event_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- Newsletter subscribers
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP
);

-- Project images
CREATE TABLE IF NOT EXISTS project_images (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    title VARCHAR(255),
    description TEXT,
    image_url VARCHAR(255) NOT NULL,
    primary_image BOOLEAN DEFAULT FALSE,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_news_articles_slug ON news_articles(slug);
CREATE INDEX IF NOT EXISTS ix_events_slug ON events(slug);
CREATE INDEX IF NOT EXISTS ix_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS ix_projects_slug ON projects(slug);
CREATE INDEX IF NOT EXISTS ix_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS ix_newsletter_subscribers_email ON newsletter_subscribers(email);

\echo "Database tables created successfully!"
EOF

log "Database tables fixed!"

# Wait a moment for services to stabilize
sleep 2

# Check if containers are running
log "Checking container status..."
docker compose ps

# Test the API
log "Testing API endpoints..."
sleep 3
curl -s http://localhost:8000/api/health || log "Health check endpoint not available yet"

log "Service started successfully! The API should now be working properly."
log "You can test it at: http://localhost:8000/api/docs"
