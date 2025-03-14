#!/usr/bin/env python
import sys
import os
import argparse
from web_server import main as run_web_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Computer Using Agent with remote web control")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the web server on")
    parser.add_argument("--ngrok", action="store_true", help="Use ngrok to expose the server to the internet")
    parser.add_argument("--ngrok-token", type=str, help="Your ngrok auth token")
    
    args = parser.parse_args()
    
    # Set environment variables if provided
    if args.ngrok_token:
        os.environ["NGROK_AUTH_TOKEN"] = args.ngrok_token
    
    # Print usage instructions
    print("=" * 70)
    print("Remote Computer Using Agent Control")
    print("=" * 70)
    print(f"Starting web server on port {args.port}")
    if args.ngrok:
        print("Attempting to create public URL with ngrok...")
        if not args.ngrok_token and not os.environ.get("NGROK_AUTH_TOKEN"):
            print("WARNING: No ngrok token provided. Free tier has limitations.")
            print("To set a token, use --ngrok-token or set NGROK_AUTH_TOKEN environment variable")
    else:
        print(f"Access locally at: http://localhost:{args.port}")
        print("To create a public URL, restart with --ngrok flag")
    print("=" * 70)
    
    # Convert arguments to the format expected by web_server.main
    sys.argv = [sys.argv[0]]
    if args.port != 5000:
        sys.argv.extend(["--port", str(args.port)])
    if args.ngrok:
        sys.argv.append("--ngrok")
    
    # Run the web server
    run_web_server() 