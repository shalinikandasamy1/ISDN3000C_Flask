import yagmail

SENDER_EMAIL = "isdnchkustphotobooth@gmail.com"
APP_PASSWORD = "idkr livz wsak xwej"  # Gmail App Password

yag = yagmail.SMTP(SENDER_EMAIL, APP_PASSWORD)

def send_photobooth_email(to_email, subject, body, attachments=None):
    yag.send(
        to=to_email,
        subject=subject,
        contents=body,
        attachments=attachments or []
    )
