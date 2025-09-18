import bcrypt
import secrets
import string
from datetime import datetime
from models import db, User, LoginHistory
from face_recognition import face_recognition
import os


class AuthService:
    def __init__(self, app=None):
        self.app = app
        self.face_threshold = float(os.getenv('FACE_THRESHOLD', 0.6))
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    
    def generate_otp(self):
        """Generate 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def hash_otp(self, otp):
        """Hash OTP for secure storage"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(otp.encode('utf-8'), salt).decode('utf-8')
    
    def verify_otp(self, otp, hashed_otp):
        """Verify OTP against hash"""
        return bcrypt.checkpw(otp.encode('utf-8'), hashed_otp.encode('utf-8'))
    
    def log_login_attempt(self, user_id, success, face_confidence=None, ip_address=None, user_agent=None, failure_reason=None):
        """Log login attempt to history"""
        try:
            login_record = LoginHistory(
                user_id=user_id,
                success=success,
                face_confidence=face_confidence,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            db.session.add(login_record)
            db.session.commit()
        except Exception as e:
            print(f"Error logging login attempt: {e}")
    
    def get_user_login_history(self, user_id, limit=50):
        """Get user's login history"""
        return LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.login_time.desc()).limit(limit).all()
    
    def check_face_uniqueness(self, face_embedding):
        """Check if face already exists in database"""
        if face_embedding is None:
            return False, None
        
        users = User.query.filter(User.embedding.isnot(None)).all()
        
        for user in users:
            stored_embedding = user.get_embedding()
            if stored_embedding is not None:
                is_same, similarity = face_recognition.is_same_person(
                    face_embedding, stored_embedding, self.face_threshold
                )
                if is_same:
                    return False, user  # Face already exists
        
        return True, None  # Face is unique
    
    def register_user(self, name, email, password, face_image_b64):
        """Register a new user"""
        try:
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return False, "Email already registered"
            
            # Extract face embedding
            face_embedding = face_recognition.get_face_embedding(face_image_b64)
            if face_embedding is None:
                return False, "No face detected in image. Please try again."
            
            # Check face uniqueness
            is_unique, duplicate_user = self.check_face_uniqueness(face_embedding)
            if not is_unique:
                return False, "Face already registered. Each person can only have one account."
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Generate OTP
            otp = self.generate_otp()
            otp_hash = self.hash_otp(otp)
            
            # Save face image
            photo_filename = f"{email.replace('@', '_').replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            photo_path = face_recognition.save_face_image(face_image_b64, photo_filename)
            
            # Create user
            user = User(
                name=name,
                email=email,
                password_hash=password_hash,
                photo_path=photo_path,
                otp_hash=otp_hash
            )
            
            # Set embedding and OTP expiry
            user.set_embedding(face_embedding)
            user.set_otp_expiry(int(os.getenv('OTP_EXPIRY_MINUTES', 10)))
            
            db.session.add(user)
            db.session.commit()
            
            return True, {"user_id": user.id, "otp": otp}
            
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}"
    
    def verify_otp_and_activate(self, user_id, otp):
        """Verify OTP and activate user account"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            if user.is_verified:
                return False, "Account already activated"
            
            if not user.is_otp_valid():
                return False, "OTP has expired. Please register again."
            
            if not self.verify_otp(otp, user.otp_hash):
                return False, "Invalid OTP"
            
            # Activate user
            user.is_verified = True
            user.clear_otp()
            
            db.session.commit()
            return True, "Account activated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"OTP verification failed: {str(e)}"
    
    def authenticate_user(self, email, face_image_b64, ip_address=None, user_agent=None):
        """Authenticate user with email and face"""
        try:
            # Find user by email
            user = User.query.filter_by(email=email, is_verified=True).first()
            if not user:
                return False, "No verified account found with this email"
            
            # Extract face embedding from provided image
            face_embedding = face_recognition.get_face_embedding(face_image_b64)
            if face_embedding is None:
                # Log failed attempt
                self.log_login_attempt(
                    user.id, False, None, ip_address, user_agent, 
                    "No face detected in image"
                )
                return False, "No face detected in image. Please try again."
            
            # Get stored embedding
            stored_embedding = user.get_embedding()
            if stored_embedding is None:
                # Log failed attempt
                self.log_login_attempt(
                    user.id, False, None, ip_address, user_agent,
                    "No face data found for account"
                )
                return False, "No face data found for this account"
            
            # Compare faces
            is_match, similarity = face_recognition.is_same_person(
                face_embedding, stored_embedding, self.face_threshold
            )
            
            if is_match:
                # Log successful attempt
                self.log_login_attempt(
                    user.id, True, similarity, ip_address, user_agent
                )
                # Update last login
                user.update_last_login()
                db.session.commit()
                return True, {"user": user, "similarity": similarity}
            else:
                # Log failed attempt
                self.log_login_attempt(
                    user.id, False, similarity, ip_address, user_agent,
                    f"Face does not match. Similarity: {similarity:.2f}"
                )
                return False, f"Face does not match. Similarity: {similarity:.2f}"
            
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    def get_user_by_email(self, email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()

# Global instance
auth_service = AuthService()