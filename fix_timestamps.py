#!/usr/bin/env python3
"""Fix mixed timezone formats in conversations database."""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data-sources' / 'conversations.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Fix conversation timestamps
cursor.execute("SELECT id, created_at, updated_at FROM conversations")
for conv_id, created, updated in cursor.fetchall():
    # Normalize created_at
    if created and not created.endswith('Z') and not created.endswith('+00:00'):
        # Convert space to T if needed
        created_fixed = created.replace(' ', 'T')
        if '.' in created_fixed:
            created_fixed = created_fixed.split('.')[0] + 'Z'
        else:
            created_fixed = created_fixed + 'Z'
        cursor.execute("UPDATE conversations SET created_at = ? WHERE id = ?", (created_fixed, conv_id))
        print(f"Fixed created_at for {conv_id}: {created} -> {created_fixed}")
    
    # Normalize updated_at
    if updated and not updated.endswith('Z') and not updated.endswith('+00:00'):
        # Convert space to T if needed
        updated_fixed = updated.replace(' ', 'T')
        if '.' in updated_fixed:
            # Keep microseconds but add Z
            if not updated_fixed.endswith('Z'):
                updated_fixed = updated_fixed + 'Z'
        else:
            updated_fixed = updated_fixed + 'Z'
        cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (updated_fixed, conv_id))
        print(f"Fixed updated_at for {conv_id}: {updated} -> {updated_fixed}")

# Fix message timestamps (just in case)
cursor.execute("SELECT id, timestamp FROM messages")
for msg_id, ts in cursor.fetchall():
    if ts and not ts.endswith('Z') and not ts.endswith('+00:00'):
        ts_fixed = ts.replace(' ', 'T')
        if '.' in ts_fixed:
            ts_fixed = ts_fixed.split('.')[0] + 'Z'
        else:
            ts_fixed = ts_fixed + 'Z'
        cursor.execute("UPDATE messages SET timestamp = ? WHERE id = ?", (ts_fixed, msg_id))
        print(f"Fixed timestamp for message {msg_id}: {ts} -> {ts_fixed}")

conn.commit()
conn.close()

print("\n✅ All timestamps normalized to UTC with 'Z' suffix")
