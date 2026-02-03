#!/usr/bin/env python3
"""
Quick Database Table Setup Script
Checks if ca_applications table exists and provides setup instructions
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def check_table_exists():
    """Check if ca_applications table exists"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Try to query the table
        result = supabase.table('ca_applications').select('id').limit(1).execute()
        
        print("✅ SUCCESS: ca_applications table exists!")
        print(f"   Table is ready to accept applications.\n")
        return True
        
    except Exception as e:
        error_str = str(e)
        
        if 'Could not find' in error_str or 'ca_applications' in error_str:
            print("❌ ERROR: ca_applications table NOT FOUND")
            print("\n📋 SETUP REQUIRED:")
            print("   1. Open your Supabase Dashboard: https://supabase.com")
            print("   2. Go to 'SQL Editor' in the left sidebar")
            print("   3. Copy and run the SQL from: QUICK_DB_SETUP.sql")
            print("\n   OR run the full migration:")
            print("   - File: database/migrations/001_ca_ecosystem_schema.sql")
            print("\n   This will create all required tables for CA applications.")
            return False
        else:
            print(f"❌ UNEXPECTED ERROR: {error_str}")
            return False

if __name__ == '__main__':
    print("🔍 Checking Supabase Database Setup...\n")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ ERROR: Missing Supabase credentials in .env file")
        print("   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        exit(1)
    
    print(f"📡 Connecting to: {SUPABASE_URL}\n")
    
    if check_table_exists():
        print("🎉 Your database is ready!")
        print("   CA applications can now be submitted successfully.")
    else:
        print("\n⚠️  Please run the database setup SQL to fix this issue.")
        exit(1)
