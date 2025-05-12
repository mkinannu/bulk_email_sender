import os
import base64
import mimetypes
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the token.json file
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def authenticate():
    """Authenticate user using OAuth and return Gmail service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service
"below function is tested and its working"
def create_message_with_attachment(sender, to, subject, message_text, file_path):
    """Create an email message with attachment."""
    message = EmailMessage()
    message.set_content(message_text)
    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject

    # Attachment
    type_subtype, _ = mimetypes.guess_type(file_path)
    if not type_subtype:
        type_subtype = "application/octet-stream"
    maintype, subtype = type_subtype.split("/", 1)

    with open(file_path, "rb") as f:
        file_data = f.read()
        filename = os.path.basename(file_path)
        message.add_attachment(file_data, maintype, subtype, filename=filename)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": encoded_message}
def create_message_advanced(sender, to, subject, message_text, html_text, cc=None, bcc=None, attachments=None, inline_images=None):
    message = EmailMessage()
    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject
    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc

    # Set both plain text and HTML content
    message.set_content(message_text)
    if html_text:
        message.add_alternative(html_text, subtype='html')

    # Inline images
    if inline_images:
        for cid, img_path in inline_images.items():
            with open(img_path, 'rb') as img:
                img_data = img.read()
                maintype, subtype = mimetypes.guess_type(img_path)[0].split('/')
                message.get_payload()[-1].add_related(img_data, maintype=maintype, subtype=subtype, cid=f"<{cid}>")

    # File attachments
    if attachments:
        for file_path in attachments:
            if not os.path.exists(file_path):
                continue
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            maintype, subtype = mime_type.split('/', 1)

            with open(file_path, 'rb') as f:
                file_data = f.read()
            message.add_attachment(file_data, maintype, subtype, filename=os.path.basename(file_path))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}

def send_email():
    # service = authenticate()
    # message = create_message_with_attachment(
    #     sender="oneprojectdev@gmail.com",
    #     to="mdnannu04@gmail.com",
    #     subject="Hello with attachment",
    #     message_text="This is a test email with an attachment sent via Gmail API.",
    #     file_path="MKI.pdf"
    # )
    # send_message = service.users().messages().send(userId="me", body=message).execute()
    # print(f"✅ Email sent! Message ID: {send_message['id']}")

    
    service = authenticate()
    message = create_message_advanced(
    sender="oneprojectdev@gmail.com",
    to="mdnannu04@gmail.com",
    cc="cc@example.com",
    bcc="bcc@example.com",
    subject="Test Email",
    message_text="This is the plain text version",
    html_text="<p>This is the <b>HTML</b> version. <img src='cid:image1'></p>",
    attachments=["report.pdf", "summary.csv"],
    inline_images={"image1": "1654424967987.jpg"}    
    )
    send_message = service.users().messages().send(userId="me", body=message).execute()
    print(f"✅ Email sent! Message ID: {send_message['id']}")

if __name__ == "__main__":
    send_email()
