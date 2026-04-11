import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

# CONFIGURATION (Matching your app.py)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# The username should be your full Gmail address
SENDER_EMAIL = "appanagirisai7569@gmail.com"
# The App Password should be 16 characters (no spaces needed here, but usually shown with spaces)
SENDER_PASSWORD = "cniaeiafmvpgkvnu" 

def test_smtp():
    print(f"--- SMTP Diagnostic Tool ---")
    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    
    try:
        # Create message
        recipient = SENDER_EMAIL # Send to yourself for testing
        msg = MIMEMultipart()
        msg['From'] = f"Mukh Swasthya Test <{SENDER_EMAIL}>"
        msg['To'] = recipient
        msg['Subject'] = "Mukh Swasthya SMTP Test"
        
        body = "This is a test email to verify your Flask-Mail configuration is working correctly."
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and Send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1) # Show the raw SMTP conversation
        server.starttls()
        
        print("Authenticating...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        print(f"Sending test email to {recipient}...")
        server.send_message(msg)
        server.quit()
        
        print("\nSUCCESS: Email sent successfully!")
        print("If you still don't see it, check your SPAM folder.")
        
    except smtplib.SMTPAuthenticationError:
        print("\nERROR: Authentication Failed.")
        print("1. Ensure 'appanagirisai7569@gmail.com' is correct.")
        print("2. Ensure 'cniaeiafmvpgkvnu' is a valid 16-character App Password.")
        print("3. Regular account passwords do NOT work for Gmail SMTP.")
    except Exception as e:
        print(f"\nERROR: {str(e)}")

if __name__ == "__main__":
    test_smtp()
