#!/usr/bin/env python3
"""
Script para obtener la página más visitada de Google Search Console
en los últimos 90 días.
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
CREDENTIALS_PATH = os.path.expanduser('~/.config/gsc/credentials.json')
TOKEN_PATH = os.path.expanduser('~/.config/gsc/token.json')
SITE_URL = 'https://www.adrihosan.com'

def get_credentials():
    """Obtiene o refresca las credenciales de Google."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return creds

def get_most_visited_page():
    """Obtiene la página más visitada en los últimos 90 días."""
    creds = get_credentials()
    service = build('searchconsole', 'v1', credentials=creds)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)

    request = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'dimensions': ['page'],
        'rowLimit': 10,
        'dataState': 'final'
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()

    if 'rows' in response:
        print("\n" + "="*60)
        print("TOP 10 PÁGINAS MÁS VISITADAS (últimos 90 días)")
        print(f"Sitio: {SITE_URL}")
        print(f"Período: {start_date} a {end_date}")
        print("="*60 + "\n")

        for i, row in enumerate(response['rows'], 1):
            page = row['keys'][0]
            clicks = int(row['clicks'])
            impressions = int(row['impressions'])
            ctr = row['ctr'] * 100
            position = row['position']

            print(f"{i}. {page}")
            print(f"   Clicks: {clicks:,} | Impresiones: {impressions:,} | CTR: {ctr:.2f}% | Posición: {position:.1f}")
            print()

        # Destacar la más visitada
        top_page = response['rows'][0]
        print("="*60)
        print("🏆 PÁGINA MÁS VISITADA:")
        print(f"   {top_page['keys'][0]}")
        print(f"   {int(top_page['clicks']):,} clicks en 90 días")
        print("="*60)
    else:
        print("No se encontraron datos para el período especificado.")

if __name__ == '__main__':
    get_most_visited_page()
