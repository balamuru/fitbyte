import os
import json
import base64
import requests
import datetime
from dotenv import load_dotenv

import db

load_dotenv()

CLIENT_ID = os.environ.get("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("FITBIT_CLIENT_SECRET")

TOKEN_URL = "https://api.fitbit.com/oauth2/token"
API_BASE_URL = "https://api.fitbit.com/1/user/-"
TOKEN_FILE = "token.json"

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)

def save_token(token_data):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=4)

def refresh_tokenIfNeeded(token_data):
    # For robust production use, decode the 'expires_in' along with a saved timestamp
    # But for a simple script, we can just attempt to refresh if we suspect it's old 
    # or just refresh when an API call fails with 401. 
    # Here, we'll try a proactive refresh flow if a call fails, or we can just try refreshing it now.
    pass # implemented inside api request helper

def make_api_request(endpoint, token_data):
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        print("Access token expired. Attempting to refresh...")
        token_data = refresh_oauth_token(token_data)
        if token_data:
            # Retry with new token
            headers["Authorization"] = f"Bearer {token_data['access_token']}"
            response = requests.get(url, headers=headers)
        else:
            print("Failed to refresh token. Manual re-authentication required.")
            return None
            
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Request to {endpoint} failed: {response.status_code} - {response.text}")
        return None

def refresh_oauth_token(token_data):
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    base64_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": token_data['refresh_token']
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        new_token_data = response.json()
        save_token(new_token_data)
        return new_token_data
    else:
        print(f"Token refresh failed: {response.status_code} - {response.text}")
        return None

def fetch_and_store_profile(token_data):
    print("Fetching user profile...")
    profile_response = make_api_request("profile.json", token_data)
    
    if profile_response and 'user' in profile_response:
        db.upsert_user_profile(profile_response['user'])
        print("Profile saved to database.")

def fetch_and_store_daily_activity(token_data, date_str=None):
    if not date_str:
        # Use today's date in YYYY-MM-DD format
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
    print(f"Fetching daily activity for {date_str}...")
    activity_response = make_api_request(f"activities/date/{date_str}.json", token_data)
    
    if activity_response and 'summary' in activity_response:
        summary = activity_response['summary']
        
        # Fitbit distances are in an array, we want "total"
        distance = 0.0
        if 'distances' in summary:
            for d in summary['distances']:
                if d.get('activity') == 'total':
                    distance = d.get('distance', 0.0)
                    break
                    
        metrics = {
            'steps': summary.get('steps', 0),
            'distance': distance,
            'calories_out': summary.get('caloriesOut', 0),
            'very_active_minutes': summary.get('veryActiveMinutes', 0),
            'fairly_active_minutes': summary.get('fairlyActiveMinutes', 0),
            'lightly_active_minutes': summary.get('lightlyActiveMinutes', 0),
            'sedentary_minutes': summary.get('sedentaryMinutes', 0),
            'resting_heart_rate': summary.get('restingHeartRate', None)
        }
        
        db.upsert_daily_activity(date_str, metrics)
        print(f"Activity for {date_str} saved to database.")

def run_ingestion():
    db.init_db() # Ensure DB is initialized
    
    token_data = load_token()
    if not token_data:
        print("Error: No authentication token found. Please run auth.py first to authenticate.")
        return
        
    fetch_and_store_profile(token_data)
    fetch_and_store_daily_activity(token_data)
    print("Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()
