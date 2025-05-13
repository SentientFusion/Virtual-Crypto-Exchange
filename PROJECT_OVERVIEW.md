# 🚧 Project Overview: CryptoSim
_Generated on 2025-05-13T18:16:56.308346_

## 📂 Folder Structure
```
├── app.py
├── binance_client.py
├── crypto_sim.db
├── models.py
├── static/
│   └── styles.css
├── stoploss.py
└── templates/
    ├── index.html
    ├── login.html
    ├── trade_history.html
    └── wallet.html
```

## 📄 Code Files

### `app.py`
- **Lines:** 60
- **Last Modified:** 2024-10-19T17:11:38.132220

```
from flask import Flask, render_template, request, redirect, url_for, session
from models import ensure_user_exists, get_user_balance, get_user_wallet, get_wallet_value, buy_crypto, sell_crypto, get_trade_history

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        ensure_user_exists(username)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balance = get_user_balance(username)
    wallet_value = get_wallet_value(username)  # This should now fetch the correct value
    holdings = get_user_wallet(username)
    
    return render_template('wallet.html', username=username, balance=balance, wallet_value=wallet_value, holdings=holdings)

@app.route('/buy', methods=['POST'])
def buy():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    symbol = request.form['symbol']
    amount = float(request.form['amount'])
    buy_crypto(username, symbol, amount)
    return redirect(url_for('index'))

@app.route('/sell', methods=['POST'])
def sell():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    symbol = request.form['symbol']
    amount = float(request.form['amount'])
    sell_crypto(username, symbol, amount)
    return redirect(url_for('index'))

@app.route('/trade_history')
def trade_history():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    history = get_trade_history(username)
    return render_template('trade_history.html', history=history)

if __name__ == '__main__':
    app.run(debug=True)

```

### `binance_client.py`
- **Lines:** 18
- **Last Modified:** 2024-10-19T12:08:39.499059

```
from binance.client import Client
import os

API_KEY = 'qIjf0Zlm1UW33VnTSXDNTEGt4lgK6t03KHX5GLVqZycWJmjZdiiF4gLt6SG2iR8U'
API_SECRET = '9BzlnqOZsTlNJq1snlqutvyQvrDOkLvwZhKxYGZsmSqUzD2TKL5ZNggTUDm8cA7a'

client = Client(API_KEY, API_SECRET)

def get_all_crypto_usdt_pairs():
    # Fetch all symbols and filter for crypto-USDT pairs
    exchange_info = client.get_exchange_info()
    pairs = [s['symbol'] for s in exchange_info['symbols'] if 'USDT' in s['symbol']]
    return pairs

def get_price(symbol):
    # Get the latest price for the specified symbol
    avg_price = client.get_avg_price(symbol=symbol)
    return avg_price['price']
```

### `models.py`
- **Lines:** 220
- **Last Modified:** 2024-10-19T17:18:52.268369

