#!/usr/bin/env python3
"""
Database Seeder Script for PostgreSQL
Run this script to populate the database with sample data for testing.

Usage:
    python seed_data.py --seed    # Add sample data
    python seed_data.py --clean   # Remove sample data
    python seed_data.py --reset   # Clean and then seed
"""

import asyncio
import json
import argparse
from datetime import datetime, timedelta
from shared.helpers import execute_query, fetch_one

# Sample data
SAMPLE_BLOG_POSTS = [
    {
        "title": "Building Modern Web Applications with FastAPI",
        "slug": "building-modern-web-applications-fastapi",
        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. In this comprehensive guide, we'll explore how to build scalable, maintainable web applications using FastAPI's powerful features including automatic API documentation, dependency injection, and async support.",
        "excerpt": "Learn how to build high-performance web applications using FastAPI framework",
        "image_url": "https://picsum.photos/800/400?random=1",
        "author_name": "John Doe",
        "tags": "python,fastapi,web-development",
        "is_published": True,
        "featured": True,
        "seo_title": "FastAPI Tutorial - Modern Web Development",
        "meta_description": "Complete guide to building web applications with FastAPI"
    },
    {
        "title": "React Best Practices for 2025",
        "slug": "react-best-practices-2025",
        "content": "React continues to evolve and here are the best practices every developer should follow in 2025. From hooks to performance optimization, we cover everything you need to know to write clean, efficient React code.",
        "excerpt": "Essential React best practices and patterns for modern development",
        "image_url": "https://picsum.photos/800/400?random=2",
        "author_name": "Jane Smith",
        "tags": "react,javascript,frontend",
        "is_published": True,
        "featured": False,
        "seo_title": "React Best Practices 2025",
        "meta_description": "Learn the latest React best practices and patterns"
    },
    {
        "title": "Database Optimization Techniques",
        "slug": "database-optimization-techniques",
        "content": "Performance is crucial for any application. Here are proven database optimization techniques that can significantly improve your application's performance, from indexing strategies to query optimization.",
        "excerpt": "Improve your database performance with these optimization strategies",
        "image_url": "https://picsum.photos/800/400?random=3",
        "author_name": "Mike Johnson",
        "tags": "database,optimization,performance",
        "is_published": True,
        "featured": False,
        "seo_title": "Database Optimization Guide",
        "meta_description": "Essential database optimization techniques for better performance"
    }
]

SAMPLE_NEWS_ARTICLES = [
    {
        "title": "Community Outreach Program Launched",
        "slug": "community-outreach-program-launched",
        "content": "We are excited to announce the launch of our new community outreach program aimed at supporting local families in need. This initiative will provide essential resources and support to underserved communities.",
        "excerpt": "New program aims to support local families and communities",
        "image_url": "https://picsum.photos/800/400?random=4",
        "author_name": "Sarah Wilson",
        "category": "community",
        "is_published": True,
        "featured": True,
        "seo_title": "Community Outreach Program - Making a Difference",
        "meta_description": "Learn about our new community outreach program and how it helps local families"
    },
    {
        "title": "Annual Fundraising Event Success",
        "slug": "annual-fundraising-event-success",
        "content": "Our annual fundraising event was a tremendous success, raising over $50,000 for local charitable causes. Thank you to all our supporters and volunteers who made this possible.",
        "excerpt": "Annual event raises significant funds for charitable causes",
        "image_url": "https://picsum.photos/800/400?random=5",
        "author_name": "David Brown",
        "category": "events",
        "is_published": True,
        "featured": False,
        "seo_title": "Fundraising Event Success Story",
        "meta_description": "Read about our successful annual fundraising event and its impact"
    }
]

