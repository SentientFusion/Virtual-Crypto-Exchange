import numpy as np
import pandas as pd
from binance.client import Client
import os # Import the os module

# Get API key and secret from environment variables
api_key = os.environ.get('BINANCE_API_KEY')
api_secret = os.environ.get('BINANCE_API_SECRET')

# Ensure API key and secret are loaded
if not api_key or not api_secret:
     raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET environment variables must be set.")


client = Client(api_key, api_secret)

def fetch_crypto_data(symbol, interval, lookback):
    # Ensure symbol ends with 'USDT' for trading pair
    symbol_pair = symbol if symbol.endswith('USDT') else symbol + 'USDT'
    klines = client.get_klines(symbol=symbol_pair, interval=interval, limit=lookback)
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df[['close']]

def calculate_ewma_volatility(prices, lambda_value):
    returns = prices.pct_change().dropna()
    # Check if returns is empty before calculating std
    if returns.empty:
        return 0.0 # Or handle appropriately if no data
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
    if data.empty:
        print(f"Could not fetch data for {symbol}. Please check the symbol or try a different interval/lookback.")
        return

    current_price = data['close'].iloc[-1]
    volatility = calculate_ewma_volatility(data['close'], lambda_value)
    stop_loss = calculate_stop_loss(current_price, volatility, multiplier)

    print(f"Current Price: {current_price}")
    print(f"EWMA Volatility: {volatility:.5f}")
    print(f"Stop-Loss Level: {stop_loss:.2f}")

if __name__ == "__main__":
    # Add a check for environment variables before running main
    if os.environ.get('BINANCE_API_KEY') and os.environ.get('BINANCE_API_SECRET'):
        main()
    else:
        print("Error: BINANCE_API_KEY and BINANCE_API_SECRET environment variables must be set to run this script.")