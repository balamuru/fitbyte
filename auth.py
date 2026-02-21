import os
import json
import base64
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("FITBIT_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("FITBIT_REDIRECT_URI", "http://localhost:8080/callback")

AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
SCOPES = "activity heartrate location nutrition profile settings sleep social weight"
TOKEN_FILE = "token.json"

auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed_url = urllib.parse.urlparse(self.path)
        
        if parsed_url.path == "/callback":
            params = urllib.parse.parse_qs(parsed_url.query)
            if "code" in params:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication successful!</h1><p>You can close this window and return to the terminal.</p></body></html>")
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication failed!</h1><p>No authorization code received.</p></body></html>")
        else:
            self.send_response(404)
            self.end_headers()


def get_authorization_code():
    global auth_code
    
    # Extract port from REDIRECT_URI
    parsed_redirect = urllib.parse.urlparse(REDIRECT_URI)
    port = parsed_redirect.port if parsed_redirect.port else 8080
    
    # Construct Authorization URL
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    print(f"Opening browser to authorize: {url}")
    webbrowser.open(url)
    
    # Start local server to listen for the callback
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    print(f"Listening for callback on port {port}...")
    
    # Handle exactly one request
    server.handle_request()
    
    return auth_code

def exchange_code_for_token(code):
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    base64_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "clientId": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    
    print("Exchanging authorization code for token...")
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=4)
        print(f"Token successfully saved to {TOKEN_FILE}")
        return token_data
    else:
        print(f"Failed to retrieve token: {response.status_code} - {response.text}")
        return None

def authenticate():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: FITBIT_CLIENT_ID and FITBIT_CLIENT_SECRET must be set in the .env file.")
        return False
        
    code = get_authorization_code()
    if code:
        token = exchange_code_for_token(code)
        return token is not None
    return False

if __name__ == "__main__":
    authenticate()
