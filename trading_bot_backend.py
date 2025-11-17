from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import aiohttp
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configurazione
METAAPI_TOKEN = os.environ.get('METAAPI_TOKEN', 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJjZjAzNDk1OTRlNzU2YmY4NWYxMTljYjIyOTQwYjQyMyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiY2YwMzQ5NTk0ZTc1NmJmODVmMTE5Y2IyMjk0MGI0MjMiLCJpYXQiOjE3NjMzOTY1OTh9.HWT8CgvXe1PVWDchvZk315Z8jidV9URFe7uytCY_8iAr-4NsZ1-qNehvmyyOIBu2rI2GSFV_SFAp_BNkbI1b0i3HnDmmSYPyngSpQqlFEoLTMYAVUAvaqO5kt9iPO1ABdW3o6F3aXgKQI5CdO8Bp3gFqwDzgy43ojTA8m--Fv6a4qwtvgAks-6GxlZ76JjdAz9nLCePrdkaUfJWynYTJky30-4DcAmF33S-vhyRw2h_XLsmImFDKa9R3VH1QHMRTZCKuiIa69a4wzalLCXPRc1EmEc62p4Vi_3kYxfgbgm5zDJe3natibiRgntzJcZ7ElcaGJPLTb6RtJLs8cKfaY-y44AaR_YEDblHr4WoPPOYAHvm4mXqs5uaRL6K-Jp1la08h-_xfmOAzZOeNlAYrKQX61khg7_e1BV7l1kdkvx4eCj2avi7lRdqFErZigMouQuCInrs16yN5_gnXBuuEykWaB_Fu6zSJzIwmW2wzw5be_bZ9WGDL9uZYzqEMWHVQ9sOxW6_RomtXGQ-5kTjb7O-GCAq83MF3GnLJAkoKWVvOK2oy6D2tSuaCyfztB0BhcgPtqMRSB0vQi-RAS2jDfJ3iJ3VgcuKQ_eJ9ub4bFq3JenBnZI8JnHrQZJl0XAvii6vqeN5TWSD9FElf2F8iO9QO6xY784YlU8SqAbKZ2do')
ACCOUNT_ID = os.environ.get('ACCOUNT_ID', 'a623a8cc-2281-4d8c-9708-d929ec6096ba')

# Configurazione bot
bot_config = {
    'active': False,
    'symbol': 'EURUSD',
    'risk_percent': 2.0,
    'ema_fast': 20,
    'ema_slow': 50,
    'rsi_period': 14,
    'stop_loss_pips': 50,
    'take_profit_pips': 100
}

# Storage per statistiche
stats = {
    'total_trades': 0,
    'wins': 0,
    'losses': 0,
    'profit': 0.0,
    'balance': 500.0
}

open_trades = []
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

async def get_account_info():
    """Ottiene informazioni account da MetaAPI"""
    try:
        headers = {
            'auth-token': METAAPI_TOKEN,
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            url = f'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{ACCOUNT_ID}/account-information'
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    stats['balance'] = data.get('balance', stats['balance'])
                    add_log(f"Saldo account: €{stats['balance']:.2f}", 'SUCCESS')
                    return data
                else:
                    add_log(f"Errore lettura account: {response.status}", 'ERROR')
                    return None
    except Exception as e:
        add_log(f"Errore connessione MetaAPI: {str(e)}", 'ERROR')
        return None

async def place_trade(action, symbol, volume, sl, tp):
    """Apre un trade tramite MetaAPI"""
    try:
        headers = {
            'auth-token': METAAPI_TOKEN,
            'Content-Type': 'application/json'
        }
        
        trade_data = {
            'actionType': 'ORDER_TYPE_BUY' if action == 'BUY' else 'ORDER_TYPE_SELL',
            'symbol': symbol,
            'volume': volume,
            'stopLoss': sl,
            'takeProfit': tp
        }
        
        async with aiohttp.ClientSession() as session:
            url = f'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{ACCOUNT_ID}/trade'
            async with session.post(url, headers=headers, json=trade_data) as response:
                if response.status == 200:
                    result = await response.json()
                    add_log(f"Trade {action} aperto: {symbol} @ {volume} lotti", 'TRADE')
                    return result
                else:
                    error_text = await response.text()
                    add_log(f"Errore apertura trade: {error_text}", 'ERROR')
                    return None
    except Exception as e:
        add_log(f"Errore place_trade: {str(e)}", 'ERROR')
        return None

async def trading_loop():
    """Loop principale del bot"""
    while bot_config['active']:
        try:
            # Ottiene info account
            account_info = await get_account_info()
            
            if account_info:
                # Qui implementi la logica di trading
                # Per ora simuliamo un trade ogni 30 secondi
                add_log("Analisi mercato in corso...", 'INFO')
            
            await asyncio.sleep(30)
            
        except Exception as e:
            add_log(f"Errore nel loop: {str(e)}", 'ERROR')
            await asyncio.sleep(10)

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
        'trades': open_trades,
        'logs': logs[:20]
    })

@app.route('/api/start', methods=['POST'])
def start_bot():
    if not bot_config['active']:
        bot_config['active'] = True
        add_log('Bot avviato con successo', 'SUCCESS')
        
        # Avvia loop in background
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(trading_loop())
        
    return jsonify({'success': True, 'message': 'Bot avviato'})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    if bot_config['active']:
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
    add_log(f"Configurazione aggiornata: {data.get('symbol')}, {data.get('risk')}%", 'SUCCESS')
    return jsonify({'success': True, 'config': bot_config})

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test connessione MetaAPI"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(get_account_info())
    
    if result:
        return jsonify({'success': True, 'message': 'Connessione OK', 'data': result})
    else:
        return jsonify({'success': False, 'message': 'Errore connessione'}), 500

if __name__ == '__main__':
    add_log('Server avviato', 'SUCCESS')
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)