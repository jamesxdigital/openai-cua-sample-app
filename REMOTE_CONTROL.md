# Remote Control for Computer Using Agent

This feature allows you to control the Computer Using Agent (CUA) remotely from any device with a web browser (like your phone or tablet), without interfering with what the agent is doing on your screen.

## Why Remote Control?

When using the Computer Using Agent in terminal mode, typing commands in the same terminal can interfere with what the agent is doing on your screen. By using remote control:

1. You can input commands from any device
2. You won't disrupt the agent's actions by typing in the terminal
3. You can monitor the agent's progress remotely

## Setup

### Prerequisites

- Python 3.7+
- Flask and Flask-SocketIO (installed via `pip install flask flask-socketio`)
- PyNgrok (installed via `pip install pyngrok`)
- Optional: Ngrok account for public access (free or paid)

### Running Locally (Same Network)

To run the web interface on your local network (accessible from devices on the same WiFi):

```bash
python remote_cli.py
```

This will start a web server on port 5000. You can access it from:
- Your computer: http://localhost:5000
- Other devices on the same network: http://YOUR_IP_ADDRESS:5000 (where YOUR_IP_ADDRESS is your computer's local IP)

### Running with Public Access (Any Network)

To make the interface accessible from anywhere (including cellular networks):

1. Sign up for a free ngrok account at https://ngrok.com/
2. Get your auth token from the ngrok dashboard
3. Run with the ngrok flag:

```bash
python remote_cli.py --ngrok --ngrok-token YOUR_NGROK_TOKEN
```

The script will output a public URL that you can access from any device, anywhere.

## Usage

1. Open the provided URL in a web browser
2. Enter your instructions in the input field
3. The agent will execute the instructions on your computer
4. View the output and status in the web interface

## Notes

- The agent operates on your physical computer, so be careful with the instructions you provide
- All safety checks are automatically acknowledged in the web interface
- The free tier of ngrok has limitations on connection time and number of connections
- For security reasons, don't leave the remote control running unattended

## Troubleshooting

- If you encounter connection issues, ensure your firewall isn't blocking the port
- If ngrok fails to connect, verify your auth token and internet connection
- If the agent isn't responding, check the terminal where you launched the remote control for error messages 