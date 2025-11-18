"""Celery tasks for email notifications.

This module provides asynchronous email notification tasks for:
- Share received notifications
- Share imported notifications
- System notifications
"""

from __future__ import annotations

import asyncio
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Template
from sqlalchemy import select

from ..db import dispose_engine, session_scope
from ..models.sharing import UserShare
from ..settings import get_settings
from ..telemetry import bind_request_context, clear_context, get_logger, new_request_id
from ..worker import celery_app

logger = get_logger("dealbrain.tasks.notifications")

SEND_SHARE_EMAIL_TASK_NAME = "notifications.send_share_email"

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render Jinja2 template with context.

    Args:
        template_name: Template filename (e.g., 'share_notification.html')
        context: Template context variables

    Returns:
        Rendered template string
    """
    template_path = TEMPLATES_DIR / template_name
    with open(template_path, "r") as f:
        template_content = f.read()

    template = Template(template_content)
    return template.render(**context)


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    from_email: str,
    from_name: str,
    smtp_config: dict[str, Any]
) -> None:
    """Send email via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (fallback)
        from_email: Sender email address
        from_name: Sender display name
        smtp_config: SMTP configuration dict with keys:
            - host: SMTP server hostname
            - port: SMTP server port
            - user: SMTP username (optional)
            - password: SMTP password (optional)
            - use_tls: Use TLS (bool)
            - use_ssl: Use SSL (bool)
            - timeout: Connection timeout in seconds

    Raises:
        smtplib.SMTPException: If email sending fails
    """
    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Attach text and HTML parts
    text_part = MIMEText(text_body, "plain", "utf-8")
    html_part = MIMEText(html_body, "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    # Send email
    smtp_class = smtplib.SMTP_SSL if smtp_config.get("use_ssl") else smtplib.SMTP

    with smtp_class(
        smtp_config["host"],
        smtp_config["port"],
        timeout=smtp_config.get("timeout", 10)
    ) as server:
        if smtp_config.get("use_tls") and not smtp_config.get("use_ssl"):
            server.starttls()

        if smtp_config.get("user") and smtp_config.get("password"):
            server.login(smtp_config["user"], smtp_config["password"])

        server.send_message(msg)

    logger.info(f"Email sent successfully to {to_email}")


async def _send_share_notification_email_async(share_id: int) -> dict[str, Any]:
    """Async implementation of share notification email sending.

    Args:
        share_id: UserShare ID

    Returns:
        Dict with keys: success, share_id, recipient_email, error (if failed)

    Raises:
        ValueError: If UserShare not found
    """
    correlation_id = new_request_id()
    bind_request_context(
        correlation_id,
        task=SEND_SHARE_EMAIL_TASK_NAME,
        share_id=share_id
    )
    logger.info("notifications.email.start", share_id=share_id)

    settings = get_settings()

    # Check if email is enabled
    if not settings.email.enabled:
        logger.info(
            "notifications.email.disabled",
            share_id=share_id,
            message="Email notifications are disabled in settings"
        )
        return {
            "success": False,
            "share_id": share_id,
            "error": "Email notifications disabled"
        }

    async with session_scope() as session:
        # 1. Load UserShare with relationships
        stmt = (
            select(UserShare)
            .where(UserShare.id == share_id)
        )
        result = await session.execute(stmt)
        share = result.scalar_one_or_none()

        if not share:
            raise ValueError(f"UserShare {share_id} not found")

        # 2. Extract data for email template
        sender_name = share.sender.display_name or share.sender.username
        recipient_email = share.recipient.email

        if not recipient_email:
            logger.warning(
                "notifications.email.no_recipient_email",
                share_id=share_id,
                recipient_id=share.recipient_id
            )
            return {
                "success": False,
                "share_id": share_id,
                "error": "Recipient has no email address"
            }

        listing = share.listing
        listing_name = listing.name if hasattr(listing, 'name') else f"Listing #{listing.id}"

        # Build template context
        context = {
            "sender_name": sender_name,
            "recipient_name": share.recipient.display_name or share.recipient.username,
            "listing_name": listing_name,
            "listing_price": f"{listing.base_price:.2f}" if hasattr(listing, 'base_price') else "N/A",
            "listing_score": f"{listing.composite_score:.1f}" if hasattr(listing, 'composite_score') and listing.composite_score else None,
            "listing_manufacturer": getattr(listing, 'manufacturer', None),
            "listing_cpu": getattr(listing, 'cpu_model', None),
            "listing_ram": getattr(listing, 'ram_gb', None),
            "listing_storage": getattr(listing, 'storage_gb', None),
            "message": share.message,
            "share_url": f"{settings.api_host}:{settings.api_port}/deals/shared/{share.share_token}",
            "share_token": share.share_token,
        }

        # 3. Render email templates
        try:
            html_body = render_template("share_notification.html", context)
            text_body = render_template("share_notification.txt", context)
        except Exception as e:
            logger.error(
                "notifications.email.template_error",
                share_id=share_id,
                error=str(e),
                exc_info=True
            )
            return {
                "success": False,
                "share_id": share_id,
                "error": f"Template rendering failed: {e}"
            }

        # 4. Send email
        try:
            smtp_config = {
                "host": settings.email.smtp_host,
                "port": settings.email.smtp_port,
                "user": settings.email.smtp_user,
                "password": settings.email.smtp_password,
                "use_tls": settings.email.smtp_tls,
                "use_ssl": settings.email.smtp_ssl,
                "timeout": settings.email.timeout_seconds,
            }

            send_email(
                to_email=recipient_email,
                subject=f"{sender_name} shared a deal with you",
                html_body=html_body,
                text_body=text_body,
                from_email=settings.email.from_email,
                from_name=settings.email.from_name,
                smtp_config=smtp_config
            )

            logger.info(
                "notifications.email.success",
                share_id=share_id,
                recipient_email=recipient_email
            )

            return {
                "success": True,
                "share_id": share_id,
                "recipient_email": recipient_email
            }

        except Exception as e:
            logger.error(
                "notifications.email.send_error",
                share_id=share_id,
                recipient_email=recipient_email,
                error=str(e),
                exc_info=True
            )
            return {
                "success": False,
                "share_id": share_id,
                "recipient_email": recipient_email,
                "error": f"Email sending failed: {e}"
            }


@celery_app.task(
    name=SEND_SHARE_EMAIL_TASK_NAME,
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_share_notification_email(self, share_id: int) -> dict[str, Any]:
    """Celery task to send share notification email.

    This task is triggered when a user shares a deal with another user.
    It sends an email notification with deal details and a link to view the share.

    Args:
        share_id: UserShare ID

    Returns:
        Dict with result info: success, share_id, recipient_email, error

    Raises:
        ValueError: If UserShare not found (will not retry)

    Retries:
        Automatically retries up to 3 times with 60 second delay on transient errors
    """
    try:
        # Run async function in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                _send_share_notification_email_async(share_id)
            )
            return result
        finally:
            loop.close()
            # Dispose engine to avoid event loop issues
            asyncio.run(dispose_engine())
            clear_context()

    except ValueError as e:
        # Don't retry if share not found
        logger.error(f"Share {share_id} not found, not retrying: {e}")
        raise

    except smtplib.SMTPException as e:
        # Retry on SMTP errors
        logger.error(
            f"SMTP error sending email for share {share_id}: {e}, "
            f"retrying in 60 seconds..."
        )
        raise self.retry(exc=e)

    except Exception as e:
        # Retry on other errors
        logger.error(
            f"Unexpected error sending email for share {share_id}: {e}, "
            f"retrying in 60 seconds..."
        )
        raise self.retry(exc=e)
