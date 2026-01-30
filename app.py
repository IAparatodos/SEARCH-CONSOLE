#!/usr/bin/env python3
"""
Aplicación web para visualizar datos de Google Search Console.
Dashboard con múltiples pestañas de análisis.
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

# Palabras transaccionales para filtrar
TRANSACTIONAL_KEYWORDS = ['comprar', 'precio', 'azulejo', 'plato', 'mampara', 'm2']


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


def query_search_console(days=90, dimension='page', row_limit=100):
    """Consulta base a Search Console."""
    creds = get_credentials()
    service = build('searchconsole', 'v1', credentials=creds)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    request_body = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'dimensions': [dimension],
        'rowLimit': row_limit,
        'dataState': 'final'
    }

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
        'days': days,
        'dimension': dimension,
        'rows': rows,
        'total_clicks': sum(r['clicks'] for r in rows),
        'total_impressions': sum(r['impressions'] for r in rows)
    }


def query_page_query_combined(days=90, row_limit=500):
    """Consulta combinada de página + query para análisis avanzado."""
    creds = get_credentials()
    service = build('searchconsole', 'v1', credentials=creds)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    request_body = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'dimensions': ['page', 'query'],
        'rowLimit': row_limit,
        'dataState': 'final'
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request_body).execute()

    rows = []
    if 'rows' in response:
        for row in response['rows']:
            rows.append({
                'page': row['keys'][0],
                'query': row['keys'][1],
                'clicks': int(row['clicks']),
                'impressions': int(row['impressions']),
                'ctr': round(row['ctr'] * 100, 2),
                'position': round(row['position'], 1)
            })

    return rows


@app.route('/')
def index():
    """Página principal con sistema de pestañas."""
    return render_template('index.html')


@app.route('/api/performance')
def api_performance():
    """Tab 1: Rendimiento General - Soporta múltiples dimensiones."""
    try:
        days = request.args.get('days', 90, type=int)
        limit = request.args.get('limit', 10, type=int)
        dimension = request.args.get('dimension', 'page')

        # Validar dimensión
        valid_dimensions = ['page', 'query', 'country', 'device']
        if dimension not in valid_dimensions:
            dimension = 'page'

        data = query_search_console(days=days, dimension=dimension, row_limit=limit)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ctr-opportunities')
def api_ctr_opportunities():
    """Tab 2: Oportunidades de CTR - Impresiones > 5000, CTR < 1.5%."""
    try:
        days = request.args.get('days', 90, type=int)
        data = query_search_console(days=days, dimension='page', row_limit=500)

        # Filtrar: Impresiones > 5000 y CTR < 1.5%
        opportunities = [
            {**row, 'action': 'Optimizar Meta Title'}
            for row in data['rows']
            if row['impressions'] > 5000 and row['ctr'] < 1.5
        ]

        # Ordenar por impresiones descendente
        opportunities.sort(key=lambda x: x['impressions'], reverse=True)

        data['rows'] = opportunities
        data['total_opportunities'] = len(opportunities)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quick-wins')
def api_quick_wins():
    """Tab 3: Quick Wins - Keywords en posición 10-15."""
    try:
        days = request.args.get('days', 90, type=int)

        # Obtener datos combinados de página + query
        rows = query_page_query_combined(days=days, row_limit=1000)

        # Filtrar posición entre 10 y 15
        quick_wins = [
            row for row in rows
            if 10 <= row['position'] <= 15
        ]

        # Ordenar por posición ascendente (más cerca del top 10 primero)
        quick_wins.sort(key=lambda x: x['position'])

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        return jsonify({
            'site_url': SITE_URL,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'days': days,
            'rows': quick_wins[:50],  # Limitar a 50 resultados
            'total_quick_wins': len(quick_wins)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactional')
def api_transactional():
    """Tab 4: Análisis Transaccional - URLs con intención de compra."""
    try:
        days = request.args.get('days', 90, type=int)
        data = query_search_console(days=days, dimension='page', row_limit=500)

        # Filtrar URLs que contienen palabras transaccionales
        transactional = []
        for row in data['rows']:
            url_lower = row['key'].lower()
            matching_keywords = [kw for kw in TRANSACTIONAL_KEYWORDS if kw in url_lower]
            if matching_keywords:
                row['matched_keywords'] = matching_keywords
                row['intent'] = 'Compra' if any(kw in ['comprar', 'precio'] for kw in matching_keywords) else 'Producto'
                transactional.append(row)

        # Ordenar por clicks descendente
        transactional.sort(key=lambda x: x['clicks'], reverse=True)

        # Calcular estadísticas
        total_transactional_clicks = sum(r['clicks'] for r in transactional)
        total_transactional_impressions = sum(r['impressions'] for r in transactional)

        data['rows'] = transactional
        data['total_transactional'] = len(transactional)
        data['transactional_clicks'] = total_transactional_clicks
        data['transactional_impressions'] = total_transactional_impressions
        data['keywords_tracked'] = TRANSACTIONAL_KEYWORDS

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/summary')
def api_summary():
    """Resumen general para el dashboard."""
    try:
        days = request.args.get('days', 90, type=int)
        data = query_search_console(days=days, dimension='page', row_limit=100)

        return jsonify({
            'total_clicks': data['total_clicks'],
            'total_impressions': data['total_impressions'],
            'top_page': data['rows'][0] if data['rows'] else None,
            'days': days,
            'start_date': data['start_date'],
            'end_date': data['end_date']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
