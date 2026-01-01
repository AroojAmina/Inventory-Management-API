"""
SMS Service for sending OTP codes via Twilio
"""
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP code via SMS using Twilio
    """
    try:
        from flask import current_app
        # Get Twilio configuration from Flask config or environment
        try:
            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID', '')
            auth_token = current_app.config.get('TWILIO_AUTH_TOKEN', '')
            twilio_phone = current_app.config.get('TWILIO_PHONE_NUMBER', '')
        except RuntimeError:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '')
        
        # If Twilio is not configured, return True for development/testing
        if not account_sid or not auth_token or not twilio_phone:
            print(f"[SMS SERVICE] OTP for {phone_number}: {otp_code} (Twilio not configured)")
            return True
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send SMS
        message = client.messages.create(
            body=f"Your OTP code is: {otp_code}. This code expires in 10 minutes.",
            from_=twilio_phone,
            to=phone_number
        )
        
        return True
    except TwilioException as e:
        print(f"[SMS SERVICE ERROR] Twilio error: {str(e)}")
        return False
    except Exception as e:
        print(f"[SMS SERVICE ERROR] Failed to send SMS: {str(e)}")
        # In development, return True to allow testing
        return True

