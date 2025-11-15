import sqlite3
import os
from pathlib import Path

# Find the database file
def find_db_file():
    # Check common locations
    possible_paths = [
        'finucity_app.db',
        'instance/finucity_app.db',
        'finucity/finucity_app.db',
        'finucity/instance/finucity_app.db',
        'app.db',
        'instance/app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found database at: {path}")
            return path
    
    # If not found in common locations, search for .db files
    db_files = list(Path('.').rglob('*.db'))
    if db_files:
        print(f"Found database at: {db_files[0]}")
        return str(db_files[0])
    
    return None

# Connect to your SQLite database
db_path = find_db_file()

if not db_path:
    print("Error: Could not find the SQLite database file!")
    exit(1)
    
print(f"Working with database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the conversation table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
if not cursor.fetchone():
    print("Creating conversations table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id VARCHAR(100) NOT NULL UNIQUE,
        title VARCHAR(200),
        category VARCHAR(50),
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    print("Conversations table created!")
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_conversations_session_id ON conversations (session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations (user_id)")
    print("Conversation indexes created!")

# Check if the column exists in chat_queries
cursor.execute("PRAGMA table_info(chat_queries)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

# Add missing columns to chat_queries if they don't exist
columns_to_add = [
    ('conversation_id', 'TEXT'),
    ('confidence_score', 'FLOAT'),
    ('response_time', 'FLOAT'),
    ('rating', 'INTEGER'),
    ('is_helpful', 'BOOLEAN'),
    ('feedback_text', 'TEXT')
]

for column_name, column_type in columns_to_add:
    if column_name not in column_names:
        try:
            print(f"Adding column {column_name} to chat_queries...")
            cursor.execute(f"ALTER TABLE chat_queries ADD COLUMN {column_name} {column_type}")
            print(f"Successfully added {column_name} column")
        except Exception as e:
            print(f"Error adding {column_name}: {e}")

# Create index on conversation_id
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_chat_queries_conversation_id ON chat_queries (conversation_id)")
    print("Created index on conversation_id")
except Exception as e:
    print(f"Error creating index: {e}")

# Update all existing rows to set conversation_id = session_id for consistency
try:
    cursor.execute("UPDATE chat_queries SET conversation_id = session_id WHERE conversation_id IS NULL AND session_id IS NOT NULL")
    rows_updated = cursor.rowcount
    print(f"Updated {rows_updated} rows to set conversation_id = session_id")
except Exception as e:
    print(f"Error updating rows: {e}")

# Commit and close
conn.commit()
conn.close()

print("Database update complete!")
print("You can now run your app with: python app.py")