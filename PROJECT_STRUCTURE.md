# Project Structure Organization

This project has been organized following Google's senior developer standards with clean file naming and structure.

## Environment Files

- `.env.example` - Template for environment variables
- `.env.development` - Development environment configuration  
- `.env.production` - Production environment configuration
- `.env` - Local environment (copy from .env.development)

**Usage:**
```bash
# For development
cp .env.development .env

# For production
cp .env.production .env
```

## Directory Structure

```
foundation-backend/
├── alembic/                 # Database migration management
├── api/                     # API endpoints
│   └── file_uploads.py      # File upload handling
├── app/                     # Application modules (if using app-based structure)
├── blog/                    # Blog module
├── contacts/                # Contacts module  
├── events/                  # Events module
├── news/                    # News module
├── projects/                # Projects module
├── shared/                  # Shared utilities and models
├── migrations/              # SQL migration scripts
├── pathways/                # API testing files (Bruno)
├── scripts/                 # Utility scripts
├── tests/                   # Test files
└── uploads/                 # File uploads directory
```

## File Naming Conventions

- **Python files**: `snake_case.py`
- **Shell scripts**: `snake_case.sh` 
- **SQL files**: `descriptive_name.sql`
- **Config files**: `kebab-case` or `snake_case`

## Cleaned Up Files

### Removed Files:
- `fix_production.sh` (empty duplicate)
- `entrypoint-new.sh` (duplicate)
- `apply_category_id_fix.sh` (obsolete)
- `fix_tables.py` (obsolete)
- `fix_tables.sql` (obsolete)
- `api/uploads_clean.py` (empty file)
- `api/uploads_simple.py` (redundant)

### Renamed Files:
- `api/uploads.py` → `api/file_uploads.py`
- `restart-backend.sh` → `restart_backend.sh`
- `run-service.sh` → `run_service.sh`
- `fix-production.sh` → `fix_production.sh`

### Archived Files:
- `migrations/create_projects_tables.sql` → `migrations/archive_create_projects_tables.sql`
- `migrations/remove_category_id.sql` → `migrations/archive_remove_category_id.sql`
- `migrations/rename_project_links.sql` → `migrations/archive_rename_project_links.sql`

## Environment Management

The project now supports proper environment separation:

1. **Development**: Use `.env.development`
2. **Production**: Use `.env.production` 
3. **Local**: Copy appropriate env file to `.env`

## Migration Strategy

- Current migrations are in `migrations/standardize_models.sql`
- Archived legacy migrations are prefixed with `archive_`
- Use Alembic for future schema changes

## Best Practices Applied

✅ **File Organization**: Clean directory structure  
✅ **Naming Conventions**: Consistent snake_case for Python/scripts  
✅ **Environment Separation**: Development and production configs  
✅ **Duplicate Removal**: Eliminated redundant files  
✅ **Documentation**: Clear structure documentation  
✅ **Migration Management**: Organized SQL migrations