```
import sqlite3
from binance.client import Client

DB_NAME = 'crypto_sim.db'

# Initialize the Binance API client
binance_client = Client(api_key='your_api_key', api_secret='your_api_secret')

# Function to initialize the database (create tables)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create users table to store USDT balance and user info
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        usdt_balance REAL
    )''')

    # Create wallet table to store user's crypto holdings
    cursor.execute('''CREATE TABLE IF NOT EXISTS wallet (
        username TEXT,
        symbol TEXT,
        amount REAL,
        PRIMARY KEY (username, symbol),
        FOREIGN KEY (username) REFERENCES users(username)
    )''')

    # Create trade history table
    cursor.execute('''CREATE TABLE IF NOT EXISTS trade_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        symbol TEXT,
        action TEXT,  -- 'buy' or 'sell'
        amount REAL,
        price REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    )''')

    conn.commit()
    conn.close()

# Function to get current crypto prices from Binance
def get_price():
    # Fetch current prices for all crypto-USDT pairs
    prices = {}
    try:
        # Get ticker prices for all pairs
        ticker_data = binance_client.get_all_tickers()
        for item in ticker_data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                prices[symbol] = float(item['price'])
    except Exception as e:
        print(f"Error fetching prices: {e}")

    return prices

# Function to get the user's crypto holdings (wallet)
def get_user_wallet(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT symbol, amount FROM wallet WHERE username=?", (username,))
    holdings = cursor.fetchall()

    conn.close()
    return holdings

# Function to calculate the total wallet value in USDT
def get_wallet_value(username):
    holdings = get_user_wallet(username)
    prices = get_price()
    total_value = 0.0

    for symbol, amount in holdings:
        # Append 'USDT' to symbol if not present
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        # Get the current price of the crypto
        price = prices.get(symbol, 0.0)
        if price > 0:
            value = amount * price
            total_value += value
            print(f"Symbol: {symbol}, Amount: {amount}, Price: {price}, Value: {value}")  # Debug statement
        else:
            print(f"Warning: No price found for {symbol}.")  # Debug statement

    print(f"Total Wallet Value for {username}: {total_value}")  # Debug statement
    return total_value

# Function to get the user's USDT balance
def get_user_balance(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT usdt_balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]

    conn.close()
    return balance

# Function to get the user's trade history
def get_trade_history(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT symbol, action, amount, price, timestamp FROM trade_history WHERE username=? ORDER BY timestamp DESC", (username,))
    history = cursor.fetchall()

    conn.close()
    return history

# Function to check if user exists and create a new user if not
def ensure_user_exists(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT usdt_balance FROM users WHERE username=?", (username,))
    result = cursor.fetchone()

    if not result:
        # If user does not exist, create user with default USDT balance
        cursor.execute("INSERT INTO users (username, usdt_balance) VALUES (?, ?)", (username, 100000.0))  # Default balance: 100,000 USDT
        conn.commit()

    conn.close()

# Buy crypto
def buy_crypto(username, symbol, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Ensure the user exists
    ensure_user_exists(username)

    # Ensure symbol ends with 'USDT' for trading pair
    symbol_pair = symbol if symbol.endswith('USDT') else symbol + 'USDT'
    
    # Get price of the crypto
    try:
        price = float(get_price()[symbol_pair])
    except KeyError:
        raise ValueError(f"Price for symbol {symbol_pair} not found.")

    total_cost = amount * price

    # Check if user has enough USDT balance
    cursor.execute("SELECT usdt_balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]

    if balance < total_cost:
        raise ValueError("Insufficient USDT balance.")

    # Deduct from USDT balance and update holdings
    new_balance = balance - total_cost
    cursor.execute("UPDATE users SET usdt_balance=? WHERE username=?", (new_balance, username))

    cursor.execute("SELECT amount FROM wallet WHERE username=? AND symbol=?", (username, symbol))
    result = cursor.fetchone()

    if result:
        new_amount = result[0] + amount
        cursor.execute("UPDATE wallet SET amount=? WHERE username=? AND symbol=?", (new_amount, username, symbol))
    else:
        cursor.execute("INSERT INTO wallet (username, symbol, amount) VALUES (?, ?, ?)", (username, symbol, amount))

    # Add trade to history
    cursor.execute("INSERT INTO trade_history (username, symbol, action, amount, price) VALUES (?, ?, 'buy', ?, ?)",
                   (username, symbol, amount, price))

    conn.commit()
    conn.close()

# Sell crypto
def sell_crypto(username, symbol, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Ensure the user exists
    ensure_user_exists(username)

    # Ensure symbol ends with 'USDT' for trading pair
    symbol_pair = symbol if symbol.endswith('USDT') else symbol + 'USDT'
    
    # Get price of the crypto
    try:
        price = float(get_price()[symbol_pair])
    except KeyError:
        raise ValueError(f"Price for symbol {symbol_pair} not found.")

    # Check if user has enough crypto holdings to sell
    cursor.execute("SELECT amount FROM wallet WHERE username=? AND symbol=?", (username, symbol))
    result = cursor.fetchone()

    if not result or result[0] < amount:
        raise ValueError("Insufficient crypto holdings.")

    # Calculate USDT earned and update USDT balance
    total_value = amount * price
    cursor.execute("SELECT usdt_balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    new_balance = balance + total_value
    cursor.execute("UPDATE users SET usdt_balance=? WHERE username=?", (new_balance, username))

    # Update crypto holdings
    new_amount = result[0] - amount
    if new_amount > 0:
        cursor.execute("UPDATE wallet SET amount=? WHERE username=? AND symbol=?", (new_amount, username, symbol))
    else:
        cursor.execute("DELETE FROM wallet WHERE username=? AND symbol=?", (username, symbol))

    # Add trade to history
    cursor.execute("INSERT INTO trade_history (username, symbol, action, amount, price) VALUES (?, ?, 'sell', ?, ?)",
                   (username, symbol, amount, price))

    conn.commit()
    conn.close()

```

### `static\styles.css`
- **Lines:** 32
- **Last Modified:** 2024-10-19T17:22:41.016412

```
body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
    text-align: center;
}

h1 {
    background-color: #4c53af;
    color: white;
    padding: 20px;
}

table {
    margin: 20px auto;
    border-collapse: collapse;
    width: 80%;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
}

th {
    background-color: #4c53af;
    color: white;
}

tr:nth-child(even) {
    background-color: #f2f2f2;
}

```

### `stoploss.py`
- **Lines:** 44
- **Last Modified:** 2024-12-30T16:19:32.086369