SAMPLE_EVENTS = [
    {
        "title": "Tech Conference 2025",
        "slug": "tech-conference-2025",
        "content": "Join us for the most anticipated tech conference of the year. Learn from industry experts and network with fellow developers.",
        "excerpt": "Annual technology conference featuring industry leaders",
        "image_url": "https://picsum.photos/800/400?random=6",
        "author_name": "Tech Team",
        "location": "San Francisco, CA",
        "event_date": datetime.now() + timedelta(days=30),
        "registration_link": "https://example.com/register",
        "is_published": True,
        "featured": True,
        "seo_title": "Tech Conference 2025 - Don't Miss Out",
        "meta_description": "Register for the biggest tech conference of 2025"
    },
    {
        "title": "Community Cleanup Day",
        "slug": "community-cleanup-day",
        "content": "Help us make our community cleaner and greener. Join our volunteer cleanup day and make a positive impact on our environment.",
        "excerpt": "Volunteer opportunity to help clean up our community",
        "image_url": "https://picsum.photos/800/400?random=7",
        "author_name": "Green Team",
        "location": "Central Park",
        "event_date": datetime.now() + timedelta(days=15),
        "registration_link": "https://example.com/cleanup",
        "is_published": True,
        "featured": False,
        "seo_title": "Community Cleanup Day - Get Involved",
        "meta_description": "Join our community cleanup day and help make a difference"
    }
]

SAMPLE_PROJECTS = [
    {
        "title": "E-Commerce Platform",
        "slug": "ecommerce-platform",
        "description": "A modern, scalable e-commerce platform built with React and Node.js, featuring real-time inventory management, payment processing, and admin dashboard.",
        "project_image": "https://picsum.photos/800/600?random=8",
        "project_image_preview": "https://picsum.photos/400/300?random=8",
        "image_title": "E-Commerce Platform",
        "image_description": "Modern online shopping platform",
        "github_link": "https://github.com/example/ecommerce",
        "demo_link": "https://ecommerce-demo.example.com",
        "technologies": ["React", "Node.js", "PostgreSQL", "Stripe", "Redis"],
        "is_ongoing": False,
        "start_date": datetime.now() - timedelta(days=180),
        "end_date": datetime.now() - timedelta(days=30),
        "featured": True,
        "public": True
    },
    {
        "title": "Task Management App",
        "slug": "task-management-app",
        "description": "A collaborative task management application with real-time updates, team collaboration features, and advanced project tracking capabilities.",
        "project_image": "https://picsum.photos/800/600?random=9",
        "project_image_preview": "https://picsum.photos/400/300?random=9",
        "image_title": "Task Management App",
        "image_description": "Collaborative project management tool",
        "github_link": "https://github.com/example/taskmanager",
        "demo_link": "https://tasks-demo.example.com",
        "technologies": ["Vue.js", "FastAPI", "PostgreSQL", "WebSocket", "Docker"],
        "is_ongoing": True,
        "start_date": datetime.now() - timedelta(days=90),
        "end_date": None,
        "featured": True,
        "public": True
    },
    {
        "title": "Mobile Fitness Tracker",
        "slug": "mobile-fitness-tracker",
        "description": "A comprehensive fitness tracking mobile app with workout planning, progress tracking, and social features to motivate users.",
        "project_image": "https://picsum.photos/800/600?random=10",
        "project_image_preview": "https://picsum.photos/400/300?random=10",
        "image_title": "Fitness Tracker App",
        "image_description": "Mobile app for fitness enthusiasts",
        "github_link": "https://github.com/example/fitness-tracker",
        "demo_link": None,
        "technologies": ["React Native", "Firebase", "MongoDB", "Express.js"],
        "is_ongoing": False,
        "start_date": datetime.now() - timedelta(days=120),
        "end_date": datetime.now() - timedelta(days=10),
        "featured": False,
        "public": True
    }
]

SAMPLE_CONTACTS = [
    {
        "name": "John Smith",
        "email": "john.smith@example.com",
        "phone": "+1 (555) 123-4567",
        "subject": "Website Development Inquiry",
        "message": "Hello, I'm interested in discussing a website development project for my small business. Could we schedule a consultation?",
        "is_read": False
    },
    {
        "name": "Emily Johnson",
        "email": "emily.j@example.com",
        "phone": "+1 (555) 987-6543",
        "subject": "Partnership Opportunity",
        "message": "I represent a nonprofit organization and would like to explore potential partnership opportunities with your foundation.",
        "is_read": True
    },
    {
        "name": "Michael Brown",
        "email": "mbrown@example.com",
        "phone": None,
        "subject": "Volunteer Application",
        "message": "I would like to volunteer with your organization. I have experience in community outreach and event planning.",
        "is_read": False
    }
]

