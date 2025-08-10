
DO $$ 
BEGIN
    IF EXISTS (SELECT column_name 
               FROM information_schema.columns 
               WHERE table_name='projects' AND column_name='github_link') THEN
        ALTER TABLE projects RENAME COLUMN github_link TO source_link;
        RAISE NOTICE 'github_link column renamed to source_link';
    ELSE
        RAISE NOTICE 'github_link column does not exist in projects table';
    END IF;
END $$;

-- Rename demo_link to live_link for more generic use
DO $$ 
BEGIN
    IF EXISTS (SELECT column_name 
               FROM information_schema.columns 
               WHERE table_name='projects' AND column_name='demo_link') THEN
        ALTER TABLE projects RENAME COLUMN demo_link TO live_link;
        RAISE NOTICE 'demo_link column renamed to live_link';
    ELSE
        RAISE NOTICE 'demo_link column does not exist in projects table';
    END IF;
END $$;
