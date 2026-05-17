import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

email_logger = logging.getLogger('email_service')

def send_match_notification_email(sender_item, receiver_item, match, app_config):
    """Sends a match notification email to one user about the other."""
    
    smtp_server = app_config.get('MAIL_SERVER')
    smtp_port = app_config.get('MAIL_PORT')
    smtp_user = app_config.get('MAIL_USERNAME')
    smtp_password = app_config.get('MAIL_PASSWORD')
    smtp_sender = app_config.get('MAIL_DEFAULT_SENDER')
    
    receiver_email = receiver_item.get('user', {}).get('email')
    
    if not smtp_server or not smtp_user or not smtp_password or not receiver_email:
        email_logger.error(f"Email configuration or receiver address missing. Skipping notification.")
        return

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"✅ Potential Match Found: Your {sender_item['title']} might be a match!"
    msg['From'] = smtp_sender
    msg['To'] = receiver_email

    score_percentage = round(match['score'] * 100)
    score_color = '#10b981' if score_percentage >= 80 else '#f59e0b'
    
    html_content = f"""
    <html>
        <body>
            <p>Hi {receiver_item.get('user', {}).get('name', 'User')},</p>
            <p>Good news! Our AI engine has found a potential match for your reported item, <b>{receiver_item['title']}</b>.</p>
            
            <p style="font-size: 18px; font-weight: bold; color: {score_color};">
                Overall Match Confidence: {score_percentage}%
            </p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; background-color: #f8f8f8; border: 1px solid #ddd;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Image Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{round(match['imageScore'] * 100)}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Text Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{round(match['textScore'] * 100)}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Location Match</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{round(match['locationScore'] * 100)}%</td>
                </tr>
            </table>
            
            <h3>Item Details of the Match:</h3>
            <p><b>Item:</b> {sender_item['title']} ({sender_item['type'].capitalize()})</p>
            <p><b>Reported by:</b> {sender_item.get('user', {}).get('name', 'User')}</p>
            <p><b>Contact Email:</b> <a href="mailto:{sender_item.get('user', {}).get('email')}">{sender_item.get('user', {}).get('email')}</a></p>
            <p><i>Please reach out directly to the other party to arrange verification and recovery.</i></p>

            <p>Thank you for using Lost & Found AI.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
        email_logger.info(f"SUCCESS: Match notification sent to {receiver_email}")
    except Exception as e:
        email_logger.error(f"Failed to send email to {receiver_email}: {e}")