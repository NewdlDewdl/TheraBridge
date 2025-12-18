"""
Email service for sending verification and notification emails

Supports multiple email providers: SendGrid, AWS SES, SMTP
"""

import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Email configuration from environment
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp")  # sendgrid, ses, smtp
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@therapybridge.com")
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class EmailService:
    """
    Email service for sending templated emails

    Supports:
    - Email verification
    - Password reset
    - Notification emails
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize email service with template directory"""
        self.template_dir = template_dir or Path("app/templates/emails")
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        self.provider = EMAIL_PROVIDER

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send email using configured provider

        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text body (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if self.provider == "sendgrid":
                return await self._send_via_sendgrid(to, subject, html_body, text_body)
            elif self.provider == "ses":
                return await self._send_via_ses(to, subject, html_body, text_body)
            elif self.provider == "smtp":
                return await self._send_via_smtp(to, subject, html_body, text_body)
            else:
                logger.warning(f"EMAIL PROVIDER NOT CONFIGURED - Email would be sent to {to}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body preview: {html_body[:200]}...")
                return True  # Mock success in development

        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str]
    ) -> bool:
        """Send email via SendGrid API"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=EMAIL_FROM,
                to_emails=to,
                subject=subject,
                html_content=html_body,
                plain_text_content=text_body
            )

            sg = SendGridAPIClient(EMAIL_API_KEY)
            response = sg.send(message)

            logger.info(f"Email sent via SendGrid: {to} (status: {response.status_code})")
            return response.status_code < 300

        except Exception as e:
            logger.error(f"SendGrid email failed: {e}", exc_info=True)
            return False

    async def _send_via_ses(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str]
    ) -> bool:
        """Send email via AWS SES"""
        try:
            import boto3

            ses_client = boto3.client('ses')

            body_dict = {}
            if html_body:
                body_dict['Html'] = {'Data': html_body}
            if text_body:
                body_dict['Text'] = {'Data': text_body}

            response = ses_client.send_email(
                Source=EMAIL_FROM,
                Destination={'ToAddresses': [to]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': body_dict
                }
            )

            logger.info(f"Email sent via AWS SES: {to}")
            return True

        except Exception as e:
            logger.error(f"AWS SES email failed: {e}", exc_info=True)
            return False

    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str]
    ) -> bool:
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EMAIL_FROM
            msg['To'] = to

            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USER and SMTP_PASSWORD:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent via SMTP: {to}")
            return True

        except Exception as e:
            logger.error(f"SMTP email failed: {e}", exc_info=True)
            return False

    async def send_verification_email(
        self,
        to: str,
        user_name: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification email

        Args:
            to: User email address
            user_name: User's name
            verification_token: Verification token

        Returns:
            True if sent successfully
        """
        verification_url = f"{FRONTEND_URL}/auth/verify?token={verification_token}"

        context = {
            'user_name': user_name,
            'verification_url': verification_url,
            'frontend_url': FRONTEND_URL
        }

        try:
            template = self.env.get_template('verification.html')
            html_body = template.render(**context)

            text_body = f"""
Hi {user_name},

Welcome to TherapyBridge! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Best regards,
The TherapyBridge Team
            """.strip()

            return await self.send_email(
                to=to,
                subject="Verify your TherapyBridge account",
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            logger.error(f"Failed to send verification email: {e}", exc_info=True)
            return False

    async def send_password_reset_email(
        self,
        to: str,
        user_name: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email

        Args:
            to: User email address
            user_name: User's name
            reset_token: Password reset token

        Returns:
            True if sent successfully
        """
        reset_url = f"{FRONTEND_URL}/auth/reset-password?token={reset_token}"

        context = {
            'user_name': user_name,
            'reset_url': reset_url,
            'frontend_url': FRONTEND_URL
        }

        try:
            template = self.env.get_template('password_reset.html')
            html_body = template.render(**context)

            text_body = f"""
Hi {user_name},

We received a request to reset your password. Click the link below to create a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The TherapyBridge Team
            """.strip()

            return await self.send_email(
                to=to,
                subject="Reset your TherapyBridge password",
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}", exc_info=True)
            return False


def get_email_service() -> EmailService:
    """FastAPI dependency to provide email service"""
    return EmailService()
