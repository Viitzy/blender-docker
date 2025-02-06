import base64
from datetime import datetime
from fastapi import HTTPException, status
import io
import json
import os
import uuid
from psycopg2.extensions import connection as Connection
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus.flowables import TopPadder

from account.src.schemas.users_schemas import UserReportCreate
from account.src.services.users.get_user_service import (
    execute as get_user_service,
)
from utils import dict_to_df, format_dict
from shared.utils.email_sender import send_email
from shared.utils.formatters import mask_phone


def generate_csv_personal_info(data: dict) -> bytes:
    df = dict_to_df(data)

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def generate_pdf_personal_info(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styleN = styles["Normal"]

    elements = list()

    logo = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "static",
            "imgs",
            "get_home_logo.png",
        )
    )
    elements.append(Image(logo, width=96, height=39, hAlign="LEFT"))
    elements.append(Spacer(1, 48))

    user_data = f"""
        <b>Nome:</b> {data["person_name"]}<br/>
        <b>Nome Preferido:</b> {data["preferred_name"] if data.get("preferred_name") else "Não informado"}<br/>
        <b>Identificação:</b> {data["identification"] if data.get("identification") else "Não informado"}<br/>
        <b>Data de Criação:</b> {data["created_at"]}<br/>
        <b>E-mails:</b> {", ".join(data["email"]) if data.get("email") else "Não informado"}<br/>
        <b>Telefones:</b> {", ".join(data["phone"]) if data.get("phone") else "Não informado"}<br/>
    """

    elements.append(Paragraph(user_data, styleN))
    elements.append(Spacer(1, 12))

    company_info = {
        "name": "GetHome",
        "address": "Belo Horizonte - MG",
        "contact": "+55(31) 9999-9999",
        "email": "contato@gethome.com.br",
    }

    company_data = f"""
        <b>{company_info["name"]}</b><br/>
        {company_info["address"]}<br/>
        {company_info["contact"]}<br/>
        {company_info["email"]}<br/>
        © {company_info["name"]} {datetime.now().year}. Todos os direitos reservados.
    """
    elements.append(Spacer(1, 100))
    elements.append(TopPadder(Paragraph(company_data, styleN)))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_json_personal_info(data: dict) -> bytes:
    json_string = json.dumps(format_dict(data))
    return json_string.encode("utf-8")


def execute(db: Connection, user_id: int, data: UserReportCreate):
    try:
        file_type = data.file_type

        user_info = get_user_service(db, user_id)
        person_user = user_info["person"]

        user_data = {
            "person_name": person_user["name"],
            "preferred_name": person_user["preferred_name"],
            "identification": person_user["identification"],
            "created_at": person_user["created_at"],
        }

        contacts = user_info["person"]["contacts"]
        for contact in contacts:
            if not user_data.get(contact["type"]["name"].lower()):
                user_data[contact["type"]["name"].lower()] = []

            user_data[contact["type"]["name"].lower()].append(contact["value"])

        if user_data.get("telefone"):
            user_data["phone"] = [
                mask_phone(phone) for phone in user_data.pop("telefone")
            ]

        email = None
        if user_info["username"] and "@" in user_info["username"]:
            email = user_info["username"]

        if user_data.get("email"):
            email = user_data["email"][0]

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no email",
            )

        mime_type = None
        ext = None
        file_bytes = None

        if file_type == "csv":
            file_bytes = generate_csv_personal_info(user_data)
            mime_type = "text/csv"
            ext = "csv"

        elif file_type == "pdf":
            file_bytes = generate_pdf_personal_info(user_data)
            mime_type = "application/pdf"
            ext = "pdf"

        elif file_type == "json":
            file_bytes = generate_json_personal_info(user_data)
            mime_type = "application/json"
            ext = "json"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type",
            )

        file_base64 = base64.b64encode(file_bytes).decode("utf-8")
        file = {
            "filename": f"{str(uuid.uuid4())}.{ext}",
            "content": file_base64,
            "file_type": mime_type,
        }

        email_sent = send_email(
            email=user_data["email"][0],
            subject="Seu relatório está pronto",
            template_path=f"{os.path.dirname(__file__)}/../../static/templates/user_report.html",
            template_vars={
                "user_name": user_info["person"]["name"].split(" ")[0]
            },
            attachments=[file],
        )
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error sending email",
            )

        return {
            "success": True,
            "message": "Success",
            "file": file,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating report",
        )
