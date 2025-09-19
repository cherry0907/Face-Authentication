import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_otp_email(self, to_email, name, otp):
        """Send OTP verification email"""
        subject = "Verify Your Account - Face Authentication App"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .otp-code {{
                    background-color: #4CAF50;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    margin: 20px 0;
                    letter-spacing: 3px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Account Verification</h1>
                    <h2>Welcome, {name}!</h2>
                </div>
                
                <p>Thank you for registering with our Face Authentication App.</p>
                <p>Please use the following One-Time Password (OTP) to verify your account:</p>
                
                <div class="otp-code">{otp}</div>
                
                <div class="warning">
                    ⚠️ <strong>Important:</strong> This OTP will expire in 10 minutes.
                    Do not share this code with anyone.
                </div>
                
                <p>If you didn't request this verification, please ignore this email.</p>
                
                <div class="footer">
                    <p>Face Authentication App &copy; 2025</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Account Verification - Face Authentication App
        
        Welcome, {name}!
        
        Thank you for registering with our Face Authentication App.
        Please use the following One-Time Password (OTP) to verify your account:
        
        OTP: {otp}
        
        Important: This OTP will expire in 10 minutes.
        Do not share this code with anyone.
        
        If you didn't request this verification, please ignore this email.
        
        Face Authentication App © 2025
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_login_alert(self, to_email, name, login_time, similarity_score):
        """Send login notification email"""
        subject = "Login Alert - Face Authentication App"
        
        formatted_time = login_time.strftime("%B %d, %Y at %I:%M %p")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .login-info {{
                    background-color: #e8f5e8;
                    border-left: 4px solid #4CAF50;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .similarity-score {{
                    background-color: #f0f8ff;
                    border: 1px solid #87ceeb;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 15px 0;
                    text-align: center;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔓 Login Alert</h1>
                    <h2>Hello, {name}!</h2>
                </div>
                
                <p>Your account was successfully accessed using face authentication.</p>
                
                <div class="login-info">
                    <h3>Login Details:</h3>
                    <p><strong>Time:</strong> {formatted_time}</p>
                    <p><strong>Authentication Method:</strong> Face Recognition</p>
                </div>
                
                <div class="similarity-score">
                    <p><strong>Face Match Confidence:</strong> {similarity_score:.1%}</p>
                </div>
                
                <p>If this wasn't you, please contact support immediately.</p>
                
                <div class="footer">
                    <p>Face Authentication App &copy; 2025</p>
                    <p>This is an automated security notification.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Login Alert - Face Authentication App
        
        Hello, {name}!
        
        Your account was successfully accessed using face authentication.
        
        Login Details:
        Time: {formatted_time}
        Authentication Method: Face Recognition
        Face Match Confidence: {similarity_score:.1%}
        
        If this wasn't you, please contact support immediately.
        
        Face Authentication App © 2025
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_login_otp_email(self, to_email, name, otp):
        """Send login OTP verification email"""
        subject = "Login Verification Code - Face Authentication App"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .otp-code {{
                    background-color: #007bff;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    margin: 20px 0;
                    letter-spacing: 3px;
                }}
                .info {{
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                    color: #0c5460;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Login Verification</h1>
                    <h2>Hello, {name}!</h2>
                </div>
                
                <p>Someone is trying to log into your Face Authentication account.</p>
                <p>Your face has been verified. Please use the following code to complete your login:</p>
                
                <div class="otp-code">{otp}</div>
                
                <div class="info">
                    ℹ️ <strong>Security Notice:</strong> This verification code will expire in 10 minutes.
                    Never share this code with anyone.
                </div>
                
                <p>If this wasn't you, please ignore this email and consider changing your password.</p>
                
                <div class="footer">
                    <p>Face Authentication App &copy; 2025</p>
                    <p>This is an automated security message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Login Verification Code - Face Authentication App
        
        Hello, {name}!
        
        Someone is trying to log into your Face Authentication account.
        Your face has been verified. Please use the following code to complete your login:
        
        OTP: {otp}
        
        Security Notice: This verification code will expire in 10 minutes.
        Never share this code with anyone.
        
        If this wasn't you, please ignore this email and consider changing your password.
        
        Face Authentication App © 2025
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_deletion_otp_email(self, to_email, name, otp):
        """Send account deletion OTP email"""
        subject = "Account Deletion Verification - Face Authentication App"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .otp-code {{
                    background-color: #dc3545;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    margin: 20px 0;
                    letter-spacing: 3px;
                }}
                .warning {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Account Deletion Request</h1>
                    <h2>Hello, {name}</h2>
                </div>
                
                <p>You have requested to permanently delete your Face Authentication account.</p>
                <p>Please use the following One-Time Password (OTP) to confirm this action:</p>
                
                <div class="otp-code">{otp}</div>
                
                <div class="warning">
                    <strong>⚠️ CRITICAL WARNING:</strong><br>
                    This action is irreversible and will permanently delete:
                    <ul>
                        <li>Your account and profile information</li>
                        <li>All stored face recognition data</li>
                        <li>Your complete login history</li>
                        <li>All associated data</li>
                    </ul>
                    This OTP will expire in 10 minutes.
                </div>
                
                <p>If you did not request account deletion, please ignore this email and consider changing your account password.</p>
                
                <div class="footer">
                    <p>Face Authentication App &copy; 2025</p>
                    <p>This is an automated security message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Account Deletion Request - Face Authentication App
        
        Hello, {name}
        
        You have requested to permanently delete your Face Authentication account.
        Please use the following One-Time Password (OTP) to confirm this action:
        
        OTP: {otp}
        
        CRITICAL WARNING:
        This action is irreversible and will permanently delete:
        - Your account and profile information
        - All stored face recognition data
        - Your complete login history
        - All associated data
        
        This OTP will expire in 10 minutes.
        
        If you did not request account deletion, please ignore this email and consider changing your account password.
        
        Face Authentication App © 2025
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_account_deleted_email(self, to_email, name):
        """Send account deletion confirmation email"""
        subject = "Account Successfully Deleted - Face Authentication App"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .confirmation {{
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                    color: #0c5460;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Account Deleted</h1>
                    <h2>Goodbye, {name}</h2>
                </div>
                
                <div class="confirmation">
                    <h3>Your account has been permanently deleted</h3>
                    <p>All your data has been removed from our systems as requested.</p>
                </div>
                
                <p>This includes:</p>
                <ul>
                    <li>Your profile and account information</li>
                    <li>All face recognition data</li>
                    <li>Complete login history</li>
                    <li>All associated data</li>
                </ul>
                
                <p>Thank you for using Face Authentication App. We're sorry to see you go.</p>
                <p>If you have any feedback or concerns, please feel free to contact our support team.</p>
                
                <div class="footer">
                    <p>Face Authentication App &copy; 2025</p>
                    <p>This is the final automated message from your deleted account.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Account Successfully Deleted - Face Authentication App
        
        Goodbye, {name}
        
        Your account has been permanently deleted.
        All your data has been removed from our systems as requested.
        
        This includes:
        - Your profile and account information
        - All face recognition data
        - Complete login history
        - All associated data
        
        Thank you for using Face Authentication App. We're sorry to see you go.
        If you have any feedback or concerns, please feel free to contact our support team.
        
        Face Authentication App © 2025
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Global instance
email_service = EmailService()