#!/usr/bin/env python3
"""
Database cleanup script for Face Authentication App
This script removes all user data, login history, and associated files.
"""

import os
import sys
from datetime import datetime

def clear_database():
    """Clear all user data from the database"""
    try:
        from app import app, db
        from models import User, LoginHistory
        
        with app.app_context():
            print("🗑️  Starting database cleanup...")
            print("=" * 50)
            
            # Get statistics before cleanup
            user_count = User.query.count()
            login_count = LoginHistory.query.count()
            
            if user_count == 0 and login_count == 0:
                print("✅ Database is already empty!")
                return
            
            print(f"📊 Found {user_count} users and {login_count} login records")
            
            # Confirm cleanup
            response = input("⚠️  Are you sure you want to delete ALL data? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cleanup cancelled.")
                return
            
            # Get all users to clean up their photo files
            users = User.query.all()
            
            # Delete all photo files
            deleted_photos = 0
            for user in users:
                if user.photo_path and os.path.exists(user.photo_path):
                    try:
                        os.remove(user.photo_path)
                        deleted_photos += 1
                        print(f"🗑️  Deleted photo: {user.photo_path}")
                    except Exception as e:
                        print(f"❌ Failed to delete photo {user.photo_path}: {e}")
            
            # Clean up uploads directory
            uploads_dir = "static/uploads"
            if os.path.exists(uploads_dir):
                try:
                    for file in os.listdir(uploads_dir):
                        file_path = os.path.join(uploads_dir, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"🗑️  Deleted upload: {file_path}")
                except Exception as e:
                    print(f"❌ Error cleaning uploads directory: {e}")
            
            # Delete all login history records
            LoginHistory.query.delete()
            
            # Delete all users
            User.query.delete()
            
            # Commit changes
            db.session.commit()
            
            print("=" * 50)
            print("✅ Database cleanup completed successfully!")
            print(f"📊 Removed:")
            print(f"   • {user_count} user accounts")
            print(f"   • {login_count} login history records")
            print(f"   • {deleted_photos} photo files")
            print(f"⏰ Cleanup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("Make sure you're running this script from the project directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        try:
            db.session.rollback()
        except:
            pass
        sys.exit(1)

def main():
    """Main function"""
    print("🔐 Face Authentication App - Database Cleanup Tool")
    print("This tool will remove ALL user data from the database.")
    print()
    
    clear_database()

if __name__ == "__main__":
    main()