SAMPLE_NEWSLETTER_SUBSCRIPTIONS = [
    {"email": "subscriber1@example.com", "is_active": True},
    {"email": "subscriber2@example.com", "is_active": True},
    {"email": "subscriber3@example.com", "is_active": False},
    {"email": "test@example.com", "is_active": True},
]

async def clean_all_data():
    """Remove all sample data from the database."""
    print("🧹 Cleaning all sample data...")
    
    # Define tables to clean in order (respecting foreign key constraints)
    tables_to_clean = [
        "project_images",
        "projects", 
        "blog_posts",
        "news_articles",
        "events",
        "contacts",
        "newsletter_subscriptions"
    ]
    
    for table in tables_to_clean:
        try:
            # Get count before deletion
            count_result = await fetch_one(f"SELECT COUNT(*) as count FROM {table}")
            count = count_result["count"] if count_result else 0
            
            if count > 0:
                await execute_query(f"DELETE FROM {table}")
                print(f"  ✅ Cleaned {count} records from {table}")
            else:
                print(f"  ℹ️  Table {table} was already empty")
                
        except Exception as e:
            print(f"  ❌ Error cleaning {table}: {e}")
    
    # Reset sequences for PostgreSQL
    try:
        sequences = [
            "blog_posts_id_seq",
            "news_articles_id_seq", 
            "events_id_seq",
            "projects_id_seq",
            "project_images_id_seq",
            "contacts_id_seq",
            "newsletter_subscriptions_id_seq"
        ]
        
        for seq in sequences:
            try:
                await execute_query(f"ALTER SEQUENCE {seq} RESTART WITH 1")
            except Exception:
                # Sequence might not exist, that's okay
                pass
                
        print("  ✅ Reset ID sequences")
    except Exception as e:
        print(f"  ⚠️  Could not reset sequences: {e}")
    
    print("✅ Data cleanup completed!")

async def seed_blog_posts():
    """Seed blog posts."""
    print("📝 Seeding blog posts...")
    
    for post in SAMPLE_BLOG_POSTS:
        now = datetime.now()
        
        await execute_query("""
            INSERT INTO blog_posts (
                title, slug, content, excerpt, image_url, author_name, tags,
                is_published, featured, seo_title, meta_description, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            post["title"], post["slug"], post["content"], post["excerpt"],
            post["image_url"], post["author_name"], post["tags"],
            post["is_published"], post["featured"], post["seo_title"],
            post["meta_description"], now, now
        ))
    
    print("✅ Blog posts seeded successfully!")

async def seed_news_articles():
    """Seed news articles."""
    print("📰 Seeding news articles...")
    
    for article in SAMPLE_NEWS_ARTICLES:
        now = datetime.now()
        
        await execute_query("""
            INSERT INTO news_articles (
                title, slug, content, excerpt, image_url, author_name, category,
                is_published, featured, seo_title, meta_description, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            article["title"], article["slug"], article["content"], article["excerpt"],
            article["image_url"], article["author_name"], article["category"],
            article["is_published"], article["featured"], article["seo_title"],
            article["meta_description"], now, now
        ))
    
    print("✅ News articles seeded successfully!")

