from fyers_apiv3 import fyersModel
import pandas as pd
import datetime as dt
import os

client_id = "CNPWV0DNSM-100"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb2I2cjlmODFqcmRvNjFoaG41bFRmWnVvMU5wTk5FNXM3dFAxOG55N0pzT0MyS3prUkxOcHE0VVZsV2JIelh4SjFaamJ5aC1sam5HX29IT1VJVmJMNlNTRHg1RDNOSzRlVC00OXE5cEtrS0xNaG44bz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiIzMGY5YjQ2NDFmYTEzNzFjZDhlOTVkYzZkYzRmMDg2OTkwMTRiNTRhNDlkNDdjOTA1ZTg3YmQ2OCIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFAwNzc5NCIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzUyMTkzODAwLCJpYXQiOjE3NTIxNDg3MzMsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc1MjE0ODczMywic3ViIjoiYWNjZXNzX3Rva2VuIn0.VQRqnIY7F6Hbb0qXXkoIMAn2qy_5OpwAbjbWnp4KZcg"

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

# Make a request to get the user profile information
response = fyers.get_profile()


# 1. Get response from Fyers Option Chain API
response = fyers.optionchain(data={"symbol": "NSE:NIFTY50-INDEX", "strikecount": 8})

# 2. Create raw DataFrame
df = pd.DataFrame(response['data']['optionsChain'])

# 3. DEBUG: Check size and structure
print("Total rows in API response:", len(df))
print("Sample rows:\n", df.head())

# 4. Filter: Only valid CE/PE option rows (exclude index row where strike_price == -1 or missing)
df = df[df['option_type'].isin(['CE', 'PE']) & (df['strike_price'] != -1)]

# 5. Drop rows with missing symbols
df = df.dropna(subset=['symbol'])

# 6. Reset index
df = df.reset_index(drop=True)

# 7. Extract and display only 'symbol'
symbol_df = df[['symbol']]

# 8. Debug count
print("Total CE/PE symbols extracted:", len(symbol_df))
# Continuing from previous code
symbol_tuple = tuple(df['symbol'])

# Optional: print or return
print(symbol_tuple)





# Time range: now and 60 days ago
now_epoch = int(dt.datetime.now().timestamp())
prev_epoch = int((dt.datetime.now() - dt.timedelta(days=60)).timestamp())

# CSV save folder
save_path = r'C:\Users\Pramod shah\Desktop\SYMBOL FETCHING\NIFTY100725'
os.makedirs(save_path, exist_ok=True)  # Create folder if it doesn't exist

# Loop over all symbols
for symbol in symbol_tuple:
    print(f"Fetching data for: {symbol}")

    # Prepare API request
    data = {
        "symbol": symbol,
        "resolution": "5S",           # 1-minute candles
        "date_format": "0",
        "range_from": prev_epoch,
        "range_to": now_epoch,
        "cont_flag": "1"
    }

    try:
        response = fyers.history(data=data)

        # Check for errors
        if 'candles' not in response or not response['candles']:
            print(f"No data returned for {symbol}")
            continue

        # Convert to DataFrame
        df = pd.DataFrame(response['candles'])
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        # Format timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        df['timestamp'] = df['timestamp'].dt.tz_localize(None)
        df = df.set_index('timestamp')

        # Prepare filename (clean symbol name for filename)
        filename = symbol.replace("NSE:", "") + "_5sec.csv"
        filepath = os.path.join(save_path, filename)

        # Save to CSV
        df.to_csv(filepath)
        print(f"Saved: {filepath}")

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")

print(" All done at:", dt.datetime.now())



