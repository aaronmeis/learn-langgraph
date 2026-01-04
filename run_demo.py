"""
Simple HTTP server to run the demo.html page with agent videos
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow local file access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 60)
    print("LangGraph Demo - Agent Videos")
    print("=" * 60)
    print(f"\nStarting server on http://localhost:{PORT}")
    print(f"Serving from: {script_dir}")
    print("\nThe demo page will open automatically in your browser.")
    print("Press Ctrl+C to stop the server.\n")
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            # Open browser automatically
            url = f"http://localhost:{PORT}/demo.html"
            print(f"Opening: {url}")
            webbrowser.open(url)
            
            print(f"\nServer running at http://localhost:{PORT}/")
            print("Available pages:")
            print(f"  - Demo with videos: http://localhost:{PORT}/demo.html")
            print(f"  - Pipeline diagram: http://localhost:{PORT}/advanced_pipeline_diagram.html")
            print("\nPress Ctrl+C to stop...\n")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nError: Port {PORT} is already in use.")
            print(f"Try closing other applications or use a different port.")
        else:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()

