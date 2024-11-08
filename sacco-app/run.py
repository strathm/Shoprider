from app import app, socketio  # Import both 'app' and 'socketio' from your __init__.py

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)  # Use socketio.run to start the app
