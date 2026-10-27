import os
from flask import Flask, request
import threading
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return "VoidPulse Bot is running perfectly!", 200

# Маршрут, куда твой майнкрафт-плагин будет отправлять сообщения из чата
@app.route('/mc-chat', methods=['POST'])
def mc_chat():
    try:
        data = request.json
        player = data.get('player', 'Игрок')
        message = data.get('message', '')
        
        # Сохраняем сообщение в очередь, чтобы бот мог его прочитать и отправить в Discord
        with open("mc_chat_queue.txt", "a", encoding="utf-8") as f:
            f.write(f"{player}:{message}\n")
            
        return {"status": "success"}, 200
    except Exception as e:
        return {"status": "error", "reason": str(e)}, 400

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
