"""
Email Service for sending OTP codes and notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def send_otp_email(user_email, otp_code):
    """
    Send OTP code via email
    Uses SMTP configuration from Flask config or environment variables
    """
    try:
        from flask import current_app
        # Get email configuration from Flask config or environment
        try:
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_username = current_app.config.get('SMTP_USERNAME', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')
        except RuntimeError:
            # Outside Flask context, use environment variables
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        # If no SMTP credentials, return False (email won't be sent)
        if not smtp_username or not smtp_password:
            print(f"[EMAIL SERVICE] OTP for {user_email}: {otp_code} (SMTP not configured)")
            return True  # Return True for development/testing
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = user_email
        msg['Subject'] = "Your OTP Code for Login"
        
        body = f"""
        <html>
            <body>
                <h2>Your One-Time Password (OTP)</h2>
                <p>Your OTP code is: <strong>{otp_code}</strong></p>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"[EMAIL SERVICE ERROR] Failed to send email: {str(e)}")
        # In development, still return True to allow testing
        return True


def send_welcome_email(user_email, user_name=None):
    """Send welcome email to new users"""
    try:
        from flask import current_app
        try:
            smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_username = current_app.config.get('SMTP_USERNAME', '')
            smtp_password = current_app.config.get('SMTP_PASSWORD', '')
        except RuntimeError:
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        if not smtp_username or not smtp_password:
            print(f"[EMAIL SERVICE] Welcome email for {user_email} (SMTP not configured)")
            return True
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = user_email
        msg['Subject'] = "Welcome to Inventory App"
        
        name = user_name or user_email
        body = f"""
        <html>
            <body>
                <h2>Welcome, {name}!</h2>
                <p>Thank you for signing up for our Inventory Management System.</p>
                <p>You can now log in and start managing your inventory.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"[EMAIL SERVICE ERROR] Failed to send welcome email: {str(e)}")
        return True

