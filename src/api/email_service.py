import os 
from email.message import EmailMessage
from typing import Optional

import aiosmtplib

async def send_email(
        to: str,
        subject: str,
        text: Optional[str] = None,
) -> None:
    msg = EmailMessage()
    msg["From"] = os.environ["MAIL_FROM"]
    msg["To"] = to
    msg["Subject"] = subject

    msg.set_content(text or " ")
    
    await aiosmtplib.send(
        msg,
        hostname=os.environ["SMTP_HOST"],
        port=int(os.environ.get("SMTP_PORT", "587")),
        username=os.environ["SMTP_USER"],
        password=os.environ["SMTP_PASS"],
        start_tls=True,
        timeout=15,
    )