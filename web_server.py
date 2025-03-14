from flask import Flask, render_template, request
from flask_socketio import SocketIO
import threading
import argparse
import os
import logging
import time
from agent.agent import Agent
from computers import MacComputer
from pyngrok import ngrok

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('web_server')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
agent = None
agent_thread = None
input_queue = []
output_buffer = []

class OutputCapture:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.captured_text = ""
    
    def write(self, text):
        # Write to the original stdout
        self.original_stdout.write(text)
        
        # Also capture the text
        self.captured_text += text
        
        # Send the text to the client via WebSocket
        socketio.emit('output', {'data': text})
        
    def flush(self):
        self.original_stdout.flush()

def agent_worker():
    global agent
    
    while True:
        if input_queue:
            user_input = input_queue.pop(0)
            logger.info(f"Processing user input: {user_input}")
            
            # Capture output during processing
            import sys
            original_stdout = sys.stdout
            capture = OutputCapture(original_stdout)
            sys.stdout = capture
            
            try:
                # Send a message to indicate processing has started
                socketio.emit('status', {'data': 'Processing...'})
                
                # Create input items for agent
                items = [{"role": "user", "content": user_input}]
                
                # Run the agent
                output_items = agent.run_full_turn(
                    items,
                    print_steps=True,
                    show_images=False,
                    debug=False,
                )
                
                # Store agent output
                output_buffer.extend(output_items)
                
                # Send a message to indicate processing is complete
                socketio.emit('status', {'data': 'Ready'})
                
            except Exception as e:
                logger.error(f"Error running agent: {str(e)}")
                import traceback
                traceback.print_exc()
                socketio.emit('error', {'data': str(e)})
                socketio.emit('status', {'data': 'Error'})
            
            # Restore stdout
            sys.stdout = original_stdout
        
        # Sleep to prevent CPU hogging
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    socketio.emit('status', {'data': 'Connected'})
    
    # Send any buffered output
    for item in output_buffer:
        if item.get("role") == "assistant" and item.get("content"):
            for content in item["content"]:
                if content.get("type") == "text":
                    socketio.emit('output', {'data': content["text"] + "\n"})

@socketio.on('input')
def handle_input(data):
    user_input = data.get('data', '')
    logger.info(f"Received input: {user_input}")
    
    if user_input.strip():
        input_queue.append(user_input)
        socketio.emit('output', {'data': f"> {user_input}\n"})

def acknowledge_safety_check_callback(message):
    """Callback for safety checks - always acknowledges in this implementation."""
    logger.info(f"Safety check: {message}")
    socketio.emit('safety_check', {'message': message})
    return True  # Auto-acknowledge all safety checks

def create_templates_directory():
    """Create templates directory if it doesn't exist"""
    if not os.path.exists('templates'):
        os.makedirs('templates')

def create_html_template():
    """Create the HTML template file"""
    template_path = os.path.join('templates', 'index.html')
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Remote CUA Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
        }
        #status {
            margin: 10px 0;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            text-align: center;
        }
        .ready {
            background-color: #27ae60;
            color: white;
        }
        .processing {
            background-color: #f39c12;
            color: white;
        }
        .error {
            background-color: #e74c3c;
            color: white;
        }
        #output {
            width: 100%;
            height: 400px;
            background-color: #2c3e50;
            color: #ecf0f1;
            font-family: monospace;
            padding: 10px;
            border-radius: 4px;
            overflow-y: auto;
            margin-bottom: 10px;
            white-space: pre-wrap;
        }
        #input-form {
            display: flex;
            margin-bottom: 20px;
        }
        #input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px 0 0 4px;
            font-size: 16px;
        }
        #send {
            padding: 10px 15px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-size: 16px;
        }
        #send:hover {
            background-color: #2980b9;
        }
        .safety-check {
            background-color: #e74c3c;
            color: white;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Remote CUA Control</h1>
        <div id="status" class="ready">Ready</div>
        <div id="output"></div>
        <form id="input-form">
            <input type="text" id="input" placeholder="Enter your command..." autocomplete="off">
            <button type="submit" id="send">Send</button>
        </form>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        const outputDiv = document.getElementById('output');
        const inputField = document.getElementById('input');
        const inputForm = document.getElementById('input-form');
        const statusDiv = document.getElementById('status');
        
        // Connect to WebSocket
        socket.on('connect', function() {
            console.log('Connected to server');
            updateStatus('Connected');
        });
        
        // Handle output from server
        socket.on('output', function(data) {
            outputDiv.innerHTML += data.data;
            outputDiv.scrollTop = outputDiv.scrollHeight;
        });
        
        // Handle status updates
        socket.on('status', function(data) {
            updateStatus(data.data);
        });
        
        // Handle errors
        socket.on('error', function(data) {
            console.error('Error:', data.data);
            outputDiv.innerHTML += `<span style="color: #e74c3c;">Error: ${data.data}</span>\n`;
            outputDiv.scrollTop = outputDiv.scrollHeight;
        });
        
        // Handle safety checks
        socket.on('safety_check', function(data) {
            outputDiv.innerHTML += `<div class="safety-check">Safety Check: ${data.message}</div>\n`;
            outputDiv.scrollTop = outputDiv.scrollHeight;
        });
        
        // Send input to server
        inputForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const value = inputField.value.trim();
            if (value) {
                socket.emit('input', {data: value});
                inputField.value = '';
            }
        });
        
        function updateStatus(status) {
            statusDiv.textContent = status;
            statusDiv.className = '';
            
            if (status === 'Ready' || status === 'Connected') {
                statusDiv.classList.add('ready');
            } else if (status === 'Processing...') {
                statusDiv.classList.add('processing');
            } else {
                statusDiv.classList.add('error');
            }
        }
    </script>
</body>
</html>
"""
    
    with open(template_path, 'w') as f:
        f.write(html_content)

def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(description="Web interface for Computer Using Agent")
        parser.add_argument("--port", type=int, default=5000, help="Port to run the web server on")
        parser.add_argument("--ngrok", action="store_true", help="Use ngrok to expose the server to the internet")
        args = parser.parse_args()
    
    global agent
    
    # Create the templates directory and HTML file
    create_templates_directory()
    create_html_template()
    
    # Initialize the agent
    with MacComputer() as computer:
        agent = Agent(
            computer=computer,
            acknowledge_safety_check_callback=acknowledge_safety_check_callback,
        )
        
        # Start the agent worker thread
        global agent_thread
        agent_thread = threading.Thread(target=agent_worker, daemon=True)
        agent_thread.start()
        
        if args.ngrok:
            try:
                # Initialize ngrok
                ngrok_token = os.environ.get("NGROK_AUTH_TOKEN")
                if not ngrok_token:
                    logger.warning("NGROK_AUTH_TOKEN not found in environment variables. "
                                  "Ngrok connection may be limited.")
                else:
                    ngrok.set_auth_token(ngrok_token)
                
                # Open a tunnel to the specified port
                http_tunnel = ngrok.connect(args.port)
                public_url = http_tunnel.public_url
                logger.info(f"Ngrok tunnel established at: {public_url}")
                print(f"=" * 50)
                print(f"Access the remote control at: {public_url}")
                print(f"=" * 50)
            except Exception as e:
                logger.error(f"Failed to establish ngrok tunnel: {e}")
                print("Failed to establish ngrok tunnel. Running on local network only.")
        
        # Start the Flask server
        socketio.run(app, host='0.0.0.0', port=args.port, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    main() 