#!/usr/bin/env python3
"""
Migrate conversations from localStorage JSON backup to SQLite database
"""
import json
import sqlite3
from datetime import datetime

# Paths
JSON_FILE = '/Users/adrianboerstra/projects/maximQBR/ALL-LOCALSTORAGE-2025-11-14.json'
DB_FILE = '/Users/adrianboerstra/projects/maximQBR/data-sources/conversations.db'

def migrate():
    # Read JSON backup
    print(f"📖 Reading backup from {JSON_FILE}")
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    # Extract conversations
    conversations_json = data.get('data', {}).get('qbr_conversations')
    if not conversations_json:
        print("❌ No qbr_conversations found in backup")
        return
    
    conversations = json.loads(conversations_json)
    print(f"✅ Found {len(conversations)} conversations")
    
    # Connect to database
    print(f"\n📊 Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Clear existing data (only the test conversation)
    cursor.execute("DELETE FROM messages")
    cursor.execute("DELETE FROM conversations")
    print("✅ Cleared existing database")
    
    # Migrate conversations
    migrated_count = 0
    message_count = 0
    
    for conv in conversations:
        try:
            # Insert conversation
            cursor.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                conv['id'],
                conv['title'],
                conv['createdAt'],
                conv['updatedAt']
            ))
            
            # Insert messages
            for msg in conv.get('messages', []):
                # Make message ID globally unique by prepending conversation ID
                unique_msg_id = f"{conv['id']}_msg_{msg['id']}"
                cursor.execute("""
                    INSERT INTO messages (id, conversation_id, role, content, timestamp, sources)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    unique_msg_id,
                    conv['id'],
                    msg['role'],
                    msg['content'],
                    msg['timestamp'],
                    json.dumps(msg.get('sources')) if msg.get('sources') else None
                ))
                message_count += 1
            
            migrated_count += 1
            print(f"  ✓ {conv['title'][:50]}... ({len(conv.get('messages', []))} messages)")
            
        except Exception as e:
            print(f"  ✗ Failed to migrate {conv['id']}: {e}")
            continue
    
    # Commit
    conn.commit()
    conn.close()
    
    print(f"\n🎉 SUCCESS!")
    print(f"   Migrated: {migrated_count} conversations")
    print(f"   Total messages: {message_count}")
    print(f"   Database: {DB_FILE}")

if __name__ == '__main__':
    migrate()
