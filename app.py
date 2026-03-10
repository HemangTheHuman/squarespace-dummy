import os
import secrets
import urllib.parse
import base64
import requests
from flask import Flask, render_template, request, jsonify, redirect, session
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
# A secret key is required for using Flask's session object
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

@app.route('/')
def index():
    # Check for OAuth callback parameters
    code = request.args.get('code')
    state = request.args.get('state')
    
    if code or state:
        # Verify the state parameter to prevent CSRF attacks
        saved_state = session.get('oauth_state')
        if not saved_state or state != saved_state:
            return jsonify({'error': 'State verification failed. CSRF attack detected.'}), 403
            
        # Clear the state from session as it's no longer needed
        session.pop('oauth_state', None)
        
        # The state is verified, and we have the code. 
        # Exchange this code for an access token.
        client_id = os.environ.get('client_id')
        secret = os.environ.get('secret')
        redirect_uri = 'https://squarespace-dummy.vercel.app'
        
        # Build Authorization header: Base64 encode "client_id:secret"
        auth_string = f"{client_id}:{secret}"
        encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        token_url = 'https://login.squarespace.com/api/1/login/oauth/provider/tokens'
        headers = {
            'Authorization': f"Basic {encoded_auth}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'SquarespaceDemoApp/1.0'
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Extract the new access token
            access_token = token_data.get('access_token')
            
            # Query the Squarespace Authorization API to get website details
            website_url = "https://api.squarespace.com/1.0/authorization/website"
            website_headers = {
                'Authorization': f"Bearer {access_token}",
                'User-Agent': 'SquarespaceDemoApp/1.0',
                'Content-Type': 'application/json'
            }
            
            website_response = requests.get(website_url, headers=website_headers)
            website_response.raise_for_status()
            website_info = website_response.json()
            
            # Save token to session if needed for further calls
            session['access_token'] = access_token
            
            # Render the landing page with the website info
            return render_template('index.html', website_info=website_info)
            
        except requests.exceptions.RequestException as e:
            # Handle potential None type for response if the request completely fails
            error_details = str(e)
            try:
                if 'response' in locals() and response is not None:
                    error_details = response.text
            except Exception:
                pass
                
            return jsonify({
                'error': 'Failed to retrieve access token.',
                'details': error_details
            }), 400

    return render_template('index.html')

@app.route('/api/verify', methods=['POST'])
def verify_project_key():
    data = request.get_json()
    project_key = data.get('project_key')
    
    # Simulate an external API call delay
    time.sleep(1.5)
    
    # Basic validation (just making sure it's not empty for this mock)
    if not project_key or len(project_key) < 5:
        return jsonify({
            'status': 'error',
            'message': 'Invalid project key. Must be at least 5 characters.'
        }), 400
        
    # Mock data received from "external cloud API"
    mock_data = {
        'status': 'success',
        'data': {
            'organization': 'Acme Corp',
            'environment': 'Production',
            'plan': 'Enterprise',
            'region': 'us-east-1',
            'verified_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    return jsonify(mock_data), 200

@app.route('/login/squarespace')
def login_squarespace():
    # Load client ID from .env
    client_id = os.environ.get('client_id')
    
    # Ideally, replace this with your environment's actual callback redirect URL
    redirect_uri = 'https://squarespace-dummy.vercel.app'  
    
    # Generate a random state string to prevent CSRF attacks
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    # Required scope for API access (comma-separated list of values)
    scope = 'website.inventory,website.orders'
    
    auth_url = 'https://login.squarespace.com/api/1/login/oauth/provider/authorize'
    
    # Setup the required squarepsace parameters
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': state,
        'access_type': 'offline'
    }
    
    # If the user is logged into squarespace, their website_id will be sent to the initiate URL.
    # Pass it along. If not passed, the user selects their site on the squarespace auth page.
    website_id = request.args.get('website_id')
    if website_id:
        params['website_id'] = website_id
        
    # Construct complete authorization URL
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    # Redirect to Squarespace authorization page
    return redirect(url)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
