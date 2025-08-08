#!/usr/bin/env python3
"""
Setup script to add admin user to existing ai_user table
"""

import mysql.connector
import hashlib
from config import DB_CONFIG

def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_admin_user():
    """Add admin user to ai_user table."""
    try:
        print("🔧 Setting up admin user in ai_user table...")
        
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if ai_user table exists
        cursor.execute("SHOW TABLES LIKE 'ai_user'")
        if not cursor.fetchone():
            print("❌ ai_user table not found!")
            return False
        
        # Check current structure
        cursor.execute("DESCRIBE ai_user")
        column_info = cursor.fetchall()
        columns = [row[0] for row in column_info]
        print(f"📋 Current ai_user columns: {columns}")

        # Check session_id column size
        for col in column_info:
            if col[0] == 'session_id':
                print(f"📏 session_id column type: {col[1]}")
                # If it's too small, expand it
                if 'char(8)' in col[1].lower() or 'varchar(3)' in col[1].lower() or 'varchar(10)' in col[1].lower():
                    print("🔧 Expanding session_id column...")
                    cursor.execute("ALTER TABLE ai_user MODIFY COLUMN session_id VARCHAR(50)")
                break
        
        # Add missing columns if needed
        if 'id' not in columns:
            print("➕ Adding id column...")
            cursor.execute("ALTER TABLE ai_user ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST")
        
        if 'full_name' not in columns:
            print("➕ Adding full_name column...")
            cursor.execute("ALTER TABLE ai_user ADD COLUMN full_name VARCHAR(255) DEFAULT NULL")
        
        if 'is_active' not in columns:
            print("➕ Adding is_active column...")
            cursor.execute("ALTER TABLE ai_user ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        if 'created_at' not in columns:
            print("➕ Adding created_at column...")
            cursor.execute("ALTER TABLE ai_user ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        
        if 'last_login' not in columns:
            print("➕ Adding last_login column...")
            cursor.execute("ALTER TABLE ai_user ADD COLUMN last_login DATETIME DEFAULT NULL")
        
        # Check if admin user already exists
        cursor.execute("SELECT COUNT(*) FROM ai_user WHERE email = %s", ("admin@example.com",))
        admin_exists = cursor.fetchone()[0] > 0

        if admin_exists:
            print("✅ Admin user already exists")
            # Update password in case it's different
            password_hash = hash_password("admin123")
            cursor.execute("""
                UPDATE ai_user SET password = %s, full_name = %s, is_active = %s
                WHERE email = %s
            """, (password_hash, "Administrator", True, "admin@example.com"))
            print("🔄 Updated admin user password and details")
        else:
            # Create admin user with session_id
            password_hash = hash_password("admin123")
            import random
            import string
            # Generate session ID (8 characters to fit current column)
            session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            cursor.execute("""
                INSERT INTO ai_user (email, password, session_id, full_name, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, ("admin@example.com", password_hash, session_id, "Administrator", True))
            print("✅ Created admin user")

        # Show all users
        cursor.execute("SELECT id, email, full_name, is_active, session_id FROM ai_user")
        users = cursor.fetchall()
        
        print("\n👥 Current users in ai_user table:")
        for user in users:
            status = "✅ Active" if (len(user) <= 3 or user[3] is None or user[3]) else "❌ Inactive"
            session_preview = user[4][:8] + "..." if len(user) > 4 and user[4] else "N/A"
            print(f"   ID: {user[0]}, Email: {user[1]}, Name: {user[2] or 'N/A'}, Status: {status}, Session: {session_preview}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 Setup complete!")
        print("📱 Login credentials:")
        print("   Email: admin@example.com")
        print("   Password: admin123")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    setup_admin_user()
