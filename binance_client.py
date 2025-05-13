from binance.client import Client
import os

# Get API key and secret from environment variables
API_KEY = os.environ.get('BINANCE_API_KEY')
API_SECRET = os.environ.get('BINANCE_API_SECRET')

# Ensure API key and secret are loaded
if not API_KEY or not API_SECRET:
    raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET environment variables must be set.")

client = Client(API_KEY, API_SECRET)

def get_all_crypto_usdt_pairs():
    # Fetch all symbols and filter for crypto-USDT pairs
    exchange_info = client.get_exchange_info()
    pairs = [s['symbol'] for s in exchange_info['symbols'] if 'USDT' in s['symbol']]
    return pairs

def get_price(symbol):
    # Get the latest price for the specified symbol
    # Ensure symbol ends with 'USDT' for trading pair if it doesn't already
    symbol_pair = symbol if symbol.endswith('USDT') else symbol + 'USDT'
    avg_price = client.get_avg_price(symbol=symbol_pair)
    return float(avg_price['price']) # Convert price to float here

# Optional: Add error handling for get_price if symbol is invalid
# try:
#     avg_price = client.get_avg_price(symbol=symbol_pair)
#     return float(avg_price['price'])
# except Exception as e:
#     print(f"Error fetching price for {symbol_pair}: {e}")
#     return None # Or raise a more specific exception