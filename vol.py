
import os
import io
import schedule
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import re
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from prophet import Prophet
from datetime import datetime, timedelta
import cryptpandas as crp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import pickle
import vol
from config import *


# Initialize the Slack client
slack_token = "xoxp-8020284472341-8019421987622-8033267998518-8eb0beda40ffc3d70f55b98aa694a12f"
client = WebClient(token=slack_token)
user_id = "U080GCRATP1"

# Define the search query (e.g., a keyword in the file name)
query = "Data has just been released"
def search_messages():
    try:

        # Use the search.all method to find messages with the query
        response = client.search_all(query=query, count=1, sort="timestamp", sort_dir="desc")
        
        if response['messages']['matches']:
            # Get the latest matching message
            message = response['messages']['matches'][0]
            file_name = message['text']
            print(f"Found a message with file reference: {file_name}")
            
            
            # Process the message or file here
            # For example, call another function to access the Google Drive file
            
        else:
            print("No recent messages with the specified file keyword.")
            
    except SlackApiError as e:
        print(f"Error with search.all: {e.response['error']}")
    return file_name
text = search_messages()
# Regular expression patterns for file and passcode
start_file = text.find("'") + 1  # The first quote
end_file = text.find("'", start_file)  # The second quote after the first file

# Extract the file name using substring
file_name = text[start_file:end_file]
print(file_name)
# Find the starting and ending positions of the passcode
start_passcode = text.find("is '") + 4  # Skip 'is ' part to get the start of the passcode
end_passcode = text.find("'", start_passcode)  # The quote marking the end of the passcode

# Extract the passcode using substring
passcode = text[start_passcode:end_passcode]




# Path to your service account key
SERVICE_ACCOUNT_FILE = 'google.json'

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate using the service account file
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)


# Build the Drive API client
service = build('drive', 'v3', credentials=credentials)

