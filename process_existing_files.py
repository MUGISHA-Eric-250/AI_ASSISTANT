# process_existing_files.py - Process existing uploaded files into vector database
import sqlite3
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from vector_db import init_vector_db
except ImportError as e:
    print(f"❌ Cannot import vector_db: {e}")
    print("Make sure you have installed: pip install chromadb sentence-transformers")
    sys.exit(1)

def process_existing_files():
    """Process all existing uploaded files into vector database"""
    print("=" * 60)
    print("🔄 Processing Existing Files into Vector Database")
    print("=" * 60)
    
    # Initialize vector DB
    print("\n📦 Initializing vector database...")
    vector_db = init_vector_db()
    if not vector_db:
        print("❌ Failed to initialize vector database")
        print("💡 Install required packages: pip install chromadb sentence-transformers")
        return
    
    # Connect to database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get all files
    c.execute("SELECT id, filename, filepath, user_id, processed_for_vector FROM files")
    files = c.fetchall()
    
    if not files:
        print("No files found in database.")
        conn.close()
        return
    
    print(f"\n📁 Found {len(files)} files to process")
    print("-" * 60)
    
    processed = 0
    skipped = 0
    errors = 0
    
    for file_id, filename, filepath, user_id, processed_flag in files:
        if processed_flag:
            print(f"⏭️  Skipping {filename} (already processed)")
            skipped += 1
            continue
        
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filename} (path: {filepath})")
            errors += 1
            continue
        
        print(f"📄 Processing: {filename} (User: {user_id})")
        result = vector_db.process_uploaded_file(filepath, filename, user_id)
        
        if result['success']:
            # Update database
            c.execute("UPDATE files SET processed_for_vector = 1 WHERE id = ?", (file_id,))
            conn.commit()
            processed += 1
            print(f"   ✅ {result['message']}")
        else:
            errors += 1
            print(f"   ❌ {result['message']}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("📊 Processing Summary:")
    print(f"   ✅ Processed: {processed}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    print("=" * 60)
    
    # Show vector DB stats
    print("\n📊 Vector Database Statistics:")
    stats = vector_db.get_collection_info()
    for key, value in stats.items():
        print(f"   • {key}: {value}")

if __name__ == '__main__':
    process_existing_files()