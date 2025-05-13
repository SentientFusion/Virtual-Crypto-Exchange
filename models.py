import sqlite3
from binance.client import Client
import os # Import the os module

DB_NAME = 'crypto_sim.db'

# Get API key and secret from environment variables
API_KEY = os.environ.get('BINANCE_API_KEY')
API_SECRET = os.environ.get('BINANCE_API_SECRET')

# Ensure API key and secret are loaded
if not API_KEY or not API_SECRET:
    raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET environment variables must be set.")

# Initialize the Binance API client using environment variables
binance_client = Client(api_key=API_KEY, api_secret=API_SECRET)

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
                # Convert price to float
                try:
                    prices[symbol] = float(item['price'])
                except ValueError:
                    print(f"Warning: Could not convert price to float for {symbol}: {item['price']}")
                    prices[symbol] = 0.0 # Set to 0 if conversion fails
    except Exception as e:
        print(f"Error fetching prices from Binance: {e}")
        # Depending on how critical prices are, you might want to re-raise or return empty
        return {} # Return empty dict on error

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
    prices = get_price() # This now fetches all USDT prices

    total_value = 0.0

    for symbol, amount in holdings:
        # Ensure symbol ends with 'USDT' for price lookup
        symbol_pair = symbol if symbol.endswith('USDT') else symbol + 'USDT'

        # Get the current price of the crypto from the fetched prices
        price = prices.get(symbol_pair) # Use .get() to avoid KeyError

        if price is not None and price > 0: # Check if price was found and is positive
            value = amount * price
            total_value += value
            # print(f"Symbol: {symbol_pair}, Amount: {amount}, Price: {price}, Value: {value}")  # Debug statement
        else:
            # print(f"Warning: No valid price found for {symbol_pair} in fetched data.")  # Debug statement
             pass # Suppress warning during normal operation if price not found

    # print(f"Total Wallet Value for {username}: {total_value}")  # Debug statement
    return total_value


# Function to get the user's USDT balance
def get_user_balance(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT usdt_balance FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        # Handle case where user might not exist yet, although ensure_user_exists should prevent this
        return 0.0 # Or None, depending on how you want to handle it


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
    prices = get_price() # Fetch prices
    price = prices.get(symbol_pair) # Get price for specific pair

    if price is None or price <= 0:
        raise ValueError(f"Price for symbol {symbol_pair} not found or is invalid.")

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
    prices = get_price() # Fetch prices
    price = prices.get(symbol_pair) # Get price for specific pair

    if price is None or price <= 0:
        raise ValueError(f"Price for symbol {symbol_pair} not found or is invalid.")


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

# You might want to call init_db() when the application starts
# to ensure the database and tables are created if they don't exist.
# Add this call near the beginning of app.py or in a separate setup script.