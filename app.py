import os
import base64
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

app = Flask(__name__)
app.secret_key = "secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def create_message_advanced(sender, to, subject, message_text, html_text, cc=None, bcc=None, attachments=None, inline_images=None):
    message = EmailMessage()
    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject
    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc

    message.set_content(message_text)
    if html_text:
        message.add_alternative(html_text, subtype="html")

    if inline_images:
        for cid, path in inline_images.items():
            with open(path, "rb") as img:
                data = img.read()
                maintype, subtype = mimetypes.guess_type(path)[0].split("/")
                message.get_payload()[-1].add_related(data, maintype=maintype, subtype=subtype, cid=f"<{cid}>")

    if attachments:
        for file_path in attachments:
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
            maintype, subtype = mime_type.split("/", 1)
            with open(file_path, "rb") as f:
                data = f.read()
            message.add_attachment(data, maintype, subtype, filename=os.path.basename(file_path))

    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        to = request.form["to"]
        cc = request.form.get("cc", "")
        bcc = request.form.get("bcc", "")
        subject = request.form["subject"]
        body = request.form["body"]
        html = request.form.get("html", "")

        attachments = []
        inline_images = {}

        files = request.files.getlist("attachments")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(path)
                if "cid:" in body + html:
                    cid = filename.split(".")[0]
                    inline_images[cid] = path
                else:
                    attachments.append(path)

        try:
            service = authenticate()
            msg = create_message_advanced(
                sender="me",
                to=to,
                subject=subject,
                message_text=body,
                html_text=html,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                inline_images=inline_images
            )
            service.users().messages().send(userId="me", body=msg).execute()
            flash("✅ Email sent successfully!", "success")
        except Exception as e:
            flash(f"❌ Failed to send email: {e}", "danger")

        return redirect(url_for("index"))

    return render_template("index1.html")
if __name__ == "__main__":
    app.run(debug=True)


# from flask import Flask, render_template, request, redirect, url_for, flash
# import os
# import base64
# import mimetypes
# from email.message import EmailMessage
# import pdfkit
# from werkzeug.utils import secure_filename

# import google.auth
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow

# app = Flask(__name__)
# app.secret_key = "supersecretkey"
# UPLOAD_FOLDER = os.path.join("static", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


# def get_gmail_service():
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
#     return build("gmail", "v1", credentials=creds)


# def create_message_with_attachments(sender, to, subject, plain_text, html_content, files):
#     message = EmailMessage()
#     message["To"] = to
#     message["From"] = sender
#     message["Subject"] = subject
#     message.set_content(plain_text)
#     message.add_alternative(html_content, subtype="html")

#     # Save HTML content as PDF and attach it
#     pdf_path = os.path.join(UPLOAD_FOLDER, "html_output.pdf")
#     pdfkit.from_string(html_content, pdf_path)
#     with open(pdf_path, "rb") as f:
#         message.add_attachment(f.read(), maintype="application", subtype="pdf", filename="html_output.pdf")

#     # Add other file attachments
#     for file_path in files:
#         mime_type, _ = mimetypes.guess_type(file_path)
#         main_type, sub_type = mime_type.split("/", 1) if mime_type else ("application", "octet-stream")
#         with open(file_path, "rb") as f:
#             message.add_attachment(f.read(), maintype=main_type, subtype=sub_type, filename=os.path.basename(file_path))

#     encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     return {"raw": encoded_message}


# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         to = request.form["to"]
#         subject = request.form["subject"]
#         plain_text = request.form["plain_text"]
#         html_content = request.form["html_body"]
#         uploaded_files = request.files.getlist("attachments")

#         file_paths = []
#         for file in uploaded_files:
#             if file.filename:
#                 filename = secure_filename(file.filename)
#                 filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#                 file.save(filepath)
#                 file_paths.append(filepath)

#         try:
#             service = get_gmail_service()
#             message = create_message_with_attachments("me", to, subject, plain_text, html_content, file_paths)
#             send_message = service.users().messages().send(userId="me", body=message).execute()
#             flash("Email sent successfully!", "success")
#         except HttpError as error:
#             flash(f"An error occurred: {error}", "danger")

#     return render_template("index.html")


# if __name__ == "__main__":
#     app.run(debug=True)