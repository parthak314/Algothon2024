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
from vol import *
from config import *
import sys

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

def fill_form(driver, wait, positions_data):
    """Fill and submit the form"""
    try:
        checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="checkbox"]')))
        if driver.execute_script("return arguments[0].getAttribute('aria-checked')", checkbox) != 'true':
            driver.execute_script("arguments[0].click();", checkbox)
        print("Handled checkbox")

        # Fill positions dict        
        text_field = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'textarea[aria-label="Your answer"]')))
        
        # Prepare the data to enter
        text_to_enter = json.dumps(positions_data, indent=2)

        # Clear the text field if needed
        driver.execute_script("arguments[0].value = '';", text_field)  # Clear using JavaScript
        
        # Use send_keys to input text
        text_field.click()  # Ensure focus
        text_field.send_keys(text_to_enter)
        print("Filled text field")

        time.sleep(2)
        # Submit form
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"][aria-label="Submit"]')))
        submit_button.click()
        print("Clicked submit button")
        
    except Exception as e:
        print(f"Form filling error: {str(e)}")
        raise

def main(positions_data):
    driver = None
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 20)
        
        # First try using saved cookies
        if os.path.exists('cookies/google_cookies.pkl'):
            print("Found saved cookies, attempting to use them...")
            driver.get('https://google.com')  # Load Google first
            load_cookies(driver)
            driver.get(FORM_URL)
            
            # Check if we're still signed in
            time.sleep(3)
            if "Sign in" in driver.page_source:
                print("Saved cookies expired, need manual sign-in")
                manual_sign_in()
                driver.get(FORM_URL)
                save_cookies(driver)
        else:
            print("No saved cookies found")
            manual_sign_in()
            driver.get(FORM_URL)
            save_cookies(driver)
        
        # Fill and submit form
        print("Filling form...")
        fill_form(driver, wait, positions_data)
        
        print("Waiting for submission confirmation...")
        time.sleep(3)
        print("Form submitted successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if driver:
            print("Current URL:", driver.current_url)

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Retrieve the data passed as an argument
        positions_data = sys.argv[1]
        main(positions_data)
    else:
        print("No data received.")