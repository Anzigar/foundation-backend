-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    timeline VARCHAR(255),
    links JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE
);

-- Create project images table
CREATE TABLE IF NOT EXISTS project_images (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    image_url VARCHAR(255) NOT NULL,
    primary BOOLEAN DEFAULT FALSE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX projects_slug_idx ON projects(slug);
CREATE INDEX projects_published_idx ON projects(published);
CREATE INDEX projects_featured_idx ON projects(featured);
CREATE INDEX project_images_project_id_idx ON project_images(project_id);
CREATE INDEX project_images_primary_idx ON project_images(primary);
CREATE INDEX project_images_order_idx ON project_images("order");
