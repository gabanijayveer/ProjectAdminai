"""
Configuration file for SQL Procedure Manager Frontend
Customize database and application settings here.
"""

import os

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'custom',
    'port': 3312,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

# FastAPI Application Configuration
FASTAPI_CONFIG = {
    'SECRET_KEY': 'your-secret-key-here-change-in-production',
    'DEBUG': True,  # Enable for development
    'HOST': '0.0.0.0',  # Allow network access
    'PORT': 8000,
    'RELOAD': True,  # Enable auto-reload for development
    'WORKERS': 1
}

# Frontend Configuration
FRONTEND_CONFIG = {
    'APP_NAME': 'AI Data Chat',
    'APP_VERSION': '1.0.0',
    'MAX_HISTORY_ITEMS': 1000,
    'DEFAULT_HISTORY_LIMIT': 50,
    'STATUS_CHECK_INTERVAL': 2000,  # milliseconds
    'AUTO_OPEN_BROWSER': True
}

# Query Execution Configuration
EXECUTION_CONFIG = {
    'MAX_EXECUTION_TIME': 300,  # seconds
    'BACKGROUND_EXECUTION': True,
    'CAPTURE_OUTPUT': True,
    'DEFAULT_QUALITY_THRESHOLD': 60
}

# Security Configuration
SECURITY_CONFIG = {
    'ENABLE_CORS': True,
    'ALLOWED_ORIGINS': [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://192.168.1.8:3000',  # Your network IP
        'http://localhost:8000',
        'http://192.168.1.8:8000',
        'http://localhost:5000',
        'http://192.168.1.8:5000'
    ],
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
    'SESSION_TIMEOUT': 3600  # seconds
}

# Logging Configuration
LOGGING_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'FILE': 'app.log',
    'MAX_BYTES': 10 * 1024 * 1024,  # 10MB
    'BACKUP_COUNT': 5
}

# Environment-specific overrides
if os.getenv('FASTAPI_ENV') == 'development':
    FASTAPI_CONFIG['DEBUG'] = True
    FASTAPI_CONFIG['RELOAD'] = True
    LOGGING_CONFIG['LEVEL'] = 'DEBUG'

if os.getenv('FASTAPI_ENV') == 'production':
    FASTAPI_CONFIG['DEBUG'] = False
    FASTAPI_CONFIG['RELOAD'] = False
    FASTAPI_CONFIG['SECRET_KEY'] = os.getenv('SECRET_KEY', FASTAPI_CONFIG['SECRET_KEY'])
    
    # Production database settings
    DB_CONFIG.update({
        'host': os.getenv('DB_HOST', DB_CONFIG['host']),
        'user': os.getenv('DB_USER', DB_CONFIG['user']),
        'password': os.getenv('DB_PASSWORD', DB_CONFIG['password']),
        'database': os.getenv('DB_NAME', DB_CONFIG['database']),
        'port': int(os.getenv('DB_PORT', DB_CONFIG['port']))
    })

# Validation functions
def validate_db_config():
    """Validate database configuration."""
    required_keys = ['host', 'user', 'password', 'database', 'port']
    for key in required_keys:
        if not DB_CONFIG.get(key):
            raise ValueError(f"Database configuration missing required key: {key}")
    
    if not isinstance(DB_CONFIG['port'], int):
        raise ValueError("Database port must be an integer")
    
    return True

def get_db_connection_string():
    """Get database connection string for logging (without password)."""
    return f"mysql://{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Export configurations
__all__ = [
    'DB_CONFIG',
    'FASTAPI_CONFIG',
    'FRONTEND_CONFIG',
    'EXECUTION_CONFIG',
    'SECURITY_CONFIG',
    'LOGGING_CONFIG',
    'validate_db_config',
    'get_db_connection_string'
]