def download_file_from_folder(folder_id, file_name, destination_path):
    # Search for the file by name within a specific folder
    results = service.files().list(
        q=f"'{folder_id}' in parents and name = '{file_name}'",  # Query to search within the folder
        fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])
    if not items:
        print(f"No file found with name {file_name} in folder {folder_id}")
        return
    
    # Assuming you want to download the first file found with that name
    file_id = items[0]['id']
    print(f"Found file: {items[0]['name']} with ID: {file_id}")
    
    # Get the request for the file
    request = service.files().get_media(fileId=file_id)
    
    # Set up a file handle for the downloaded file
    fh = io.FileIO(destination_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    # Download the file
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download progress: {int(status.progress() * 100)}%")

    print(f"Downloaded {destination_path}")

# Replace with the actual folder ID, file name, and desired download location
folder_id = '1ElVOO_4Plr24xEOmdqsINmIRM_y4M3_n'  # Folder ID from the URL
destination_path = 'stuff.crypt'  # Where you want to save the file locally

# Call the function
download_file_from_folder(folder_id, file_name, destination_path)



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialAnalysis:
    def __init__(self, 
                 short_term_period: int = 10, 
                 long_term_period: int = 200,
                 atr_period: int = 14,
                 volatility_impact: float = 0.5,
                 max_weight: float = 0.1,
                 forecast_days: int = 30):
        self.short_term_period = short_term_period
        self.long_term_period = long_term_period
        self.atr_period = atr_period
        self.volatility_impact = volatility_impact
        self.max_weight = max_weight
        self.forecast_days = forecast_days

    def calculate_moving_averages(self, data: pd.Series) -> Tuple[float, float]:
        """Calculate moving averages using proper rolling windows."""
        if len(data) < max(self.short_term_period, self.long_term_period):
            return np.nan, np.nan
        
        short_term_ma = data.rolling(window=self.short_term_period, min_periods=1).mean().iloc[-1]
        long_term_ma = data.rolling(window=self.long_term_period, min_periods=1).mean().iloc[-1]
        
        return short_term_ma, long_term_ma

    def calculate_true_range(self, data: pd.DataFrame) -> pd.Series:
        """Calculate True Range using actual OHLC data if available."""
        if all(col in data.columns for col in ['High', 'Low', 'Close']):
            high_low = data['High'] - data['Low']
            high_close = abs(data['High'] - data['Close'].shift(1))
            low_close = abs(data['Low'] - data['Close'].shift(1))
        else:
            close_std = data['Close'].rolling(window=20).std()
            high = data['Close'] + close_std
            low = data['Close'] - close_std
            high_low = high - low
            high_close = abs(high - data['Close'].shift(1))
            low_close = abs(low - data['Close'].shift(1))
        
        return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    def calculate_volatility(self, data: pd.Series) -> float:
        """Calculate volatility using dynamic standard deviation."""
        if len(data) < self.atr_period:
            return 0.0
            
        ohlc_data = pd.DataFrame({
            'Close': data,
            'High': data + data.rolling(window=20).std(),
            'Low': data - data.rolling(window=20).std()
        })
        
        tr = self.calculate_true_range(ohlc_data)
        atr = tr.rolling(window=self.atr_period).mean()
        
        normalized_atr = (atr / ohlc_data['Close']).tail(self.atr_period).mean()
        
        return float(normalized_atr) if not np.isnan(normalized_atr) else 0.0

    def normalize_values(self, values: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize values ensuring abs(weight) <= max_weight and sum(abs(weights)) = 1.
        Preserves signs of original values.
        """
        if not values:
            return {}
            
        values = {k: v for k, v in values.items() if not np.isnan(v) and not np.isinf(v)}
        
        if not values:
            return {}

        def normalize_preserving_signs(weights: Dict[str, float]) -> Dict[str, float]:
            total_abs = sum(abs(v) for v in weights.values())
            if total_abs == 0:
                equal_weight = 1.0 / len(weights)
                return {k: equal_weight for k in weights}
            return {k: v / total_abs for k, v in weights.items()}

        normalized = normalize_preserving_signs(values)
        
        while True:
            excess = {}
            need_redistribution = False
            
            for strategy, weight in normalized.items():
                if abs(weight) > self.max_weight:
                    excess[strategy] = abs(weight) - self.max_weight
                    normalized[strategy] = self.max_weight if weight > 0 else -self.max_weight
                    need_redistribution = True
            
            if not need_redistribution:
                break
                
            total_excess = sum(excess.values())
            recipients = {k: v for k, v in normalized.items() if k not in excess and abs(v) < self.max_weight}
            
            if not recipients:
                locked_weight = len(excess) * self.max_weight
                remaining_weight = 1.0 - locked_weight
                remaining_strategies = {k: v for k, v in normalized.items() if k not in excess}
                
                if remaining_strategies:
                    for k in remaining_strategies:
                        sign = 1 if normalized[k] >= 0 else -1
                        equal_remaining = (remaining_weight / len(remaining_strategies))
                        normalized[k] = sign * min(equal_remaining, self.max_weight)
                break
            
            recipient_total_abs = sum(abs(v) for v in recipients.values())
            if recipient_total_abs > 0:
                for strategy in recipients:
                    sign = 1 if normalized[strategy] >= 0 else -1
                    proportion = abs(normalized[strategy]) / recipient_total_abs
                    additional = proportion * total_excess
                    normalized[strategy] += sign * additional
            
            normalized = normalize_preserving_signs(normalized)
        
        return normalized

    def prepare_prophet_data(self, data: pd.Series) -> pd.DataFrame:
        """Prepare data for Prophet forecasting."""
        prophet_df = pd.DataFrame({
            'ds': pd.date_range(end=pd.Timestamp.now(), periods=len(data)),
            'y': data.values
        })
        return prophet_df

    def analyze_strategies(self, df: pd.DataFrame) -> Dict[str, float]:
        """Main analysis function combining traditional analysis with Prophet forecasting."""
        try:
            # Clean data first
            df_cleaned = df.copy()
            df_cleaned = df_cleaned.replace([np.inf, -np.inf], np.nan)
            df_cleaned = df_cleaned.fillna(method='ffill').fillna(method='bfill')
            
            strategies_analysis = {}
            
            for strategy in df_cleaned.columns:
                data = df_cleaned[strategy]
                
                if len(data) < max(self.short_term_period, self.long_term_period):
                    logger.warning(f"Insufficient data for strategy {strategy}")
                    continue
                
                # Traditional analysis
                short_ma, long_ma = self.calculate_moving_averages(data)
                volatility = self.calculate_volatility(data)
                
                if not np.isnan(short_ma) and not np.isnan(long_ma):
                    # Calculate trend signal (positive or negative)
                    trend_signal = (short_ma - long_ma) / long_ma
                    volatility_adjusted = trend_signal / (1 + self.volatility_impact * volatility)
                    
                    # Prophet analysis
                    try:
                        prophet_data = self.prepare_prophet_data(data)
                        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
                        model.fit(prophet_data)
                        future = model.make_future_dataframe(periods=self.forecast_days)
                        forecast = model.predict(future)
                        trend_growth = (forecast['trend'].iloc[-1] - forecast['trend'].iloc[0]) / forecast['trend'].iloc[0]
                        
                        # Combine traditional and Prophet signals
                        final_signal = (volatility_adjusted + trend_growth) / 2
                        strategies_analysis[strategy] = final_signal
                        
                    except Exception as e:
                        logger.warning(f"Prophet analysis failed for {strategy}, using only traditional signals")
                        strategies_analysis[strategy] = volatility_adjusted
            
            return self.normalize_values(strategies_analysis)
            
        except Exception as e:
            logger.error(f"Error in strategy analysis: {e}")
            raise
def setup_driver():
    """Set up and return the Chrome WebDriver with appropriate options"""
    options = webdriver.ChromeOptions()
    
    # Essential options
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    
    # Use existing Chrome profile
    options.add_argument(f'--user-data-dir={CHROME_USER_DATA_DIR}')
    options.add_argument('--profile-directory=Default')
    
    service = Service(CHROME_DRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def save_cookies(driver):
    """Save cookies after manual login"""
    # Create cookies directory if it doesn't exist
    if not os.path.exists('cookies'):
        os.makedirs('cookies')
    
    # Save cookies
    pickle.dump(driver.get_cookies(), open("cookies/google_cookies.pkl", "wb"))
    print("Cookies saved successfully!")

def load_cookies(driver):
    """Load saved cookies"""
    try:
        cookies = pickle.load(open("cookies/google_cookies.pkl", "rb"))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue
        return True
    except:
        return False

def manual_sign_in():
    """Guide user through manual sign-in process"""
    print("\n=== Manual Sign-In Process ===")
    print("1. A Chrome window will open")
    print("2. Please sign in to your Google account manually")
    print("3. Once signed in, press Enter in this console to continue")
    print("4. The script will save your login session for future use")
    input("Press Enter to start the process...")

def fill_form(driver, wait,data):
    """Fill and submit the form"""
    try:
        # Handle email recording checkbox
        # checkbox = wait.until(EC.element_to_be_clickable(
        #     (By.CSS_SELECTOR, 'div[role="checkbox"]')))
        # if not checkbox.is_selected():
        #     checkbox.click()
        # print("Handled checkbox")

        checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="checkbox"]')))
        if driver.execute_script("return arguments[0].getAttribute('aria-checked')", checkbox) != 'true':
            driver.execute_script("arguments[0].click();", checkbox)
        print("Handled checkbox")

        # Fill positions dict        
        text_field = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'textarea[aria-label="Your answer"]')))
        
        # Prepare the data to enter
        positions_data = data
        text_to_enter = json.dumps(positions_data, indent=2)

        # Clear the text field if needed
        driver.execute_script("arguments[0].value = '';", text_field)  # Clear using JavaScript
        
        # Use send_keys to input text
        text_field.click()  # Ensure focus
        text_field.send_keys(text_to_enter)
        print("Filled text field")

        # time.sleep(2)
        # Submit form
        # submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"][jsaction*="submit"]')))
        # submit_button.click()
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"][aria-label="Submit"]')))
        submit_button.click()
        print("Clicked submit button")
        
    except Exception as e:
        print(f"Form filling error: {str(e)}")
        raise


def main():
    try:
        analyzer = FinancialAnalysis(
            short_term_period=10,
            long_term_period=200,
            atr_period=14,
            volatility_impact=0.5,
            max_weight=0.1,
            forecast_days=30
        )
        
        # Load your data
        decrypted_df = crp.read_encrypted(path='stuff.crypt', password=passcode)
        df = decrypted_df
        results = analyzer.analyze_strategies(df)
        
        print(f"\nAnalysis run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nFinal Strategy Weights (Normalized, Prophet-Adjusted, Max |10%|):")
        total_abs_weight = 0
        negative_count = 0
        positive_count = 0
        
        for strategy, weight in sorted(results.items(), key=lambda x: x[1], reverse=True):
            print(f"{strategy}: {weight:.4f}")
            total_abs_weight += abs(weight)
            if weight < 0:
                negative_count += 1
            else:
                positive_count += 1
        
        print(f"\nTotal absolute weight: {total_abs_weight:.4f}")
        print(f"Max absolute weight: {max(abs(v) for v in results.values()):.4f}")
        print(f"Number of long positions: {positive_count}")
        print(f"Number of short positions: {negative_count}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    # Run the initial analysis immediately
    print("Starting initial analysis...")
    main()
    
    # Schedule the task to run every 19 minutes
    schedule.every(19).minutes.do(main)
    print(f"Scheduled to run every 19 minutes. Next run at: {datetime.now() + timedelta(minutes=19)}")
    
    # Keep running the schedule
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Sleep for 60 seconds before checking again (more efficient than 1 second)
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise



    