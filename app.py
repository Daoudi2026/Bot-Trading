from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime
import logging
import asyncio
import aiohttp
import threading
import time

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configurazione
METAAPI_TOKEN = os.environ.get('METAAPI_TOKEN', '')
ACCOUNT_ID = os.environ.get('ACCOUNT_ID', '')

# Configurazione bot
bot_config = {
    'active': False,
    'symbol': 'EURUSD',
    'risk_percent': 2.0,
    'ema_fast': 20,
    'ema_slow': 50,
    'check_interval': 60  # secondi tra controlli
}

# Storage
stats = {
    'total_trades': 0,
    'wins': 0,
    'losses': 0,
    'profit': 0.0,
    'balance': 500.0
}

open_positions = []
logs = []
trading_thread = None

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
    if len(logs) > 100:
        logs.pop()
    logger.info(f"[{log_type}] {message}")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# MetaAPI Functions
async def get_account_info():
    """Ottiene info account"""
    try:
        headers = {'auth-token': METAAPI_TOKEN}
        async with aiohttp.ClientSession() as session:
            url = f'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{ACCOUNT_ID}/account-information'
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    stats['balance'] = data.get('balance', stats['balance'])
                    return data
                else:
                    add_log(f"Errore API account: {response.status}", 'ERROR')
                    return None
    except Exception as e:
        add_log(f"Errore get_account_info: {str(e)}", 'ERROR')
        return None

async def get_candles(symbol='EURUSD', timeframe='1h', limit=100):
    """Ottiene candele storiche"""
    try:
        headers = {'auth-token': METAAPI_TOKEN}
        async with aiohttp.ClientSession() as session:
            url = f'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{ACCOUNT_ID}/historical-market-data/symbols/{symbol}/timeframes/{timeframe}/candles'
            params = {'limit': limit}
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    add_log(f"Errore candles: {response.status}", 'ERROR')
                    return None
    except Exception as e:
        add_log(f"Errore get_candles: {str(e)}", 'ERROR')
        return None

def calculate_ema(prices, period):
    """Calcola EMA"""
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices, period=14):
    """Calcola RSI"""
    if len(prices) < period + 1:
        return 50
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

async def analyze_market(symbol):
    """Analizza mercato e genera segnali"""
    try:
        candles = await get_candles(symbol)
        if not candles or len(candles) < 50:
            add_log("Dati insufficienti per analisi", 'WARNING')
            return None
        
        closes = [float(c['close']) for c in candles]
        
        ema_fast = calculate_ema(closes, bot_config['ema_fast'])
        ema_slow = calculate_ema(closes, bot_config['ema_slow'])
        rsi = calculate_rsi(closes)
        
        if ema_fast is None or ema_slow is None:
            return None
        
        add_log(f"Analisi: EMA20={ema_fast:.5f}, EMA50={ema_slow:.5f}, RSI={rsi:.1f}", 'INFO')
        
        # Segnale BUY
        if ema_fast > ema_slow and rsi < 70 and rsi > 30:
            signal = {
                'action': 'BUY',
                'symbol': symbol,
                'ema_fast': ema_fast,
                'ema_slow': ema_slow,
                'rsi': rsi
            }
            add_log(f"🟢 SEGNALE BUY rilevato! RSI={rsi:.1f}", 'SUCCESS')
            return signal
        
        # Segnale SELL
        elif ema_fast < ema_slow and rsi > 30 and rsi < 70:
            signal = {
                'action': 'SELL',
                'symbol': symbol,
                'ema_fast': ema_fast,
                'ema_slow': ema_slow,
                'rsi': rsi
            }
            add_log(f"🔴 SEGNALE SELL rilevato! RSI={rsi:.1f}", 'SUCCESS')
            return signal
        
        return None
        
    except Exception as e:
        add_log(f"Errore analyze_market: {str(e)}", 'ERROR')
        return None

async def place_trade(signal):
    """Apre un trade"""
    try:
        headers = {
            'auth-token': METAAPI_TOKEN,
            'Content-Type': 'application/json'
        }
        
        # Calcolo volume basato su rischio
        risk_amount = stats['balance'] * (bot_config['risk_percent'] / 100)
        volume = max(0.01, round(risk_amount / 100, 2))  # Semplificato
        
        trade_data = {
            'actionType': 'ORDER_TYPE_BUY' if signal['action'] == 'BUY' else 'ORDER_TYPE_SELL',
            'symbol': signal['symbol'],
            'volume': volume
        }
        
        async with aiohttp.ClientSession() as session:
            url = f'https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{ACCOUNT_ID}/trade'
            async with session.post(url, headers=headers, json=trade_data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    position = {
                        'id': result.get('orderId', 'unknown'),
                        'action': signal['action'],
                        'symbol': signal['symbol'],
                        'volume': volume,
                        'entry_time': datetime.now().isoformat()
                    }
                    open_positions.append(position)
                    stats['total_trades'] += 1
                    
                    add_log(f"✅ Trade aperto: {signal['action']} {signal['symbol']} @ {volume} lotti", 'TRADE')
                    return result
                else:
                    error = await response.text()
                    add_log(f"Errore apertura trade: {error}", 'ERROR')
                    return None
                    
    except Exception as e:
        add_log(f"Errore place_trade: {str(e)}", 'ERROR')
        return None

def trading_loop_sync():
    """Loop principale trading (sync wrapper)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    add_log("🚀 Trading loop avviato!", 'SUCCESS')
    
    while bot_config['active']:
        try:
            # Ottiene info account
            account = loop.run_until_complete(get_account_info())
            
            if account:
                add_log(f"💰 Saldo: €{stats['balance']:.2f}", 'INFO')
            
            # Analizza mercato
            signal = loop.run_until_complete(analyze_market(bot_config['symbol']))
            
            # Se c'è un segnale e non ci sono posizioni aperte
            if signal and len(open_positions) == 0:
                add_log(f"📊 Segnale trovato: {signal['action']}", 'SUCCESS')
                loop.run_until_complete(place_trade(signal))
            elif len(open_positions) > 0:
                add_log(f"⏳ Posizione già aperta, attendo...", 'INFO')
            else:
                add_log("🔍 Nessun segnale, continuo a monitorare...", 'INFO')
            
            # Attende prima del prossimo controllo
            time.sleep(bot_config['check_interval'])
            
        except Exception as e:
            add_log(f"Errore nel loop: {str(e)}", 'ERROR')
            time.sleep(10)
    
    add_log("⏹️ Trading loop fermato", 'INFO')

# Routes
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
        'positions': open_positions,
        'logs': logs[:20]
    })

@app.route('/api/start', methods=['POST'])
def start_bot():
    global trading_thread
    
    if not bot_config['active']:
        bot_config['active'] = True
        add_log('🚀 Bot avviato!', 'SUCCESS')
        
        # Avvia thread trading
        trading_thread = threading.Thread(target=trading_loop_sync, daemon=True)
        trading_thread.start()
        
    return jsonify({'success': True, 'message': 'Bot avviato'})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    if bot_config['active']:
        bot_config['active'] = False
        add_log('⏹️ Bot fermato', 'INFO')
    return jsonify({'success': True, 'message': 'Bot fermato'})

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    bot_config.update({
        'symbol': data.get('symbol', bot_config['symbol']),
        'risk_percent': float(data.get('risk', bot_config['risk_percent'])),
    })
    add_log(f"⚙️ Config aggiornata: {data.get('symbol')}", 'SUCCESS')
    return jsonify({'success': True, 'config': bot_config})

if __name__ == '__main__':
    add_log('🟢 Server avviato', 'SUCCESS')
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
