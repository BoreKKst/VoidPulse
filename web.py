import os
from flask import Flask
import threading
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return "VoidPulse Bot is running perfectly!", 200

def run():
    # Render сам передает порт через переменные окружения, ловим его здесь:
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
