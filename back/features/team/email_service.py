import smtplib
from email.message import EmailMessage

from flask import current_app, url_for


def send_asset_request_notification(asset_request):
    """Email the administrator when a technician submits an asset request.

    SMTP details are read from the app configuration. If mail is not configured,
    the request remains safely stored and the caller can show that clearly.
    """
    host = current_app.config.get("SMTP_HOST")
    recipient = current_app.config.get("ASSET_APPROVAL_EMAIL")
    sender = current_app.config.get("SMTP_FROM") or current_app.config.get("SMTP_USERNAME")
    if not host or not recipient or not sender:
        current_app.logger.warning("Asset request %s saved, but SMTP is not configured.", asset_request.id)
        return False

    data = asset_request.asset_data
    message = EmailMessage()
    message["Subject"] = f"Asset Verify: approval needed for {data.get('name', 'new asset')}"
    message["From"] = sender
    message["To"] = recipient
    requester = asset_request.requested_by
    message.set_content(
        "A technician submitted a new asset for approval.\n\n"
        f"Submitted by: {requester.username if requester else 'Unknown technician'}\n"
        f"Technician email: {requester.email if requester and requester.email else 'Not available'}\n"
        f"Asset: {data.get('name', '')}\n"
        f"Serial number: {data.get('serial_number', '')}\n"
        f"Department: {data.get('department', '')}\n"
        f"Location: {data.get('location', '')}\n\n"
        "Sign in to Asset Verify and open Team > Asset requests to approve or reject it.\n"
        f"Review requests: {url_for('team.asset_requests', _external=True)}"
    )

    port = current_app.config.get("SMTP_PORT", 587)
    username = current_app.config.get("SMTP_USERNAME")
    password = current_app.config.get("SMTP_PASSWORD")
    use_tls = current_app.config.get("SMTP_USE_TLS", True)
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException):
        current_app.logger.exception("Failed to email administrator about asset request %s.", asset_request.id)
        return False
    return True
