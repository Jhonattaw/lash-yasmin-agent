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
    tz = pytz.timezone('America/Sao_Paulo')

    creds = _get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    start_dt = tz.localize(datetime.datetime.strptime(f"{date_str} 09:00", "%Y-%m-%d %H:%M"))
    end_dt   = tz.localize(datetime.datetime.strptime(f"{date_str} 19:00", "%Y-%m-%d %H:%M"))

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Gerar slots de 30min, pulando almoço (12h-13h)
    all_slots = []
    curr = start_dt
    while curr < end_dt:
        if curr.hour != 12:
            all_slots.append(curr)
        curr += datetime.timedelta(minutes=30)

    # Filtrar slots ocupados
    available_slots = []
    for slot in all_slots:
        is_busy = False
        for event in events:
            start_str = event['start'].get('dateTime')
            end_str   = event['end'].get('dateTime')

            if not start_str or not end_str:
                continue  # ignora eventos de dia inteiro

            start_event = datetime.datetime.fromisoformat(
                start_str.replace('Z', '+00:00')
            ).astimezone(tz)
            end_event = datetime.datetime.fromisoformat(
                end_str.replace('Z', '+00:00')
            ).astimezone(tz)

            if start_event <= slot < end_event:
                is_busy = True
                break

        if not is_busy:
            available_slots.append(slot.strftime("%H:%M"))

    return available_slots

DURACAO_PADRAO = 150  # minutos (2h30)

DURACOES = {
    "egípcio": 150,
    "5d": 180,
    "mega": 150,
    "brasileiro": 210,
    "manutenção": 90,
}


def _duracao_servico(service):
    s = service.lower()
    for chave, minutos in DURACOES.items():
        if chave in s:
            return minutos
    return DURACAO_PADRAO


def create_event(date_str, time_str, service, client_name):
    tz = pytz.timezone('America/Sao_Paulo')
    creds = _get_credentials()
    service_api = build('calendar', 'v3', credentials=creds)

    start_dt = tz.localize(
        datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    )
    end_dt = start_dt + datetime.timedelta(minutes=_duracao_servico(service))

    evento = {
        'summary': f'{service} - {client_name}',
        'description': f'Agendamento via Lash IA\nCliente: {client_name}\nServiço: {service}',
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
    }

    criado = service_api.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
    return criado.get('id')