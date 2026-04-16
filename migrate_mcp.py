# migrate_mcp.py
import sqlite3

def migrate_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check if tool_used column exists in conversation table
    try:
        c.execute("SELECT tool_used FROM conversation LIMIT 1")
    except sqlite3.OperationalError:
        # Add tool_used column if it doesn't exist
        c.execute("ALTER TABLE conversation ADD COLUMN tool_used TEXT")
        print("✅ Added tool_used column to conversation table")
    
    # Check if file_content column exists in files table (from your error)
    try:
        c.execute("SELECT file_content FROM files LIMIT 1")
    except sqlite3.OperationalError:
        # Add file_content column if it doesn't exist
        c.execute("ALTER TABLE files ADD COLUMN file_content TEXT")
        print("✅ Added file_content column to files table")
    
    conn.commit()
    conn.close()
    print("✅ Database migration completed")

if __name__ == '__main__':
    migrate_database()