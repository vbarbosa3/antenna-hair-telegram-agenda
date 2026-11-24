"""Integração com Google Calendar usando OAuth de aplicativo desktop.

Na primeira execução, execute setup_google_calendar.py. O Google abrirá uma tela
oficial de autorização e será criado token.json localmente.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = Path(os.environ.get("GOOGLE_CREDENTIALS_FILE", BASE_DIR / "credentials.json"))
TOKEN_FILE = Path(os.environ.get("GOOGLE_TOKEN_FILE", BASE_DIR / "token.json"))
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
TIMEZONE = os.environ.get("GOOGLE_CALENDAR_TIMEZONE", "America/Sao_Paulo")
LOCAL_ZONE = ZoneInfo(TIMEZONE)


class CalendarError(RuntimeError):
    pass


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            raise CalendarError(
                f"Arquivo {CREDENTIALS_FILE.name} não encontrado. "
                "Baixe as credenciais OAuth do Google Cloud Console."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def service():
    return build("calendar", "v3", credentials=get_credentials(), cache_discovery=False)


def check_freebusy(start: datetime, end: datetime) -> bool:
    """Retorna True se houver algum evento conflitante."""
    if start.tzinfo is None:
        start = start.replace(tzinfo=LOCAL_ZONE)
    if end.tzinfo is None:
        end = end.replace(tzinfo=LOCAL_ZONE)
    api = service()
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": TIMEZONE,
        "items": [{"id": CALENDAR_ID}],
    }
    result = api.freebusy().query(body=body).execute()
    return bool(result.get("calendars", {}).get(CALENDAR_ID, {}).get("busy", []))


def create_booking_event(booking: dict[str, Any]) -> dict[str, Any]:
    service_info = booking["service"]
    start = datetime.fromisoformat(
        f"{booking['appointment_date']}T{booking['appointment_time']}:00"
    ).replace(tzinfo=LOCAL_ZONE)
    end = start + timedelta(minutes=service_info.duration_minutes)
    if check_freebusy(start, end):
        raise CalendarError("Esse horário já está ocupado na agenda.")

    event = {
        "summary": f"{service_info.name} – {booking['customer_name']}",
        "description": (
            "Agendamento criado pelo chatbot Antenna Hair.\n"
            f"Serviço: {service_info.name}\n"
            f"Valor: R$ {service_info.price},00\n"
            f"Telegram ID: {booking['user_id']}"
        ),
        "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end.isoformat(), "timeZone": TIMEZONE},
        "extendedProperties": {"private": {"antenna_hair_bot": "true"}},
    }
    return service().events().insert(calendarId=CALENDAR_ID, body=event).execute()


def authorize_and_test() -> str:
    get_credentials()
    return "Autorização concluída."
