# migrate_db.py - Fix database schema
import sqlite3
import os

def migrate_database():
    print("=" * 60)
    print("🔄 Migrating Database Schema")
    print("=" * 60)
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check and add missing columns to files table
    try:
        c.execute("SELECT processed_for_vector FROM files LIMIT 1")
        print("✅ processed_for_vector column already exists")
    except sqlite3.OperationalError:
        print("📝 Adding processed_for_vector column...")
        c.execute("ALTER TABLE files ADD COLUMN processed_for_vector INTEGER DEFAULT 0")
        print("✅ Added processed_for_vector column")
    
    # Check if file_content column exists
    try:
        c.execute("SELECT file_content FROM files LIMIT 1")
        print("✅ file_content column already exists")
    except sqlite3.OperationalError:
        print("📝 Adding file_content column...")
        c.execute("ALTER TABLE files ADD COLUMN file_content TEXT")
        print("✅ Added file_content column")
    
    # Check if image_id and file_id columns exist in conversation table
    try:
        c.execute("SELECT image_id FROM conversation LIMIT 1")
        print("✅ image_id column already exists")
    except sqlite3.OperationalError:
        print("📝 Adding image_id column...")
        c.execute("ALTER TABLE conversation ADD COLUMN image_id INTEGER")
        print("✅ Added image_id column")
    
    try:
        c.execute("SELECT file_id FROM conversation LIMIT 1")
        print("✅ file_id column already exists")
    except sqlite3.OperationalError:
        print("📝 Adding file_id column...")
        c.execute("ALTER TABLE conversation ADD COLUMN file_id INTEGER")
        print("✅ Added file_id column")
    
    conn.commit()
    
    # Show table schema
    print("\n📊 Files Table Schema:")
    c.execute("PRAGMA table_info(files)")
    columns = c.fetchall()
    for col in columns:
        print(f"   • {col[1]} ({col[2]})")
    
    conn.close()
    print("\n✅ Database migration completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    migrate_database()