async def seed_events():
    """Seed events."""
    print("📅 Seeding events...")
    
    for event in SAMPLE_EVENTS:
        now = datetime.now()
        
        await execute_query("""
            INSERT INTO events (
                title, slug, content, excerpt, image_url, author_name, location,
                event_date, registration_link, is_published, featured, seo_title,
                meta_description, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event["title"], event["slug"], event["content"], event["excerpt"],
            event["image_url"], event["author_name"], event["location"],
            event["event_date"], event["registration_link"], event["is_published"],
            event["featured"], event["seo_title"], event["meta_description"],
            now, now
        ))
    
    print("✅ Events seeded successfully!")

async def seed_projects():
    """Seed projects and project images."""
    print("🚀 Seeding projects...")
    
    for project in SAMPLE_PROJECTS:
        now = datetime.now()
        
        # Convert technologies to JSON string
        technologies_json = json.dumps(project["technologies"])
        
        await execute_query("""
            INSERT INTO projects (
                title, slug, description, project_image, project_image_preview,
                image_title, image_description, github_link, demo_link, technologies,
                is_ongoing, start_date, end_date, featured, public, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            project["title"], project["slug"], project["description"],
            project["project_image"], project["project_image_preview"],
            project["image_title"], project["image_description"],
            project["github_link"], project["demo_link"], technologies_json,
            project["is_ongoing"], project["start_date"], project["end_date"],
            project["featured"], project["public"], now, now
        ))
        
        # Get the project ID
        result = await fetch_one("SELECT id FROM projects WHERE slug = %s", (project["slug"],))
        project_id = result["id"]
        
        # Add sample images for each project
        sample_images = [
            {
                "title": f"{project['title']} - Main View",
                "description": "Main application interface",
                "image_url": f"https://picsum.photos/800/600?random={project_id}0",
                "primary": True,
                "order": 0
            },
            {
                "title": f"{project['title']} - Dashboard",
                "description": "Admin dashboard interface",
                "image_url": f"https://picsum.photos/800/600?random={project_id}1",
                "primary": False,
                "order": 1
            },
            {
                "title": f"{project['title']} - Mobile View",
                "description": "Mobile responsive design",
                "image_url": f"https://picsum.photos/800/600?random={project_id}2",
                "primary": False,
                "order": 2
            }
        ]
        
        for img in sample_images:
            await execute_query("""
                INSERT INTO project_images (
                    project_id, title, description, image_url, primary_image, order_index, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id, img["title"], img["description"], img["image_url"],
                img["primary"], img["order"], now
            ))
    
    print("✅ Projects seeded successfully!")

async def seed_contacts():
    """Seed contact messages."""
    print("📧 Seeding contacts...")
    
    for contact in SAMPLE_CONTACTS:
        now = datetime.now()
        
        await execute_query("""
            INSERT INTO contacts (
                name, email, phone, subject, message, is_read, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            contact["name"], contact["email"], contact["phone"],
            contact["subject"], contact["message"], contact["is_read"], now
        ))
    
    print("✅ Contacts seeded successfully!")

async def seed_newsletter_subscriptions():
    """Seed newsletter subscriptions."""
    print("📧 Seeding newsletter subscriptions...")
    
    for subscription in SAMPLE_NEWSLETTER_SUBSCRIPTIONS:
        now = datetime.now()
        
        await execute_query("""
            INSERT INTO newsletter_subscriptions (
                email, is_active, created_at
            ) VALUES (%s, %s, %s)
        """, (
            subscription["email"], subscription["is_active"], now
        ))
    
    print("✅ Newsletter subscriptions seeded successfully!")

async def seed_all_data():
    """Seed all sample data."""
    print("🌱 Starting database seeding...")
    
    try:
        await seed_blog_posts()
        await seed_news_articles()
        await seed_events()
        await seed_projects()
        await seed_contacts()
        await seed_newsletter_subscriptions()
        
        print("\n🎉 All sample data seeded successfully!")
        print("📊 You can now test the API endpoints with the sample data.")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        raise

async def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Database Seeder for Foundation Backend")
    parser.add_argument("--seed", action="store_true", help="Add sample data to the database")
    parser.add_argument("--clean", action="store_true", help="Remove all sample data from the database")
    parser.add_argument("--reset", action="store_true", help="Clean and then seed the database")
    
    args = parser.parse_args()
    
    if args.reset:
        await clean_all_data()
        await seed_all_data()
    elif args.clean:
        await clean_all_data()
    elif args.seed:
        await seed_all_data()
    else:
        print("Usage:")
        print("  python seed_data.py --seed    # Add sample data")
        print("  python seed_data.py --clean   # Remove sample data")
        print("  python seed_data.py --reset   # Clean and then seed")

if __name__ == "__main__":
    asyncio.run(main())
