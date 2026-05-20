import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

email_logger = logging.getLogger('email_service')

def send_match_notification_email(sender_item, receiver_item, match, app_config):
    """Sends a formatted match notification email to users."""
    
    smtp_server = app_config.get('MAIL_SERVER')
    smtp_port = int(app_config.get('MAIL_PORT', 587))
    smtp_user = app_config.get('MAIL_USERNAME')
    smtp_password = app_config.get('MAIL_PASSWORD')
    smtp_sender = app_config.get('MAIL_DEFAULT_SENDER') or smtp_user
    receiver_email = receiver_item.get('user', {}).get('email')
    
    if not receiver_email:
        email_logger.error("No receiver email found.")
        return

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"✅ Potential Match Found: Your {sender_item['title']} might be a match!"
    msg['From'] = smtp_sender
    msg['To'] = receiver_email

    # Prepare data for the template
    score_percentage = round(match['score'] * 100)
    score_color = '#10b981' if score_percentage >= 80 else '#f59e0b'
    
    # --- YOUR HTML TEMPLATE INJECTED HERE ---
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
    msg.attach(MIMEText(html_content, 'html'))
    
    # --- SENDING LOGIC (Keep your existing SMTP or API logic here) ---
    try:
        email_logger.info(f"Sending email to {receiver_email}...")
        # (Your SMTP code here)
    except Exception as e:
        email_logger.error(f"Email failed: {e}")