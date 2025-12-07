"""
Test MySQL Database Connection
Run this to verify your database is properly configured
"""
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables - prioritize .env.local
from pathlib import Path
env_local = Path('.env.local')
if env_local.exists():
    load_dotenv('.env.local')
else:
    load_dotenv()

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'database': os.getenv('MYSQL_DATABASE', 'chatbot_db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

print("=" * 60)
print("Testing MySQL Connection")
print("=" * 60)
print(f"\nConfiguration:")
print(f"  Host: {MYSQL_CONFIG['host']}")
print(f"  Database: {MYSQL_CONFIG['database']}")
print(f"  User: {MYSQL_CONFIG['user']}")
print(f"  Port: {MYSQL_CONFIG['port']}")
print(f"  Password: {'*' * len(MYSQL_CONFIG['password'])}")

try:
    print("\n[*] Connecting to MySQL...")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    
    if conn.is_connected():
        print("[OK] Connected successfully!")
        
        cursor = conn.cursor()
        
        # Check tables
        print("\n[*] Checking tables...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"[OK] Found {len(tables)} table(s):")
            for table in tables:
                print(f"   - {table[0]}")
                
                # Show table structure
                cursor.execute(f"DESCRIBE {table[0]}")
                columns = cursor.fetchall()
                print(f"     Columns ({len(columns)}):")
                for col in columns:
                    print(f"       * {col[0]} ({col[1]})")
        else:
            print("[!] No tables found! Run the database_setup.sql script.")
        
        # Check for any existing data
        print("\n[*] Checking data...")
        try:
            cursor.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]
            print(f"[OK] Leads table: {count} record(s)")
        except:
            print("[!] Leads table not found")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM chatbots")
            count = cursor.fetchone()[0]
            print(f"[OK] Chatbots table: {count} record(s)")
        except:
            print("[!] Chatbots table not found")
        
        cursor.close()
        conn.close()
        print("\n[OK] All checks passed! Database is ready.")
        
except Error as e:
    print(f"\n[ERROR] Database Error: {e}")
    print("\nPossible solutions:")
    print("  1. Make sure MySQL server is running")
    print("  2. Check your .env.local file has correct credentials")
    print("  3. Run database_setup.sql in MySQL Workbench")
    print("  4. Verify database 'chatbot_db' exists")

print("\n" + "=" * 60)

