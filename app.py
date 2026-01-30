#!/usr/bin/env python3
"""
Aplicación web para visualizar datos de Google Search Console.
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
CREDENTIALS_PATH = os.path.expanduser('~/.config/gsc/credentials.json')
SITE_URL = 'https://www.adrihosan.com'


def get_credentials():
    """Obtiene credenciales de Google (soporta service account y OAuth)."""
    with open(CREDENTIALS_PATH, 'r') as f:
        creds_data = json.load(f)

    if creds_data.get('type') == 'service_account':
        from google.oauth2 import service_account
        return service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=SCOPES
        )

    from google.oauth2.credentials import Credentials
    TOKEN_PATH = os.path.expanduser('~/.config/gsc/token.json')
    if os.path.exists(TOKEN_PATH):
        return Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return None


def get_search_console_data(days=90, row_limit=10):
    """Obtiene datos de Search Console."""
    creds = get_credentials()
    service = build('searchconsole', 'v1', credentials=creds)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    request = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'dimensions': ['page'],
        'rowLimit': row_limit,
        'dataState': 'final'
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()

    pages = []
    if 'rows' in response:
        for row in response['rows']:
            pages.append({
                'page': row['keys'][0],
                'clicks': int(row['clicks']),
                'impressions': int(row['impressions']),
                'ctr': round(row['ctr'] * 100, 2),
                'position': round(row['position'], 1)
            })

    return {
        'site_url': SITE_URL,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'days': days,
        'pages': pages,
        'total_clicks': sum(p['clicks'] for p in pages),
        'total_impressions': sum(p['impressions'] for p in pages)
    }


@app.route('/')
def index():
    """Página principal con los datos de Search Console."""
    try:
        data = get_search_console_data(days=90, row_limit=10)
        return render_template('index.html', data=data, error=None)
    except Exception as e:
        return render_template('index.html', data=None, error=str(e))


@app.route('/api/data')
def api_data():
    """API endpoint para obtener datos en JSON."""
    try:
        data = get_search_console_data(days=90, row_limit=10)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
