from flask import Flask, render_template_string, request, redirect, url_for
import datetime

app = Flask(__name__)

tickets_list = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoidPulse 🌌 | Next-Gen Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(18, 24, 38, 0.75);
            --primary: #8b5cf6;
            --secondary: #ec4899;
            --accent: #38bdf8;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(139, 92, 246, 0.25);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body {
            background-color: var(--bg-color);
            color: var(--text);
            min-height: 100vh;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.12) 0%, transparent 40%);
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 40px; border-bottom: 1px solid var(--border); padding-bottom: 20px;
        }
        .logo { font-size: 28px; font-weight: 800; background: linear-gradient(135deg, var(--accent), var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 10px; }
        .status-badge { background: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3); padding: 6px 16px; border-radius: 50px; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 12px #22c55e; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.8; } 50% { transform: scale(1.3); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.8; } }
        
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        @media(max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .card:hover { border-color: rgba(139, 92, 246, 0.5); transform: translateY(-3px); }
        .card h2 { font-size: 20px; margin-bottom: 20px; color: var(--text); display: flex; align-items: center; gap: 10px; }
        
        .stat-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .stat-label { color: var(--text-muted); }
        .stat-value { font-weight: 600; color: var(--accent); }
        
        form { display: flex; flex-direction: column; gap: 15px; }
        input, textarea, select {
            background: rgba(11, 15, 25, 0.85);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 18px;
            color: var(--text);
            font-size: 15px;
            outline: none;
            transition: all 0.3s;
        }
        input:focus, textarea:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
        textarea { resize: vertical; min-height: 100px; }
        button {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; border: none; padding: 14px; border-radius: 12px;
            font-weight: 600; font-size: 16px; cursor: pointer;
            transition: opacity 0.3s, transform 0.2s;
            box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3);
        }
        button:hover { opacity: 0.95; transform: translateY(-2px); }
        
        .ticket-list { margin-top: 15px; max-height: 250px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 5px; }
        .ticket-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 14px 18px; border-radius: 12px; font-size: 14px; }
        .ticket-title { font-weight: 600; color: var(--accent); margin-bottom: 4px; display: flex; justify-content: space-between; }
        .ticket-desc { color: var(--text-muted); font-size: 13px; margin-top: 4px; }
        
        footer { text-align: center; margin-top: 50px; color: var(--text-muted); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🌌 VOIDPULSE <span style="font-size: 13px; font-weight: 300; color: var(--text-muted);">Secure Web Dashboard</span></div>
            <div class="status-badge"><div class="status-dot"></div> 24/7 Онлайн</div>
        </header>

        <div class="grid">
            <div class="card">
                <h2>📊 Статус Системы</h2>
                <div class="stat-item"><span class="stat-label">Бот</span><span class="stat-value">Активен (Discord Gateway)</span></div>
                <div class="stat-item"><span class="stat-label">Хостинг</span><span class="stat-value">Render Cloud</span></div>
                <div class="stat-item"><span class="stat-label">База Данных</span><span class="stat-value">Google Sheets Sync</span></div>
                <div class="stat-item"><span class="stat-label">Доступ</span><span class="stat-value">Защищен (Owner Only)</span></div>
                <div class="stat-item"><span class="stat-label">Время</span><span class="stat-value" id="time"></span></div>
            </div>

            <div class="card">
                <h2>🎫 Создать Тикет Поддержки</h2>
                <form action="/create_ticket" method="POST">
                    <input type="text" name="username" placeholder="Ваш Discord / Никнейм" required>
                    <select name="category">
                        <option value="⚙️ Технический вопрос">⚙️ Технический вопрос</option>
                        <option value="🛡️ Жалоба на персонал">🛡️ Жалоба на персонал</option>
                        <option value="💎 Покупка привилегии">💎 Покупка привилегии</option>
                    </select>
                    <textarea name="message" placeholder="Опишите суть вопроса..." required></textarea>
                    <button type="submit">Отправить тикет 🚀</button>
                </form>
            </div>
        </div>

        <div class="card" style="margin-top: 30px;">
            <h2>📂 Активные тикеты с веб-сайта</h2>
            <div class="ticket-list">
                {% if tickets %}
                    {% for t in tickets %}
                    <div class="ticket-card">
                        <div class="ticket-title"><span>{{ t.category }} • {{ t.username }}</span><span style="font-size: 11px; color: var(--text-muted);">{{ t.time }}</span></div>
                        <div class="ticket-desc">{{ t.message }}</div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: var(--text-muted); text-align: center; padding: 20px;">Пока нет ни одного тикета.</p>
                {% endif %}
            </div>
        </div>

        <footer>VoidPulse Security & Management System © 2026</footer>
    </div>
    <script>
        setInterval(() => {
            document.getElementById('time').innerText = new Date().toLocaleTimeString();
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, tickets=tickets_list)

@app.route('/create_ticket', methods=['POST'])
def create_ticket():
    username = request.form.get('username')
    category = request.form.get('category')
    message = request.form.get('message')
    time_str = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    
    if username and message:
        tickets_list.insert(0, {
            'username': username,
            'category': category,
            'message': message,
            'time': time_str
        })
    return redirect(url_for('home'))

def keep_alive():
    from threading import Thread
    def run():
        app.run(host='0.0.0.0', port=10000)
    t = Thread(target=run)
    t.start()
