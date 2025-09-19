from app import app, db
from models import User, LoginHistory
import os

def clear_database():
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            
            # Recreate all tables
            db.create_all()
            
            # Clear uploaded face images
            upload_folder = app.config['UPLOAD_FOLDER']
            for filename in os.listdir(upload_folder):
                if filename.endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(upload_folder, filename)
                    try:
                        os.remove(file_path)
                        print(f"Removed file: {filename}")
                    except Exception as e:
                        print(f"Error removing {filename}: {e}")
            
            print("Database cleared successfully!")
            print("All face images removed!")
            
        except Exception as e:
            print(f"Error clearing database: {e}")

if __name__ == "__main__":
    clear_database()