```
import numpy as np
import pandas as pd
from binance.client import Client

api_key = 'qIjf0Zlm1UW33VnTSXDNTEGt4lgK6t03KHX5GLVqZycWJmjZdiiF4gLt6SG2iR8U'
api_secret = '9BzlnqOZsTlNJq1snlqutvyQvrDOkLvwZhKxYGZsmSqUzD2TKL5ZNggTUDm8cA7a'

client = Client(api_key, api_secret)

def fetch_crypto_data(symbol, interval, lookback):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df[['close']]

def calculate_ewma_volatility(prices, lambda_value):
    returns = prices.pct_change().dropna()
    return returns.ewm(span=1/lambda_value).std().iloc[-1]

def calculate_stop_loss(current_price, volatility, multiplier):
    return current_price - (volatility * current_price * multiplier)

def main():
    symbol = input("Enter the cryptocurrency symbol (e.g., BTCUSDT): ").upper()
    interval = "1h"
    lookback = 50
    lambda_value = 0.94
    multiplier = 2

    data = fetch_crypto_data(symbol, interval, lookback)
    current_price = data['close'].iloc[-1]
    volatility = calculate_ewma_volatility(data['close'], lambda_value)
    stop_loss = calculate_stop_loss(current_price, volatility, multiplier)

    print(f"Current Price: {current_price}")
    print(f"EWMA Volatility: {volatility:.5f}")
    print(f"Stop-Loss Level: {stop_loss:.2f}")

if __name__ == "__main__":
    main()

```

### `templates\index.html`
- **Lines:** 47
- **Last Modified:** 2024-10-16T13:59:18.921535

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Trading Sim</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <h1>Crypto Trading Simulator</h1>
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Price (USDT)</th>
                <th>Buy</th>
                <th>Sell</th>
            </tr>
        </thead>
        <tbody>
            {% for symbol, price in prices.items() %}
            <tr>
                <td>{{ symbol }}</td>
                <td>{{ price }}</td>
                <td>
                    <form action="{{ url_for('buy') }}" method="POST">
                        <input type="hidden" name="symbol" value="{{ symbol }}">
                        <input type="number" name="amount" placeholder="Amount" step="0.0001" required>
                        <button type="submit">Buy</button>
                    </form>
                </td>
                <td>
                    <form action="{{ url_for('sell') }}" method="POST">
                        <input type="hidden" name="symbol" value="{{ symbol }}">
                        <input type="number" name="amount" placeholder="Amount" step="0.0001" required>
                        <button type="submit">Sell</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <a href="{{ url_for('wallet') }}">View Wallet</a> | 
    <a href="{{ url_for('trade_history') }}">Trade History</a>
</body>
</html>

```

### `templates\login.html`
- **Lines:** 16
- **Last Modified:** 2024-10-19T16:53:25.378746

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <h1>Login</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Enter your username" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>

```

### `templates\trade_history.html`
- **Lines:** 36
- **Last Modified:** 2024-10-16T14:00:21.997940

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trade History</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <h1>Your Trade History</h1>
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Action</th>
                <th>Amount</th>
                <th>Price (USDT)</th>
                <th>Timestamp</th>
            </tr>
        </thead>
        <tbody>
            {% for symbol, action, amount, price, timestamp in history %}
            <tr>
                <td>{{ symbol }}</td>
                <td>{{ action }}</td>
                <td>{{ amount }}</td>
                <td>{{ price }}</td>
                <td>{{ timestamp }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <a href="{{ url_for('index') }}">Back to Trading</a>
</body>
</html>

```

### `templates\wallet.html`
- **Lines:** 52
- **Last Modified:** 2024-10-19T17:11:50.978144

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Wallet</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <h1>Your Wallet</h1>
    <div>
        <strong>USDT Balance: </strong> {{ balance }} USDT
        <br>
        <strong>Current Wallet Value: </strong> {{ wallet_value }} USDT
    </div>
    <h2>Crypto Holdings</h2>
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Amount</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for holding in holdings %}
            <tr>
                <td>{{ holding[0] }}</td>
                <td>{{ holding[1] }}</td>
                <td>
                    <form action="{{ url_for('sell') }}" method="POST">
                        <input type="hidden" name="symbol" value="{{ holding[0] }}">
                        <input type="number" name="amount" min="0" max="{{ holding[1] }}" step="0.0001" placeholder="Amount to sell" required>
                        <button type="submit">Sell</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <h2>Buy Crypto</h2>
    <form action="{{ url_for('buy') }}" method="POST">
        <input type="text" name="symbol" placeholder="Enter crypto symbol (e.g., BTCUSDT)" required>
        <input type="number" name="amount" min="0" step="0.0001" placeholder="Amount to buy" required>
        <button type="submit">Buy</button>
    </form>
    <br>
    <a href="{{ url_for('trade_history') }}">View Trade History</a>
    <br>
    <a href="{{ url_for('login') }}">Logout</a>
</body>
</html>

```
