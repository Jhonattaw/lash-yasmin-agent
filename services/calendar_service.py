import datetime
import pytz
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Nome do arquivo de credenciais na raiz do seu projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentialsg.json')
CALENDAR_ID = 'dheaw2@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_available_slots(date_str):
    """
    date_str: 'YYYY-MM-DD'
    Retorna horários livres em Brasília (UTC-3) entre 09:00 e 18:00
    """
    tz = pytz.timezone('America/Sao_Paulo')
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    # Definir o range do dia no horário de Brasília
    start_dt = tz.localize(datetime.datetime.strptime(f"{date_str} 09:00", "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.datetime.strptime(f"{date_str} 18:00", "%Y-%m-%d %H:%M"))

    # Buscar eventos no período, convertendo para ISO para a API
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])

    # Gerar slots de 30min em Brasília
    all_slots = []
    curr = start_dt
    while curr < end_dt:
        all_slots.append(curr)
        curr += datetime.timedelta(minutes=30)

    # Filtrar slots ocupados
    available_slots = []
    for slot in all_slots:
        is_busy = False
        for event in events:
            # Converte as datas dos eventos para o fuso de Brasília
            start_event = datetime.datetime.fromisoformat(event['start'].get('dateTime').replace('Z', '+00:00')).astimezone(tz)
            end_event = datetime.datetime.fromisoformat(event['end'].get('dateTime').replace('Z', '+00:00')).astimezone(tz)
            
            if start_event <= slot < end_event:
                is_busy = True
                break
        
        if not is_busy:
            available_slots.append(slot.strftime("%H:%M"))

    return available_slots