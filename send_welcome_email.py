import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.settings")
django.setup()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

def send_welcome_email(user_email, user_name, login_url):
    # Email configuration from settings.py
    sender_email = settings.DEFAULT_FROM_EMAIL
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_HOST_USER
    smtp_password = settings.EMAIL_HOST_PASSWORD
    use_tls = settings.EMAIL_USE_TLS

    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Welcome to NextGen LMS"
    message["From"] = sender_email
    message["To"] = user_email

    # HTML content (unchanged)
    html_content = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to NextGen LMS</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f9fafb;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white;
            padding: 20px;
            text-align: center;
        }
        h1, h2, h3 {
            font-family: 'Playfair Display', serif;
            color: #1e3a8a;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
        }
        .button {
            display: inline-block;
            background-color: #c2410c;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }
        .button:hover {
            background-color: #9a3412;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #4b5563;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to NextGen LMS</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Welcome to the NextGen Learning Management System! We're excited to have you on board.</p>
            <h3>Getting Started</h3>
            <ol>
                <li>Log in to your account using your email and the temporary password: <strong>Test@123</strong></li>
                <li>Navigate to the "My Courses" section</li>
                <li>Start with the mandatory "Code of Conduct" course</li>
            </ol>
            <p>The "Code of Conduct" course has been automatically assigned to you. It's an important introduction to our learning community's standards and expectations.</p>
            <a href="{login_url}" class="button">Log In Now</a>
        </div>
        <div class="footer">
            <p>If you have any questions, please don't hesitate to contact our support team.</p>
            <p>&copy; 2024 NextGen LMS. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
    """

    # Replace placeholders
    html_content = html_content.replace("{user_name}", user_name)
    html_content = html_content.replace("{login_url}", login_url)

    # Attach HTML content
    message.attach(MIMEText(html_content, "html"))

    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, user_email, message.as_string())
        print(f"Welcome email sent successfully to {user_email}")
    except Exception as e:
        print(f"Error sending email to {user_email}: {str(e)}")

# Example usage
if __name__ == "__main__":
    new_user_email = "vea11sc.snehakumari@gmail.com"
    new_user_name = "Sneha Kumari"
    lms_login_url = "https://lms.learnknowdigital.com/en/user/login/"

    send_welcome_email(new_user_email, new_user_name, lms_login_url)