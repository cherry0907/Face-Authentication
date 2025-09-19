from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, validate_csrf, CSRFError
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import db, User
from auth import auth_service
from email_service import email_service
from face_recognition import face_recognition
import secrets

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///face_auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
auth_service.app = app

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

def cleanup_expired_accounts():
    """Clean up expired unverified accounts"""
    try:
        with app.app_context():
            # Find expired unverified accounts (older than 1 hour)
            expired_threshold = datetime.utcnow() - timedelta(hours=1)
            expired_users = User.query.filter(
                User.is_verified == False,
                User.created_at < expired_threshold
            ).all()
            
            for user in expired_users:
                # Delete associated files
                if user.photo_path and os.path.exists(user.photo_path):
                    try:
                        os.remove(user.photo_path)
                    except Exception:
                        pass  # Continue even if file deletion fails
                
                db.session.delete(user)
            
            if expired_users:
                db.session.commit()
                print(f"Cleaned up {len(expired_users)} expired unverified accounts")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass

# Schedule cleanup to run every hour (you can run this as a background task)
import threading
import time

def periodic_cleanup():
    """Run cleanup periodically"""
    while True:
        time.sleep(3600)  # Wait 1 hour
        cleanup_expired_accounts()

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    """Home page - redirect based on login status"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        face_image = request.form.get('face_image', '')
        
        # Validate input
        if not all([name, email, password, face_image]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            })
        
        if len(name) < 2:
            return jsonify({
                'success': False,
                'message': 'Name must be at least 2 characters long'
            })
        
        if len(password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            })
        
        # Check if email already exists (including unverified accounts)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.is_verified:
                return jsonify({
                    'success': False,
                    'message': 'Email already registered with a verified account'
                })
            else:
                # Delete the existing unverified account to allow re-registration
                if existing_user.photo_path and os.path.exists(existing_user.photo_path):
                    try:
                        os.remove(existing_user.photo_path)
                    except:
                        pass  # Continue even if file deletion fails
                
                db.session.delete(existing_user)
                db.session.commit()
        
        # Register user
        success, result = auth_service.register_user(name, email, password, face_image)
        
        if success:
            # Send OTP email
            otp = result['otp']
            user_id = result['user_id']
            
            email_success, email_message = email_service.send_otp_email(email, name, otp)
            
            if not email_success:
                # If email fails, delete the user and return error
                user = User.query.get(user_id)
                if user:
                    # Delete associated files
                    if user.photo_path and os.path.exists(user.photo_path):
                        try:
                            os.remove(user.photo_path)
                        except:
                            pass  # Continue even if file deletion fails
                    
                    db.session.delete(user)
                    db.session.commit()
                
                return jsonify({
                    'success': False,
                    'message': f'Failed to send verification email: {email_message}'
                })
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'message': 'Account created! Check your email for verification code.'
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        })

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and activate account"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        user_id = request.form.get('user_id')
        otp = request.form.get('otp', '').strip()
        
        if not user_id or not otp:
            return jsonify({
                'success': False,
                'message': 'User ID and OTP are required'
            })
        
        if len(otp) != 6 or not otp.isdigit():
            return jsonify({
                'success': False,
                'message': 'OTP must be 6 digits'
            })
        
        # Verify OTP
        success, message = auth_service.verify_otp_and_activate(user_id, otp)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'OTP verification failed: {str(e)}'
        })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        # Get form data
        email = request.form.get('email', '').strip().lower()
        face_image = request.form.get('face_image', '')
        
        # Validate input
        if not email or not face_image:
            return jsonify({
                'success': False,
                'message': 'Email and face image are required'
            })
        
        # Authenticate user (face verification only)
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.environ.get('HTTP_USER_AGENT', '')
        success, result = auth_service.authenticate_user(email, face_image, ip_address, user_agent)
        
        if success:
            user = result['user']
            similarity = result['similarity']
            
            # Generate login OTP
            otp = auth_service.generate_otp()
            otp_hash = auth_service.hash_otp(otp)
            
            # Store login OTP in session (temporary)
            session['login_otp'] = otp_hash
            session['login_user_id'] = user.id
            session['login_similarity'] = similarity
            session['login_otp_expires'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            
            # Send login OTP email
            email_success, email_message = email_service.send_login_otp_email(user.email, user.name, otp)
            
            if email_success:
                return jsonify({
                    'success': True,
                    'message': 'Face verified! Check your email for the login code.',
                    'show_otp': True
                })
            else:
                # Clear session data if email fails
                session.pop('login_otp', None)
                session.pop('login_user_id', None)
                session.pop('login_similarity', None)
                session.pop('login_otp_expires', None)
                
                return jsonify({
                    'success': False,
                    'message': f'Failed to send login code: {email_message}'
                })
        else:
            return jsonify({
                'success': False,
                'message': result
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        })

@app.route('/verify-login-otp', methods=['POST'])
def verify_login_otp():
    """Verify login OTP and complete login"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        otp = request.form.get('otp', '').strip()
        
        if not otp or len(otp) != 6:
            return jsonify({
                'success': False,
                'message': 'Valid 6-digit OTP is required'
            })
        
        # Check session data
        if 'login_otp' not in session or 'login_user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Login session expired. Please try again.'
            })
        
        # Check OTP expiry
        expires_str = session.get('login_otp_expires')
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > expires:
                # Clear session data
                session.pop('login_otp', None)
                session.pop('login_user_id', None)
                session.pop('login_similarity', None)
                session.pop('login_otp_expires', None)
                return jsonify({
                    'success': False,
                    'message': 'OTP expired. Please try logging in again.'
                })
        
        # Verify OTP
        if not auth_service.verify_otp(otp, session['login_otp']):
            return jsonify({
                'success': False,
                'message': 'Invalid OTP'
            })
        
        # Get user and complete login
        user = auth_service.get_user_by_id(session['login_user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            })
        
        similarity = session.get('login_similarity', 0)
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.name
        
        # Update last login
        user.update_last_login()
        db.session.commit()
        
        # Send login alert email
        email_service.send_login_alert(
            user.email, 
            user.name, 
            user.last_login_at,
            similarity
        )
        
        # Clear login OTP session data
        session.pop('login_otp', None)
        session.pop('login_user_id', None)
        session.pop('login_similarity', None)
        session.pop('login_otp_expires', None)
        
        return jsonify({
            'success': True,
            'message': 'Login successful!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'OTP verification failed: {str(e)}'
        })

@app.route('/security-report')
def security_report():
    """User security report page"""
    if 'user_id' not in session:
        flash('Please log in to access security report', 'error')
        return redirect(url_for('login'))
    
    try:
        user = auth_service.get_user_by_id(session['user_id'])
        if not user or not user.is_verified:
            session.clear()
            flash('User not found or not verified', 'error')
            return redirect(url_for('login'))
        
        # Get login history
        login_history = auth_service.get_user_login_history(user.id)
        
        return render_template('security_report.html', user=user, login_history=login_history)
        
    except Exception as e:
        flash(f'Error loading security report: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/account-settings')
def account_settings():
    """User account settings page"""
    if 'user_id' not in session:
        flash('Please log in to access account settings', 'error')
        return redirect(url_for('login'))
    
    try:
        user = auth_service.get_user_by_id(session['user_id'])
        if not user or not user.is_verified:
            session.clear()
            flash('User not found or not verified', 'error')
            return redirect(url_for('login'))
        
        return render_template('account_settings.html', user=user)
        
    except Exception as e:
        flash(f'Error loading account settings: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/update-face-request', methods=['POST'])
def update_face_request():
    """Request to update face data - sends OTP"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.json.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        user = auth_service.get_user_by_id(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        face_image = request.json.get('face_image', '')
        if not face_image:
            return jsonify({'success': False, 'message': 'Face image is required'})
        
        # Validate face image
        face_embedding = face_recognition.get_face_embedding(face_image)
        if face_embedding is None:
            return jsonify({'success': False, 'message': 'No face detected in image'})
        
        # Generate OTP for verification
        otp = auth_service.generate_otp()
        otp_hash = auth_service.hash_otp(otp)
        
        # Store temporary data in session
        session['update_face_data'] = face_image
        session['update_face_otp'] = otp_hash
        session['update_face_expires'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        
        # Send OTP email
        email_success, email_message = email_service.send_otp_email(user.email, user.name, otp)
        
        if email_success:
            return jsonify({'success': True, 'message': 'Verification code sent successfully'})
        else:
            return jsonify({'success': False, 'message': f'Failed to send verification code: {email_message}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'})


@app.route('/update-face-confirm', methods=['POST'])
def update_face_confirm():
    """Confirm face data update with OTP"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.json.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        user = auth_service.get_user_by_id(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        otp = request.json.get('otp', '').strip()
        if not otp or len(otp) != 6:
            return jsonify({'success': False, 'message': 'Valid 6-digit OTP is required'})
        
        # Check session data
        if 'update_face_otp' not in session or 'update_face_data' not in session:
            return jsonify({'success': False, 'message': 'Update session expired. Please try again'})
        
        # Check OTP expiry
        expires_str = session.get('update_face_expires')
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > expires:
                # Clear session data
                session.pop('update_face_data', None)
                session.pop('update_face_otp', None)
                session.pop('update_face_expires', None)
                return jsonify({'success': False, 'message': 'OTP expired. Please try again'})
        
        # Verify OTP
        if not auth_service.verify_otp(otp, session['update_face_otp']):
            return jsonify({'success': False, 'message': 'Invalid OTP'})
        
        # Update face data
        face_image = session['update_face_data']
        face_embedding = face_recognition.get_face_embedding(face_image)
        
        if face_embedding is None:
            return jsonify({'success': False, 'message': 'Failed to process face data'})
        
        # Save new face image
        photo_filename = f"{user.email.replace('@', '_').replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        photo_path = face_recognition.save_face_image(face_image, photo_filename)
        
        # Update user
        user.set_embedding(face_embedding)
        if photo_path:
            user.photo_path = photo_path
        
        db.session.commit()
        
        # Clear session data
        session.pop('update_face_data', None)
        session.pop('update_face_otp', None)
        session.pop('update_face_expires', None)
        
        return jsonify({'success': True, 'message': 'Face data updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating face data: {str(e)}'})


@app.route('/delete-account-request', methods=['POST'])
def delete_account_request():
    """Request account deletion - sends OTP"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.json.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        user = auth_service.get_user_by_id(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Generate OTP for deletion
        otp = auth_service.generate_otp()
        otp_hash = auth_service.hash_otp(otp)
        
        # Store deletion OTP in session
        session['delete_account_otp'] = otp_hash
        session['delete_account_expires'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        
        # Send deletion OTP email
        email_success, email_message = email_service.send_deletion_otp_email(user.email, user.name, otp)
        
        if email_success:
            return jsonify({'success': True, 'message': 'Deletion code sent successfully'})
        else:
            return jsonify({'success': False, 'message': f'Failed to send deletion code: {email_message}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing deletion request: {str(e)}'})


@app.route('/delete-account-confirm', methods=['POST'])
def delete_account_confirm():
    """Confirm account deletion with OTP"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.json.get('csrf_token'))
        except CSRFError:
            return jsonify({
                'success': False,
                'message': 'Security token expired. Please refresh the page and try again.'
            }), 400
        
        user = auth_service.get_user_by_id(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        otp = request.json.get('otp', '').strip()
        if not otp or len(otp) != 6:
            return jsonify({'success': False, 'message': 'Valid 6-digit OTP is required'})
        
        # Check session data
        if 'delete_account_otp' not in session:
            return jsonify({'success': False, 'message': 'Deletion session expired. Please try again'})
        
        # Check OTP expiry
        expires_str = session.get('delete_account_expires')
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > expires:
                session.pop('delete_account_otp', None)
                session.pop('delete_account_expires', None)
                return jsonify({'success': False, 'message': 'OTP expired. Please try again'})
        
        # Verify OTP
        if not auth_service.verify_otp(otp, session['delete_account_otp']):
            return jsonify({'success': False, 'message': 'Invalid OTP'})
        
        # Delete user account
        user_email = user.email
        user_name = user.name
        
        # Delete associated files
        if user.photo_path and os.path.exists(user.photo_path):
            try:
                os.remove(user.photo_path)
            except:
                pass  # Continue even if file deletion fails
        
        # Delete user (cascade will handle login history)
        db.session.delete(user)
        db.session.commit()
        
        # Clear session
        session.clear()
        
        # Send deletion confirmation email
        email_service.send_account_deleted_email(user_email, user_name)
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting account: {str(e)}'})


@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    try:
        user = auth_service.get_user_by_id(session['user_id'])
        if not user or not user.is_verified:
            session.clear()
            flash('User not found or not verified', 'error')
            return redirect(url_for('login'))
        
        return render_template('dashboard.html', user=user)
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Internal server error'), 500

@app.errorhandler(413)
def too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'success': False,
        'message': 'File too large. Please try with a smaller image.'
    }), 413

# CSRF error handler
@app.errorhandler(400)
def csrf_error(error):
    """Handle CSRF errors"""
    if 'CSRF' in str(error):
        return jsonify({
            'success': False,
            'message': 'Security token expired. Please refresh the page and try again.'
        }), 400
    return str(error), 400

# Custom template filters
@app.template_filter('datetime')
def datetime_filter(dt, format='%B %d, %Y at %I:%M %p'):
    """Format datetime for templates with timezone conversion"""
    if dt is None:
        return 'Never'
    
    # Convert UTC to local time
    import time
    from datetime import timezone, timedelta
    
    # Get local timezone offset
    local_offset = time.timezone if (time.daylight == 0) else time.altzone
    local_tz = timezone(timedelta(seconds=-local_offset))
    
    # Convert UTC datetime to local timezone
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc)
    
    local_dt = dt.astimezone(local_tz)
    return local_dt.strftime(format)

@app.template_filter('datetime_utc')
def datetime_utc_filter(dt, format='%B %d, %Y at %I:%M %p UTC'):
    """Format datetime for templates keeping UTC"""
    if dt is None:
        return 'Never'
    return dt.strftime(format)

# Context processors
@app.context_processor
def inject_csrf_token():
    """Inject CSRF token into all templates"""
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

@app.context_processor
def inject_user():
    """Inject current user into templates"""
    user = None
    if 'user_id' in session:
        user = auth_service.get_user_by_id(session['user_id'])
    return dict(current_user=user)

if __name__ == '__main__':
    # Create database tables
    create_tables()
    
    # Run the app
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=os.getenv('FLASK_ENV') == 'development'
    )