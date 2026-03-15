from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Get port from environment (Render uses PORT env variable)
    port = int(os.getenv('PORT', 5002))
    
    # Disable debug in production
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    
    print(f"🚀 Starting server on port {port} (debug={debug_mode})")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
