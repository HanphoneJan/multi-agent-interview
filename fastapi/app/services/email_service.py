"""Email service for sending emails via SMTP"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import get_settings

settings = get_settings()


class EmailService:
    """Email service for sending verification codes and notifications"""

    @classmethod
    def _create_smtp_connection(cls):
        """Create SMTP connection based on settings"""
        if settings.SMTP_USE_SSL:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_USE_TLS:
                context = ssl.create_default_context()
                server.starttls(context=context)
        return server

    @classmethod
    def _is_configured(cls) -> bool:
        """Check if email service is properly configured"""
        return all([
            settings.SMTP_HOST,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM
        ])

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text content (optional, for fallback)

        Returns:
            True if sent successfully, False otherwise
        """
        if not cls._is_configured():
            print("[EmailService] SMTP not configured, skipping email send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_email

            # Add plain text part if provided
            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))

            # Add HTML part
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # Connect and send
            with cls._create_smtp_connection() as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                # Encode message to bytes to handle non-ASCII characters
                message_bytes = msg.as_bytes()
                server.sendmail(settings.SMTP_FROM, to_email, message_bytes)

            print(f"[EmailService] Email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"[EmailService] Failed to send email: {e}")
            return False

    @classmethod
    def send_verification_code(cls, to_email: str, code: str, expire_minutes: int = 10) -> bool:
        """
        Send verification code email

        Args:
            to_email: Recipient email address
            code: 6-digit verification code
            expire_minutes: Code expiration time in minutes

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "AI面试助手 - 邮箱验证码"

        html_body = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>邮箱验证码</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #3964fe, #5a7eff);
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    color: #ffffff;
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 16px;
                    color: #333333;
                    margin-bottom: 20px;
                }}
                .code-box {{
                    background-color: #f8f9fa;
                    border: 2px dashed #3964fe;
                    border-radius: 8px;
                    padding: 30px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .verification-code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #3964fe;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .expire-notice {{
                    font-size: 14px;
                    color: #666666;
                    margin-top: 20px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin-top: 30px;
                    font-size: 13px;
                    color: #856404;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #999999;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI面试助手</h1>
                </div>
                <div class="content">
                    <p class="greeting">您好，</p>
                    <p>您正在进行邮箱验证操作，请使用以下验证码完成验证：</p>

                    <div class="code-box">
                        <div class="verification-code">{code}</div>
                    </div>

                    <p class="expire-notice">
                        验证码有效期为 <strong>{expire_minutes} 分钟</strong>，请尽快完成验证。
                    </p>

                    <div class="warning">
                        <strong>安全提示：</strong>请勿将验证码透露给他人。如果这不是您的操作，请忽略此邮件。
                    </div>
                </div>
                <div class="footer">
                    <p>此邮件由 AI面试助手 系统自动发送，请勿回复。</p>
                    <p>&copy; 2026 AI面试助手. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        AI面试助手 - 邮箱验证码

        您好，

        您的验证码是：{code}

        验证码有效期为 {expire_minutes} 分钟，请尽快完成验证。

        安全提示：请勿将验证码透露给他人。如果这不是您的操作，请忽略此邮件。

        此邮件由 AI面试助手 系统自动发送，请勿回复。
        """

        return cls.send_email(to_email, subject, html_body, text_body)


# Global email service instance
email_service = EmailService()
