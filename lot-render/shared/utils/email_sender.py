import os
from sendgrid.helpers.mail import Mail, Attachment
from sendgrid import SendGridAPIClient
from string import Template
from typing import TypedDict
from sendgrid.helpers.mail import FileContent, FileName, FileType, Disposition


class AttachmentInfo(TypedDict):
    filename: str
    content: str
    file_type: str


def read_template(template_path: str) -> str:
    with open(template_path, "r", encoding="utf-8") as file:
        template_content = file.read()
    return template_content


def send_email(
    email: str,
    subject: str,
    template_path: str,
    template_vars: dict = None,
    attachments: list[AttachmentInfo] = None,
):
    if None in [email, subject, template_path]:
        return False

    try:
        template_content = read_template(template_path)
        template = Template(template_content)
        html_content = template.substitute(template_vars or {})

        message = Mail(
            from_email="admin.digital@gethome.com.br",
            to_emails=email,
            subject=subject,
            html_content=html_content,
        )

        if attachments:
            for attachment_info in attachments:
                attachment = Attachment(
                    FileContent(attachment_info["content"]),
                    FileName(attachment_info["filename"]),
                    FileType(f"application/{attachment_info['file_type']}"),
                    Disposition("attachment"),
                )
                message.attachment = attachment

        SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
