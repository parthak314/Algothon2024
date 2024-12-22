# Algothon 2024

## Overview

This project is designed to automate the process of downloading encrypted financial data, decrypting it, analyzing it using various financial strategies, and submitting the results to a Google Form. The project leverages several technologies including Slack API, Google Drive API, Selenium for web automation, and Prophet for forecasting.

## Project Structure

- `config.py`: Contains configuration details such as Chrome driver paths and Google Form URL.
- `gFormAuto.py`: Handles the automation of filling and submitting the Google Form.
- `movavgtest.py`: Main script for downloading, decrypting, and analyzing financial data.
- `vol.py`: Similar to `movavgtest.py` but includes additional functionality for Slack notifications.
- `top.py`: Orchestrates the execution of `vol.py` and `gFormAuto.py`.
- `google.json`: Service account credentials for accessing Google Drive.
- `stuff.crypt`: Encrypted financial data file.
- `cookies/`: Directory to store cookies for maintaining session state.
- `.gitignore`: Specifies files and directories to be ignored by Git.

## Setup

1. **Install Dependencies**:
   Ensure you have the required Python packages installed. You can use `pip` to install them:
   ```sh
   pip install -r requirements.txt

2. **Configure Chrome Driver**: Update the paths in config.py to point to your Chrome driver and user data directory:
```python
# config.py
CHROME_DRIVER_PATH = r'path\to\chromedriver.exe'
CHROME_USER_DATA_DIR = r'path\to\chrome\user\data'
```
3. Google Service Account: Place your google.json file in the project directory. This file contains the credentials for accessing Google Drive.

4. Slack API Token: Update the Slack API token in movavgtest.py and vol.py:
```python
slack_token = "your-slack-token"
```

## Usage
1. Run the Analysis: Execute top.py to start the process. This script will run vol.py to download and analyse the data, and then run gFormAuto.py to submit the results to the Google Form.

```python
python vol.py
```

2. Manual Sign-In: The first time you run the script, you will need to manually sign in to your Google account. Follow the instructions in the console to complete the sign-in process.

## Authors
Tejas Bantupalli, Parth Khanna, Arjun Watve


