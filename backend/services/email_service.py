import requests
import os
import logging

email_logger = logging.getLogger('email_service')

def send_match_notification_email(sender_item, receiver_item, match, app_config):
    api_key = os.environ.get('RESEND_API_KEY')
    # Make sure this matches your verified Resend email/domain
    from_email = os.environ.get('EMAIL_FROM', 'onboarding@resend.dev') 
    receiver_email = receiver_item.get('user', {}).get('email')
    
    if not api_key or not receiver_email:
        email_logger.error("Email configuration missing.")
        return

    score_percentage = round(match.get('score', 0) * 100)
    score_color = '#10b981' if score_percentage >= 80 else '#f59e0b'
    
    # Your beautiful custom HTML template
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Good news! We found a potential match!</h2>
            <p>Our AI system has identified a <b>{score_percentage}%</b> match for the item you reported.</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Match Metrics</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Score</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Overall Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {score_color}; font-weight: bold;">{score_percentage}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Image Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{round(match.get('imageScore', 0) * 100)}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Text Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{round(match.get('textScore', 0) * 100)}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Location Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{round(match.get('locationScore', 0) * 100)}%</td>
                </tr>
            </table>
            
            <h3>Item Details of the Match:</h3>
            <p><b>Item:</b> {sender_item.get('title')} ({sender_item.get('type', '').capitalize()})</p>
            <p><b>Reported by:</b> {sender_item.get('user', {}).get('name', 'User')}</p>
            <p><b>Contact Email:</b> <a href="mailto:{sender_item.get('user', {}).get('email')}">{sender_item.get('user', {}).get('email')}</a></p>
            <p><i>Please reach out directly to the other party to arrange verification and recovery.</i></p>

            <p>Thank you for using Lost & Found AI.</p>
        </body>
    </html>
    """

    payload = {
        "from": from_email,
        "to": [receiver_email],
        "subject": f"✅ Potential Match Found: Your {sender_item.get('title')} might be a match!",
        "html": html_content
    }
    
    try:
        response = requests.post("https://api.resend.com/emails", 
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, 
                                 json=payload)
        if response.status_code == 200:
            email_logger.info(f"Successfully sent match email to {receiver_email}")
        else:
            email_logger.error(f"API Error: {response.text}")
    except Exception as e:
        email_logger.error(f"Failed to send email: {e}")