import requests
import os
import logging

email_logger = logging.getLogger('email_service')

def send_match_notification_email(sender_item, receiver_item, match, app_config):
    """
    Sends a formatted match notification email via Resend HTTP API.
    This bypasses SMTP firewall restrictions on Render.
    """
    
    # Use environment variables
    api_key = os.environ.get('RESEND_API_KEY')
    from_email = os.environ.get('EMAIL_FROM', 'onboarding@resend.dev')
    receiver_email = receiver_item.get('user', {}).get('email')
    
    if not api_key or not receiver_email:
        email_logger.error("Resend API Key or receiver email missing.")
        return

    score_percentage = round(match.get('score', 0) * 100)
    
    html_content = f"""
    <html>
        <body>
            <h2>Good news! We found a potential match!</h2>
            <p>Our AI system has identified a <b>{score_percentage}%</b> match for the item you reported.</p>
            <p><b>Item:</b> {sender_item.get('title')}</p>
            <p><b>Contact:</b> {sender_item.get('user', {}).get('email')}</p>
        </body>
    </html>
    """

    resend_url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": from_email,
        "to": [receiver_email],
        "subject": f"✅ Potential Match Found: {sender_item.get('title')}",
        "html": html_content
    }
    
    try:
        email_logger.info(f"Attempting to send API email to {receiver_email}...")
        response = requests.post(resend_url, headers=headers, json=payload)
        if response.status_code == 200:
            email_logger.info("Successfully sent match email via API")
        else:
            email_logger.error(f"API Error: {response.text}")
    except Exception as e:
        email_logger.error(f"Failed to send email: {e}")