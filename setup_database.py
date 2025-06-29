#!/usr/bin/env python3
"""
Comprehensive database setup script for production deployment.
This script ensures all tables are created and migrations are applied correctly.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_db_connection_params():
    """Get database connection parameters from environment variables."""
    params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'database': os.getenv('POSTGRES_DB', 'foundation'),
    }
    
    password = os.getenv('POSTGRES_PASSWORD')
    if password:
        params['password'] = password
    
    return params


def create_sync_db_url(params):
    """Create synchronous database URL."""
    if 'password' in params:
        return f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    else:
        return f"postgresql://{params['user']}@{params['host']}:{params['port']}/{params['database']}"


def check_database_exists(params):
    """Check if the database exists, create if it doesn't."""
    try:
        # Connect to postgres database first
        conn_params = params.copy()
        conn_params['database'] = 'postgres'
        
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (params['database'],))
        exists = cursor.fetchone() is not None
        
        if not exists:
            print(f"Creating database '{params['database']}'...")
            cursor.execute(f"CREATE DATABASE \"{params['database']}\"")
            print(f"Database '{params['database']}' created successfully!")
        else:
            print(f"Database '{params['database']}' already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        return False


def run_alembic_migrations():
    """Run Alembic migrations."""
    try:
        print("Running Alembic migrations...")
        import alembic.config
        import alembic.command
        
        # Get alembic config
        alembic_cfg = alembic.config.Config("alembic.ini")
        
        # Override database URL
        params = get_db_connection_params()
        sync_url = create_sync_db_url(params)
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        
        # Run migrations
        alembic.command.upgrade(alembic_cfg, "head")
        print("Alembic migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error running Alembic migrations: {e}")
        return False


def create_tables_manually():
    """Create tables manually using SQLAlchemy models."""
    try:
        print("Creating tables manually using SQLAlchemy models...")
        
        # Import all models to ensure they're registered
        import blog.models
        import news.models
        import events.models
        import projects.models
        import contacts.models
        import shared.models
        import shared.media_models
        from shared.database import Base
        
        # Create engine
        params = get_db_connection_params()
        sync_url = create_sync_db_url(params)
        engine = create_engine(sync_url)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully using SQLAlchemy models!")
        return True
        
    except Exception as e:
        print(f"Error creating tables manually: {e}")
        return False


def verify_tables_exist():
    """Verify that all expected tables exist in the database."""
    try:
        print("Verifying tables exist...")
        
        params = get_db_connection_params()
        sync_url = create_sync_db_url(params)
        engine = create_engine(sync_url)
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Expected tables based on your models
        expected_tables = [
            'users',
            'blog_categories',
            'blog_posts',
            'news_articles',
            'events',
            'projects',
            'contacts',
            'media',
            'alembic_version'  # Alembic version tracking table
        ]
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' missing")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\nMissing tables: {missing_tables}")
            return False
        else:
            print("\nAll expected tables exist!")
            return True
            
    except Exception as e:
        print(f"Error verifying tables: {e}")
        return False


def generate_sql_script():
    """Generate SQL script for manual database setup."""
    try:
        print("Generating SQL script for manual setup...")
        
        # Import all models
        import blog.models
        import news.models
        import events.models
        import projects.models
        import contacts.models
        import shared.models
        import shared.media_models
        from shared.database import Base
        
        # Create engine with special settings for SQL generation
        params = get_db_connection_params()
        sync_url = create_sync_db_url(params)
        engine = create_engine(sync_url)
        
        # Generate DDL
        from sqlalchemy.schema import CreateTable
        
        sql_statements = []
        sql_statements.append("-- Foundation Backend Database Schema")
        sql_statements.append("-- Generated automatically from SQLAlchemy models")
        sql_statements.append("")
        
        for table in Base.metadata.sorted_tables:
            create_table_ddl = str(CreateTable(table).compile(engine))
            sql_statements.append(f"-- Table: {table.name}")
            sql_statements.append(create_table_ddl + ";")
            sql_statements.append("")
        
        # Write to file
        sql_file = Path("database_schema.sql")
        with open(sql_file, 'w') as f:
            f.write('\n'.join(sql_statements))
        
        print(f"SQL script generated: {sql_file.absolute()}")
        return True
        
    except Exception as e:
        print(f"Error generating SQL script: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Foundation Backend Database Setup")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_DB']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    params = get_db_connection_params()
    print("Database configuration:")
    print(f"  Host: {params['host']}")
    print(f"  Port: {params['port']}")
    print(f"  User: {params['user']}")
    print(f"  Database: {params['database']}")
    print()
    
    # Step 1: Ensure database exists
    if not check_database_exists(params):
        print("Failed to ensure database exists. Exiting.")
        sys.exit(1)
    
    # Step 2: Try running Alembic migrations first
    migration_success = run_alembic_migrations()
    
    # Step 3: If migrations failed, create tables manually
    if not migration_success:
        print("Alembic migrations failed. Attempting manual table creation...")
        if not create_tables_manually():
            print("Manual table creation also failed. Exiting.")
            sys.exit(1)
    
    # Step 4: Verify all tables exist
    if not verify_tables_exist():
        print("Table verification failed. Some tables may be missing.")
        sys.exit(1)
    
    # Step 5: Generate SQL script for future reference
    generate_sql_script()
    
    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
