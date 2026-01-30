#!/usr/bin/env python3
"""
Aplicación web para visualizar datos de Google Search Console.
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
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


def get_search_console_data(days=90, row_limit=10, dimension='page',
                            start_date=None, end_date=None, query_filter=None):
    """Obtiene datos de Search Console con filtros personalizados."""
    creds = get_credentials()
    service = build('searchconsole', 'v1', credentials=creds)

    if not end_date:
        end_date = datetime.now().date()
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    if not start_date:
        start_date = end_date - timedelta(days=days)
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    request_body = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'dimensions': [dimension],
        'rowLimit': row_limit,
        'dataState': 'final'
    }

    # Añadir filtro de búsqueda si se proporciona
    if query_filter:
        request_body['dimensionFilterGroups'] = [{
            'filters': [{
                'dimension': dimension,
                'operator': 'contains',
                'expression': query_filter
            }]
        }]

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request_body).execute()

    rows = []
    if 'rows' in response:
        for row in response['rows']:
            rows.append({
                'key': row['keys'][0],
                'clicks': int(row['clicks']),
                'impressions': int(row['impressions']),
                'ctr': round(row['ctr'] * 100, 2),
                'position': round(row['position'], 1)
            })

    return {
        'site_url': SITE_URL,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'days': (end_date - start_date).days,
        'dimension': dimension,
        'filter': query_filter,
        'rows': rows,
        'total_clicks': sum(r['clicks'] for r in rows),
        'total_impressions': sum(r['impressions'] for r in rows)
    }


@app.route('/')
def index():
    """Página principal con los datos de Search Console."""
    # Obtener parámetros de la URL
    days = request.args.get('days', 90, type=int)
    dimension = request.args.get('dimension', 'page')
    row_limit = request.args.get('limit', 10, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query_filter = request.args.get('filter', '')

    try:
        data = get_search_console_data(
            days=days,
            row_limit=row_limit,
            dimension=dimension,
            start_date=start_date,
            end_date=end_date,
            query_filter=query_filter if query_filter else None
        )
        return render_template('index.html', data=data, error=None,
                             current_days=days, current_dimension=dimension,
                             current_limit=row_limit, current_filter=query_filter)
    except Exception as e:
        return render_template('index.html', data=None, error=str(e),
                             current_days=days, current_dimension=dimension,
                             current_limit=row_limit, current_filter=query_filter)


@app.route('/api/data')
def api_data():
    """API endpoint para obtener datos en JSON."""
    days = request.args.get('days', 90, type=int)
    dimension = request.args.get('dimension', 'page')
    row_limit = request.args.get('limit', 10, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query_filter = request.args.get('filter')

    try:
        data = get_search_console_data(
            days=days,
            row_limit=row_limit,
            dimension=dimension,
            start_date=start_date,
            end_date=end_date,
            query_filter=query_filter
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
