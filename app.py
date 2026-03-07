from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__)

@app.route('/')
def index():
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
