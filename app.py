from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import json
import os
from models import db, Symbol

app = Flask(__name__)

# Configure SQLAlchemy with SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'symbols.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)




CSV_FOLDER = 'data'

def fetch_csv_data(ticker, interval='1m', ema_period=20, rsi_period=14):
    file_path = os.path.join(CSV_FOLDER, f"{ticker}_1min.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV not found: {file_path}")

    df = pd.read_csv(file_path, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]

    # Determine if resampling is needed
    if interval != '1m':
        pandas_interval = interval.replace('m', 'T').replace('h', 'H').replace('d', 'D')
        df = df.resample(pandas_interval).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

    # Compute indicators
    df['EMA'] = ta.ema(df['close'], length=ema_period)
    df['RSI'] = ta.rsi(df['close'], length=rsi_period)

    # Format for frontend
    candlestick_data = [
        {
            'time': int(ts.timestamp()),
            'open': row.open,
            'high': row.high,
            'low': row.low,
            'close': row.close
        }
        for ts, row in df.iterrows()
    ]

    ema_data = [
        {
            'time': int(ts.timestamp()),
            'value': row.EMA
        }
        for ts, row in df.iterrows() if not pd.isna(row.EMA)
    ]

    rsi_data = [
        {
            'time': int(ts.timestamp()),
            'value': row.RSI if not pd.isna(row.RSI) else 0
        }
        for ts, row in df.iterrows()
    ]

    return candlestick_data, ema_data, rsi_data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data/<ticker>/<interval>/<int:ema_period>/<int:rsi_period>')
def get_data(ticker, interval, ema_period, rsi_period):
    candlestick_data, ema_data, rsi_data = fetch_csv_data(ticker, interval, ema_period, rsi_period)
    return jsonify({'candlestick': candlestick_data, 'ema': ema_data, 'rsi': rsi_data})

# Create database tables on startup if they don't exist
with app.app_context():
    db.drop_all()     # Drop old tables first
    db.create_all()   # Then create new tables


 

    # Scan CSV files and extract symbol names
    symbols_in_folder = set()
    for filename in os.listdir(CSV_FOLDER):
        if filename.endswith('.csv'):
            symbol = filename.split('_')[0]
            symbols_in_folder.add(symbol)

    # Add to DB if not already present
    added = 0
    for ticker in symbols_in_folder:
        if not Symbol.query.filter_by(ticker=ticker).first():
            symbol_entry = Symbol(ticker=ticker, name="From CSV")
            db.session.add(symbol_entry)
            added += 1

    db.session.commit()
    print(f"✅ Added {added} symbols from CSV filenames")




@app.route('/api/symbols')
def get_symbols():
    results = []
    symbols = Symbol.query.all()

    for symbol in symbols:
        ticker = symbol.ticker
        csv_path = os.path.join(CSV_FOLDER, f"{ticker}_1min.csv")
        price = 0

        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if not df.empty and 'close' in df.columns:
                    price = float(df['close'].iloc[-1])
            except Exception as e:
                print(f"Error reading {csv_path}: {e}")

        results.append({
            'id': symbol.id,
            'symbol': ticker,
            'name': "EXPIRED",  # or customize if available
            'price': price,
            'change': 0  # Optional: calculate price change %
        })

    return jsonify(results)



@app.route('/api/symbols', methods=['POST'])
def add_symbol():
    data = request.json
    if not data or 'symbol' not in data:
        return jsonify({'error': 'Symbol is required'}), 400
    
    ticker = data['symbol'].strip().upper()
    if not ticker:
        return jsonify({'error': 'Symbol cannot be empty'}), 400
    
    # Check if symbol already exists
    existing = Symbol.query.filter_by(ticker=ticker).first()
    if existing:
        return jsonify({'error': 'Symbol already exists', 'symbol': existing.to_dict()}), 409
    
    # Validate symbol with yfinance
    try:
        info = yf.Ticker(ticker).info
        if 'regularMarketPrice' not in info and 'currentPrice' not in info:
            return jsonify({'error': 'Invalid symbol'}), 400
            
        # Add symbol to database
        symbol = Symbol(ticker=ticker, name=info.get('shortName', ticker))
        db.session.add(symbol)
        db.session.commit()
        
        return jsonify({'message': 'Symbol added successfully', 'symbol': symbol.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': f'Error adding symbol: {str(e)}'}), 400

@app.route('/api/symbols/<int:symbol_id>', methods=['DELETE'])
def delete_symbol(symbol_id):
    symbol = Symbol.query.get_or_404(symbol_id)
    db.session.delete(symbol)
    db.session.commit()
    return jsonify({'message': 'Symbol deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)