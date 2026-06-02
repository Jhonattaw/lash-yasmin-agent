import datetime
import pytz
import json
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentialsg.json')
CALENDAR_ID = 'dheaw2@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/calendar']


def _get_credentials():
    """Carrega credenciais: variável de ambiente (Vercel) ou arquivo local."""
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json_str:
        creds_dict = json.loads(creds_json_str)
        return service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )


def get_available_slots(date_str):
    """
    date_str: 'YYYY-MM-DD'
    Retorna horários livres em Brasília (UTC-3) entre 09:00 e 18:00
    """
    tz = pytz.timezone('America/Sao_Paulo')

    creds = _get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    start_dt = tz.localize(datetime.datetime.strptime(f"{date_str} 09:00", "%Y-%m-%d %H:%M"))
    end_dt   = tz.localize(datetime.datetime.strptime(f"{date_str} 18:00", "%Y-%m-%d %H:%M"))

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    all_slots = []
    curr = start_dt
    while curr < end_dt:
        all_slots.append(curr)
        curr += datetime.timedelta(minutes=30)

    available_slots = []
    for slot in all_slots:
        is_busy = False
        for event in events:
            start_event = datetime.datetime.fromisoformat(
                event['start'].get('dateTime').replace('Z', '+00:00')
            ).astimezone(tz)
            end_event = datetime.datetime.fromisoformat(
                event['end'].get('dateTime').replace('Z', '+00:00')
            ).astimezone(tz)

            if start_event <= slot < end_event:
                is_busy = True
                break

        if not is_busy:
            available_slots.append(slot.strftime("%H:%M"))

    return available_slots