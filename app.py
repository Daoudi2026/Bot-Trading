from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configurazione
METAAPI_TOKEN = os.environ.get('METAAPI_TOKEN', '')
ACCOUNT_ID = os.environ.get('ACCOUNT_ID', '')

# Configurazione bot
bot_config = {
    'active': False,
    'symbol': 'EURUSD',
    'risk_percent': 2.0,
}

# Storage per statistiche
stats = {
    'total_trades': 0,
    'wins': 0,
    'losses': 0,
    'profit': 0.0,
    'balance': 500.0
}

logs = []

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_log(message, log_type='INFO'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'time': timestamp,
        'type': log_type,
        'message': message
    }
    logs.insert(0, log_entry)
    if len(logs) > 50:
        logs.pop()
    logger.info(f"[{log_type}] {message}")

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Trading Bot API attivo',
        'bot_active': bot_config['active']
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'active': bot_config['active'],
        'config': bot_config,
        'stats': stats,
        'logs': logs[:20]
    })

@app.route('/api/start', methods=['POST'])
def start_bot():
    bot_config['active'] = True
    add_log('Bot avviato con successo', 'SUCCESS')
    return jsonify({'success': True, 'message': 'Bot avviato'})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    bot_config['active'] = False
    add_log('Bot fermato', 'INFO')
    return jsonify({'success': True, 'message': 'Bot fermato'})

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    bot_config.update({
        'symbol': data.get('symbol', bot_config['symbol']),
        'risk_percent': float(data.get('risk', bot_config['risk_percent'])),
    })
    add_log(f"Configurazione aggiornata", 'SUCCESS')
    return jsonify({'success': True, 'config': bot_config})

if __name__ == '__main__':
    add_log('Server avviato', 'SUCCESS')
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
