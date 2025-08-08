from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import os
import json
import mysql.connector
from datetime import datetime, timedelta
import uuid
import threading
import io
import sys
import hashlib
import jwt
from contextlib import redirect_stdout, redirect_stderr
from config import DB_CONFIG, FASTAPI_CONFIG, validate_db_config
from Proceduremanager import run_sql_procedure_agent, MATH_FORMULAS

# Initialize FastAPI app
app = FastAPI(
    title="AI Data Chat API",
    description="AI-powered data analysis and SQL query API backend",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.8:3000",  # Network access
        "file://",  # For local HTML files
        "*"  # Allow all origins during development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate database configuration on startup
validate_db_config()

# JWT Configuration
JWT_SECRET_KEY = FASTAPI_CONFIG.get('SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# Default session configuration for chat history management (for backward compatibility)
DEFAULT_SESSION_ID = "114"
DEFAULT_TOKEN = "123456"
current_session = {
    'session_id': DEFAULT_SESSION_ID,
    'token': DEFAULT_TOKEN,
    'chat_history': []
}

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = DEFAULT_SESSION_ID
    token: Optional[str] = DEFAULT_TOKEN

class QueryAnalysisRequest(BaseModel):
    query: str

class SessionRequest(BaseModel):
    session_id: str
    token: str

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    message: str

class QueryResult(BaseModel):
    success: bool
    results: List[str]
    summary: str
    quality_score: int
    raw_output: Optional[str] = None

# Authentication Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class SessionInfo(BaseModel):
    session_id: str
    user_id: int
    email: str
    expires_at: datetime

# AI Chat processor using your Proceduremanager.py
def is_greeting_or_simple_query(query: str) -> bool:
    """Check if query is a greeting or simple conversation that doesn't need SQL processing."""
    greeting_patterns = [
        'hi', 'hello', 'hey', 'hy', 'hii', 'helo',
        'how are you', 'how r u', 'whats up', 'what\'s up',
        'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'bye', 'goodbye', 'see you',
        'ok', 'okay', 'yes', 'no', 'sure', 'fine'
    ]

    query_lower = query.lower().strip()

    # Check for exact matches or simple greetings
    if query_lower in greeting_patterns:
        return True

    # Check for greeting-like patterns (short queries with greeting words)
    if len(query_lower) <= 20:  # Short queries
        for pattern in greeting_patterns:
            if pattern in query_lower:
                return True

    return False

def needs_context(query: str) -> bool:
    """Determine if query needs previous conversation context."""
    context_keywords = [
        'previous', 'before', 'earlier', 'last time', 'again',
        'same', 'similar', 'like before', 'as we discussed',
        'continue', 'more', 'also', 'additionally', 'further',
        'update', 'modify', 'change', 'compare', 'difference'
    ]

    query_lower = query.lower()

    # Check if query explicitly references previous conversation
    for keyword in context_keywords:
        if keyword in query_lower:
            return True

    # If it's a greeting or simple query, no context needed
    if is_greeting_or_simple_query(query):
        return False

    # For complex data queries, use minimal context only if recent history exists
    return False  # Default to no context unless explicitly needed

def handle_greeting(query: str) -> str:
    """Handle greeting messages without running SQL procedures."""
    greeting_responses = {
        'hi': "Hello! I'm your AI data assistant. I can help you analyze your data, run SQL queries, and provide insights. What would you like to explore today?",
        'hello': "Hi there! I'm ready to help you with data analysis and SQL queries. What can I assist you with?",
        'hey': "Hey! I'm your data assistant. Ask me anything about your database or data analysis needs.",
        'hy': "Hi! I'm here to help with your data queries and analysis. What would you like to know?",
        'how are you': "I'm doing great and ready to help with your data analysis! What database queries or insights do you need today?",
        'thanks': "You're welcome! Feel free to ask me anything about your data or if you need help with SQL queries.",
        'thank you': "You're very welcome! I'm here whenever you need data analysis or database assistance.",
        'good morning': "Good morning! Ready to dive into some data analysis today? What can I help you with?",
        'good afternoon': "Good afternoon! I'm here to assist with your data queries and analysis needs.",
        'good evening': "Good evening! How can I help you with your data today?"
    }

    query_lower = query.lower().strip()

    # Try exact match first
    if query_lower in greeting_responses:
        return greeting_responses[query_lower]

    # Try partial matches for variations
    for greeting, response in greeting_responses.items():
        if greeting in query_lower:
            return response

    # Default friendly response
    return "Hello! I'm your AI data assistant. I can help you analyze data, run SQL queries, and provide insights. What would you like to explore?"

# Database setup for history
def get_db_connection():
    """Get MySQL database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Initialize MySQL database for storing query history and user authentication."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if ai_user table exists (your existing table)
        cursor.execute("SHOW TABLES LIKE 'ai_user'")
        ai_user_exists = cursor.fetchone() is not None

        if ai_user_exists:
            print("✅ Found existing ai_user table")
            # Add missing columns to ai_user table if needed
            try:
                cursor.execute("DESCRIBE ai_user")
                columns = [row[0] for row in cursor.fetchall()]

                # Add id column if it doesn't exist
                if 'id' not in columns:
                    cursor.execute("ALTER TABLE ai_user ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST")
                    print("✅ Added id column to ai_user table")

                # Add full_name column if it doesn't exist
                if 'full_name' not in columns:
                    cursor.execute("ALTER TABLE ai_user ADD COLUMN full_name VARCHAR(255) DEFAULT NULL")
                    print("✅ Added full_name column to ai_user table")

                # Add is_active column if it doesn't exist
                if 'is_active' not in columns:
                    cursor.execute("ALTER TABLE ai_user ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                    print("✅ Added is_active column to ai_user table")

                # Add created_at column if it doesn't exist
                if 'created_at' not in columns:
                    cursor.execute("ALTER TABLE ai_user ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                    print("✅ Added created_at column to ai_user table")

                # Add last_login column if it doesn't exist
                if 'last_login' not in columns:
                    cursor.execute("ALTER TABLE ai_user ADD COLUMN last_login DATETIME DEFAULT NULL")
                    print("✅ Added last_login column to ai_user table")

            except mysql.connector.Error as e:
                print(f"⚠️ Note: {e}")
        else:
            # Create users table for authentication (fallback)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    INDEX idx_email (email),
                    INDEX idx_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            print("✅ Created users table")

        # Create user_sessions table for session management
        table_name = 'ai_user' if ai_user_exists else 'users'
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(500) NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_user_id (user_id),
                INDEX idx_token (token),
                INDEX idx_expires (expires_at),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        print("✅ Created user_sessions table")

        # Update query_history table to link with users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id VARCHAR(255) PRIMARY KEY,
                timestamp DATETIME,
                user_query TEXT,
                query_type VARCHAR(100),
                suggested_formulas JSON,
                procedure_code LONGTEXT,
                execution_results JSON,
                quality_score INTEGER,
                status VARCHAR(50),
                session_id VARCHAR(50),
                user_id INT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_status (status),
                INDEX idx_query_type (query_type),
                INDEX idx_session_id (session_id),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # Add user_id column to existing query_history table if it doesn't exist
        try:
            cursor.execute('''
                ALTER TABLE query_history
                ADD COLUMN user_id INT,
                ADD INDEX idx_user_id (user_id),
                ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ''')
            print("✅ Added user_id column to existing query_history table")
        except mysql.connector.Error as alter_error:
            if "Duplicate column name" in str(alter_error) or "Duplicate key name" in str(alter_error):
                print("✅ user_id column and indexes already exist")
            else:
                print(f"⚠️ Note: {alter_error}")

        # Create default admin user if no users exist
        table_name = 'ai_user' if ai_user_exists else 'users'
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            # Create default admin user
            import hashlib
            default_password = "admin123"
            password_hash = hashlib.sha256(default_password.encode()).hexdigest()

            if ai_user_exists:
                import random
                import string
                session_id = ''.join(random.choices(string.digits, k=8))
                cursor.execute('''
                    INSERT INTO ai_user (email, password, session_id, full_name, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                ''', ("admin@example.com", password_hash, session_id, "Administrator", True))
            else:
                cursor.execute('''
                    INSERT INTO users (email, password_hash, full_name, is_active)
                    VALUES (%s, %s, %s, %s)
                ''', ("admin@example.com", password_hash, "Administrator", True))

            print("✅ Created default admin user (admin@example.com / admin123)")

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ MySQL database initialized successfully")
    except mysql.connector.Error as e:
        print(f"❌ Database initialization error: {e}")
        # Try to create database if it doesn't exist
        try:
            temp_config = DB_CONFIG.copy()
            temp_config.pop('database')
            temp_conn = mysql.connector.connect(**temp_config)
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            temp_conn.commit()
            temp_cursor.close()
            temp_conn.close()
            print(f"✅ Database '{DB_CONFIG['database']}' created")
            # Retry initialization
            init_db()
        except mysql.connector.Error as create_error:
            print(f"❌ Failed to create database: {create_error}")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Authentication utility functions
def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed_password

def create_access_token(user_id: int, email: str) -> str:
    """Create a JWT access token."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)

    # Verify user exists and is active
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if ai_user table exists
        cursor.execute("SHOW TABLES LIKE 'ai_user'")
        ai_user_exists = cursor.fetchone() is not None

        if ai_user_exists:
            cursor.execute("""
                SELECT id, email, full_name, is_active, created_at, last_login
                FROM ai_user WHERE id = %s AND (is_active IS NULL OR is_active = TRUE)
            """, (payload["user_id"],))
        else:
            cursor.execute("""
                SELECT id, email, full_name, is_active, created_at, last_login
                FROM users WHERE id = %s AND is_active = TRUE
            """, (payload["user_id"],))

        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return {
            "id": user_data[0],
            "email": user_data[1],
            "full_name": user_data[2] if len(user_data) > 2 else None,
            "is_active": user_data[3] if len(user_data) > 3 else True,
            "created_at": user_data[4] if len(user_data) > 4 else None,
            "last_login": user_data[5] if len(user_data) > 5 else None
        }

    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

def create_user_session(user_id: int, token: str) -> str:
    """Create a new user session."""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Deactivate old sessions for this user
        cursor.execute("""
            UPDATE user_sessions SET is_active = FALSE
            WHERE user_id = %s AND is_active = TRUE
        """, (user_id,))

        # Create new session
        cursor.execute("""
            INSERT INTO user_sessions (session_id, user_id, token, expires_at, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, user_id, token, expires_at, True))

        conn.commit()
        cursor.close()
        conn.close()

        return session_id

    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

# Template helper functions
def get_category_icon(category: str) -> str:
    """Get Font Awesome icon for formula category."""
    icons = {
        'statistical': 'chart-bar',
        'aggregation': 'calculator',
        'business': 'briefcase',
        'performance_ranking': 'trophy',
        'interview_ranking': 'users',
        'hiring_metrics': 'user-tie',
        'financial': 'dollar-sign',
        'time_series': 'clock',
        'data_quality': 'check-circle'
    }
    return icons.get(category, 'cog')

# Utility function for category icons (now used by frontend)
def get_category_icon(category: str) -> str:
    """Get Font Awesome icon for formula category."""
    icons = {
        'statistical': 'chart-bar',
        'aggregation': 'calculator',
        'business': 'briefcase',
        'performance_ranking': 'trophy',
        'interview_ranking': 'users',
        'hiring_metrics': 'user-tie',
        'financial': 'dollar-sign',
        'time_series': 'clock',
        'data_quality': 'check-circle'
    }
    return icons.get(category, 'cog')

def validate_session(session_id: str, token: str) -> bool:
    """Validate session ID and token."""
    return session_id == DEFAULT_SESSION_ID and token == DEFAULT_TOKEN

def save_query_history(query_data: Dict[str, Any]):
    """Save query execution to history database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Convert timestamp to MySQL datetime format
        timestamp = datetime.fromisoformat(query_data['timestamp'].replace('Z', '+00:00'))

        cursor.execute('''
            INSERT INTO query_history
            (id, timestamp, user_query, query_type, suggested_formulas,
             procedure_code, execution_results, quality_score, status, session_id, user_id, user_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new_values
            ON DUPLICATE KEY UPDATE
            timestamp = new_values.timestamp,
            user_query = new_values.user_query,
            query_type = new_values.query_type,
            suggested_formulas = new_values.suggested_formulas,
            procedure_code = new_values.procedure_code,
            execution_results = new_values.execution_results,
            quality_score = new_values.quality_score,
            status = new_values.status,
            session_id = new_values.session_id,
            user_id = new_values.user_id,
            user_email = new_values.user_email
        ''', (
            query_data['id'],
            timestamp,
            query_data['user_query'],
            query_data['query_type'],
            json.dumps(query_data['suggested_formulas']),
            query_data['procedure_code'],
            json.dumps(query_data['execution_results']),
            query_data['quality_score'],
            query_data['status'],
            query_data.get('session_id', None),
            query_data.get('user_id', None),
            query_data.get('user_email', None)
        ))

        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"❌ Error saving query history: {e}")

def get_session_history(session_id: str, token: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get chat history for a valid session from database."""
    if not validate_session(session_id, token):
        return []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query for session-specific chat history
        cursor.execute('''
            SELECT id, timestamp, user_query, execution_results, quality_score, status
            FROM query_history
            WHERE session_id = %s AND query_type = 'session_chat'
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (session_id, limit))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        history = []
        for row in rows:
            try:
                # Parse execution results (AI response)
                ai_response = json.loads(row[3]) if row[3] else []

                history.append({
                    'id': row[0],
                    'timestamp': row[1].isoformat() if row[1] else '',
                    'user_query': row[2],
                    'ai_response': ai_response,
                    'quality_score': row[4] or 0,
                    'status': row[5],
                    'session_id': session_id
                })
            except (json.JSONDecodeError, IndexError) as e:
                print(f"Error parsing history entry: {e}")
                continue

        # Reverse to show oldest first (chronological order)
        return list(reversed(history))

    except Exception as e:
        print(f"Error retrieving session history: {e}")
        return current_session['chat_history']  # Fallback to memory

def add_to_session_history(session_id: str, token: str, user_query: str, ai_response: List[str], quality_score: Optional[int] = None) -> bool:
    """Add a chat interaction to session history in database."""
    if not validate_session(session_id, token):
        return False

    try:
        # Generate unique ID for this chat entry
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Prepare data for database storage
        query_data = {
            'id': chat_id,
            'timestamp': timestamp.isoformat(),
            'user_query': user_query,
            'query_type': 'session_chat',
            'suggested_formulas': [],
            'procedure_code': f'Session chat - Token: {token}',
            'execution_results': ai_response if isinstance(ai_response, list) else [str(ai_response)],
            'quality_score': quality_score or 0,
            'status': 'completed',
            'session_id': session_id
        }

        # Save to database
        save_query_history(query_data)

        # Also keep in memory for quick access
        chat_entry = {
            'id': chat_id,
            'timestamp': timestamp.isoformat(),
            'user_query': user_query,
            'ai_response': ai_response,
            'quality_score': quality_score or 0,
            'session_id': session_id
        }

        current_session['chat_history'].append(chat_entry)

        # Keep only last 20 entries in memory
        if len(current_session['chat_history']) > 20:
            current_session['chat_history'] = current_session['chat_history'][-20:]

        return True

    except Exception as e:
        print(f"Error saving session history: {e}")
        return False

def get_context_from_history(session_id: str, token: str, limit: int = 2) -> str:
    """Get selective chat context for better AI responses - only when needed."""
    if not validate_session(session_id, token):
        return ""

    # Get recent history from database (reduced limit for efficiency)
    recent_history = get_session_history(session_id, token, limit)

    if not recent_history:
        return ""

    context_parts = []

    # Only include non-greeting conversations in context
    for entry in recent_history[-limit:]:
        user_query = entry['user_query']

        # Skip greetings and simple responses from context
        if not is_greeting_or_simple_query(user_query):
            context_parts.append(f"Previous Query: {user_query}")

            # Include only relevant parts of response
            if isinstance(entry['ai_response'], list):
                # For list responses, take first meaningful line
                meaningful_response = ""
                for line in entry['ai_response']:
                    if line and not line.startswith("Hello") and not line.startswith("Hi"):
                        meaningful_response = line[:150]
                        break
                if meaningful_response:
                    context_parts.append(f"Previous Response: {meaningful_response}...")
            else:
                response_str = str(entry['ai_response'])
                if not response_str.startswith(("Hello", "Hi", "Hey")):
                    context_parts.append(f"Previous Response: {response_str[:150]}...")

    return "\n".join(context_parts) if context_parts else ""

def extract_execution_results(raw_output: str) -> List[str]:
    """Extract from Description or DATA TABLES to the end - no SQL content."""
    lines = raw_output.split('\n')

    execution_results = []
    found_start = False

    # Look for "Description" or "DATA TABLES" sections
    for line in lines:
        line_stripped = line.strip()

        # Check if we found the start of meaningful content
        if (line_stripped.startswith('Description:') or
            line_stripped == 'DATA TABLES' or
            line_stripped.startswith('• • Key Metrics:') or
            (line_stripped.startswith('###') and not any(sql_word in line_stripped.upper() for sql_word in ['CREATE', 'SELECT', 'PROCEDURE']))):
            found_start = True
            execution_results.append(line_stripped)
            continue

        # If we found the start, capture everything after it (excluding SQL)
        if found_start:
            # Skip empty lines and separator lines
            if not line_stripped or line_stripped.startswith('=') or line_stripped.startswith('-'):
                continue

            # Skip all SQL-related content
            if any(sql_word in line_stripped.upper() for sql_word in [
                'CREATE PROCEDURE', 'DECLARE', 'BEGIN', 'END;', 'SELECT', 'FROM', 'WHERE',
                'GROUP BY', 'ORDER BY', 'LIMIT', 'INSERT', 'UPDATE', 'DELETE', 'ALTER TABLE',
                'DROP', 'CALL', 'SET @', 'IF', 'ELSE', 'WHILE', 'LOOP', 'CURSOR', 'DELIMITER',
                'COMMIT', 'ROLLBACK', 'TRANSACTION', 'INDEX', 'PRIMARY KEY', 'FOREIGN KEY'
            ]):
                continue

            # Skip technical/debug lines
            if any(skip_word in line_stripped for skip_word in [
                'Generated Procedure:', 'Connected to MySQL', 'Dataset Analysis:',
                'Using standard processing', 'All required tables found',
                'Dropped existing procedure', 'Extracted procedure code:',
                'Successfully created procedure', 'Procedure verified', 'Procedure executed',
                'Report Generated at:', 'Cleaned up', 'Database connection closed',
                'STEP', 'PROCEDURE EXPLANATION', 'Generated SQL Procedure:',
                'EXECUTION RESULTS', 'EXECUTION COMPLETED'
            ]):
                continue

            # Add the line to results
            execution_results.append(line_stripped)

    # If no Description or DATA TABLES found, look for table data directly
    if not execution_results:
        for line in lines:
            line_stripped = line.strip()

            # Look for table headers or meaningful data
            if (' | ' in line_stripped and
                any(header_word in line_stripped for header_word in ['ID', 'Name', 'Email', 'Date', 'Amount', 'Status'])):
                found_start = True
                execution_results.append(line_stripped)
                continue

            # If we found table data, continue capturing
            if found_start:
                if not line_stripped or line_stripped.startswith('=') or line_stripped.startswith('-'):
                    continue

                # Skip SQL content
                if any(sql_word in line_stripped.upper() for sql_word in [
                    'CREATE', 'SELECT', 'FROM', 'WHERE', 'DECLARE', 'BEGIN', 'END;'
                ]):
                    continue

                execution_results.append(line_stripped)

    return execution_results if execution_results else ["No execution results found in the output."]

def process_user_query(user_query: str, session_id: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """Process user query using the actual Proceduremanager.py backend with smart context usage."""
    try:
        # Use default session if not provided
        if not session_id:
            session_id = DEFAULT_SESSION_ID
        if not token:
            token = DEFAULT_TOKEN

        # Handle greetings without running procedures
        if is_greeting_or_simple_query(user_query):
            greeting_response = handle_greeting(user_query)

            # Add to session history with high quality score
            add_to_session_history(session_id, token, user_query, [greeting_response], 95)

            return {
                'success': True,
                'results': [greeting_response],
                'summary': "Greeting handled successfully",
                'quality_score': 95,
                'raw_output': greeting_response
            }

        # Smart context usage - only get context if needed
        enhanced_query = user_query
        if needs_context(user_query):
            context = get_context_from_history(session_id, token, limit=2)
            if context:
                enhanced_query = f"Context from previous conversation:\n{context}\n\nCurrent Query: {user_query}"

        # Capture raw output from your Proceduremanager
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Run your actual Proceduremanager function with enhanced query
            run_sql_procedure_agent(enhanced_query)

        # Get the raw output
        raw_output = stdout_capture.getvalue()
        error_output = stderr_capture.getvalue()

        if raw_output:
            # Filter output to start from "**Description:**" line
            lines = raw_output.strip().split('\n')
            filtered_lines = []
            start_capturing = False

            for line in lines:
                if '**Description:**' in line:
                    start_capturing = True

                if start_capturing:
                    filtered_lines.append(line)

            # If we found the description, use filtered content, otherwise use all
            if filtered_lines:
                execution_results = ['\n'.join(filtered_lines)]
            else:
                execution_results = [raw_output.strip()]

            # Debug: Let's see what we extracted
            print(f"DEBUG: Extracted {len(execution_results)} result lines:")
            for i, result in enumerate(execution_results[:5]):  # Show first 5 lines
                print(f"  {i+1}: {result}")

            if execution_results and len(execution_results) > 0:
                # Filter out the "No execution results found" message if we have real data
                if execution_results[0] != "No execution results found in the output. The query may have completed without returning data.":
                    result = {
                        'success': True,
                        'results': execution_results,
                        'summary': f"Query executed successfully - {len(execution_results)} result lines",
                        'quality_score': 90,
                        'raw_output': raw_output
                    }

                    # Add to session history
                    add_to_session_history(session_id, token, user_query, execution_results, 90)

                    return result

            # If no meaningful results found, show a simple message
            return {
                'success': True,
                'results': ["The query executed successfully but no data results were returned to display."],
                'summary': "Query completed - no display data available",
                'quality_score': 75,
                'raw_output': raw_output
            }
        else:
            return {
                'success': False,
                'results': [f"No output captured from Proceduremanager.py"],
                'summary': "No output received",
                'quality_score': 0,
                'error': error_output if error_output else 'No output or error captured'
            }

    except Exception as e:
        return {
            'success': False,
            'results': [f"make proper query"],
            'summary': "System error occurred",
            'quality_score': 0,
            'error': str(e)
        }

def get_query_type_from_text(user_query: str) -> str:
    """Determine query type from user input."""
    query_lower = user_query.lower()

    if any(word in query_lower for word in ['hire', 'hiring', 'candidate', 'recruit']):
        return 'HIRING'
    elif any(word in query_lower for word in ['sales', 'revenue', 'profit', 'customer']):
        return 'SALES'
    elif any(word in query_lower for word in ['analysis', 'statistical', 'trend', 'pattern']):
        return 'STATISTICAL'
    elif any(word in query_lower for word in ['performance', 'rank', 'top', 'best']):
        return 'PERFORMANCE'
    else:
        return 'GENERAL'

def suggest_optimal_formulas_for_query(query_type: str) -> List[str]:
    """Suggest optimal formulas based on query type."""
    suggestions = []

    if query_type == 'HIRING':
        suggestions.extend([
            "Performance ranking analysis",
            "Employee scoring system",
            "Candidate comparison metrics"
        ])
    elif query_type == 'SALES':
        suggestions.extend([
            "Revenue trend analysis",
            "Sales performance metrics",
            "Customer value ranking"
        ])
    elif query_type == 'STATISTICAL':
        suggestions.extend([
            "Statistical analysis",
            "Data distribution metrics",
            "Trend identification"
        ])
    elif query_type == 'PERFORMANCE':
        suggestions.extend([
            "Performance ranking",
            "Comparative analysis",
            "Top performer identification"
        ])

    return suggestions

def suggest_performance_formulas(user_query: Optional[str] = None) -> List[str]:
    """Simple performance suggestions."""
    return [
        "Data analysis completed",
        "Performance metrics calculated",
        "Results optimized for your query"
    ]

def get_query_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve query history from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, timestamp, user_query, query_type, suggested_formulas,
                   procedure_code, execution_results, quality_score, status, session_id
            FROM query_history
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (limit,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'timestamp': row[1].isoformat() if row[1] else '',
                'user_query': row[2],
                'query_type': row[3],
                'suggested_formulas': json.loads(row[4]) if row[4] else [],
                'procedure_code': row[5],
                'execution_results': json.loads(row[6]) if row[6] else [],
                'quality_score': row[7],
                'status': row[8],
                'session_id': row[9] if len(row) > 9 else None
            })

        return history
    except mysql.connector.Error as e:
        print(f"❌ Error retrieving query history: {e}")
        return []

def clear_session_history(session_id: str, token: str) -> bool:
    """Clear chat history for a session from database."""
    if not validate_session(session_id, token):
        return False

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete session-specific chat history
        cursor.execute('''
            DELETE FROM query_history
            WHERE session_id = %s AND query_type = 'session_chat'
        ''', (session_id,))

        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        # Also clear memory
        current_session['chat_history'] = []

        print(f"Cleared {deleted_count} chat entries for session {session_id}")
        return True

    except Exception as e:
        print(f"Error clearing session history: {e}")
        return False

# FastAPI API Routes

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "AI Data Chat API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": {
                "register": "/auth/register",
                "login": "/auth/login",
                "logout": "/auth/logout",
                "me": "/auth/me"
            },
            "chat": "/api/execute_query",
            "analysis": "/api/analyze_query",
            "history": "/api/history",
            "docs": "/docs"
        }
    }

# Authentication Routes
@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if ai_user table exists
        cursor.execute("SHOW TABLES LIKE 'ai_user'")
        ai_user_exists = cursor.fetchone() is not None

        if ai_user_exists:
            # Check if user already exists in ai_user table
            cursor.execute("SELECT id FROM ai_user WHERE email = %s", (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Hash password and create user in ai_user table
            password_hash = hash_password(user_data.password)
            import random
            import string
            session_id = ''.join(random.choices(string.digits, k=8))
            cursor.execute("""
                INSERT INTO ai_user (email, password, session_id, full_name, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_data.email, password_hash, session_id, user_data.full_name, True))

            user_id = cursor.lastrowid

            # Update last login
            cursor.execute("""
                UPDATE ai_user SET last_login = %s WHERE id = %s
            """, (datetime.utcnow(), user_id))

            conn.commit()

            # Get user data for response
            cursor.execute("""
                SELECT id, email, full_name, is_active, created_at, last_login
                FROM ai_user WHERE id = %s
            """, (user_id,))

        else:
            # Check if user already exists in users table
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Hash password and create user in users table
            password_hash = hash_password(user_data.password)
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, is_active)
                VALUES (%s, %s, %s, %s)
            """, (user_data.email, password_hash, user_data.full_name, True))

            user_id = cursor.lastrowid

            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = %s WHERE id = %s
            """, (datetime.utcnow(), user_id))

            conn.commit()

            # Get user data for response
            cursor.execute("""
                SELECT id, email, full_name, is_active, created_at, last_login
                FROM users WHERE id = %s
            """, (user_id,))

        user_data_result = cursor.fetchone()
        cursor.close()
        conn.close()

        # Create JWT token
        access_token = create_access_token(user_id, user_data.email)

        # Create session
        session_id = create_user_session(user_id, access_token)

        user_response = UserResponse(
            id=user_data_result[0],
            email=user_data_result[1],
            full_name=user_data_result[2] if len(user_data_result) > 2 else None,
            is_active=user_data_result[3] if len(user_data_result) > 3 else True,
            created_at=user_data_result[4] if len(user_data_result) > 4 else datetime.utcnow(),
            last_login=user_data_result[5] if len(user_data_result) > 5 else datetime.utcnow()
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=user_response
        )

    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user and return JWT token."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if ai_user table exists
        cursor.execute("SHOW TABLES LIKE 'ai_user'")
        ai_user_exists = cursor.fetchone() is not None

        if ai_user_exists:
            # Get user by email from ai_user table
            cursor.execute("""
                SELECT id, email, password, full_name, is_active, created_at, last_login
                FROM ai_user WHERE email = %s
            """, (login_data.email,))
        else:
            # Get user by email from users table
            cursor.execute("""
                SELECT id, email, password_hash, full_name, is_active, created_at, last_login
                FROM users WHERE email = %s
            """, (login_data.email,))

        user_data = cursor.fetchone()

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password (column index 2 for both tables)
        if not verify_password(login_data.password, user_data[2]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if account is active (if column exists)
        if len(user_data) > 4 and user_data[4] is not None and not user_data[4]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )

        user_id = user_data[0]
        user_email = user_data[1]

        # Update last login
        if ai_user_exists:
            cursor.execute("""
                UPDATE ai_user SET last_login = %s WHERE id = %s
            """, (datetime.utcnow(), user_id))
        else:
            cursor.execute("""
                UPDATE users SET last_login = %s WHERE id = %s
            """, (datetime.utcnow(), user_id))

        conn.commit()
        cursor.close()
        conn.close()

        # Create JWT token
        access_token = create_access_token(user_id, user_email)

        # Create session
        session_id = create_user_session(user_id, access_token)

        user_response = UserResponse(
            id=user_data[0],
            email=user_data[1],
            full_name=user_data[3] if len(user_data) > 3 else None,
            is_active=user_data[4] if len(user_data) > 4 else True,
            created_at=user_data[5] if len(user_data) > 5 else datetime.utcnow(),
            last_login=datetime.utcnow()
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=user_response
        )

    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        last_login=current_user["last_login"]
    )

@app.post("/auth/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout user and deactivate session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Deactivate all sessions for this user
        cursor.execute("""
            UPDATE user_sessions SET is_active = FALSE
            WHERE user_id = %s AND is_active = TRUE
        """, (current_user["id"],))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Successfully logged out"}

    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.get("/auth/session")
async def get_session_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current session information."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get active session for user
        cursor.execute("""
            SELECT session_id, expires_at FROM user_sessions
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC LIMIT 1
        """, (current_user["id"],))

        session_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found"
            )

        return SessionInfo(
            session_id=session_data[0],
            user_id=current_user["id"],
            email=current_user["email"],
            expires_at=session_data[1]
        )

    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

@app.get("/history/recent")
async def recent_chats(session_id: Optional[str] = None, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get recent chat history for authenticated user, optionally filtered by session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if session_id:
            # Get recent chats for specific session
            cursor.execute("""
                SELECT user_query, timestamp, session_id, quality_score, id
                FROM query_history
                WHERE user_id = %s AND session_id = %s AND user_query IS NOT NULL AND user_query != ''
                ORDER BY timestamp DESC
                LIMIT 20
            """, (current_user["id"], session_id))
        else:
            # Get recent chats across all sessions for sidebar
            cursor.execute("""
                SELECT user_query, timestamp, session_id, quality_score, id
                FROM query_history
                WHERE user_id = %s AND user_query IS NOT NULL AND user_query != ''
                ORDER BY timestamp DESC
                LIMIT 5
            """, (current_user["id"],))

        results = cursor.fetchall()
        recent_chats = []

        for row in results:
            recent_chats.append({
                'id': row[4] if len(row) > 4 else '',
                'query': row[0],
                'timestamp': row[1].isoformat() if row[1] else '',
                'session_id': row[2] if row[2] else '',
                'quality_score': row[3] if row[3] else None
            })

        cursor.close()
        conn.close()

        print(f"Found {len(recent_chats)} recent chats for user {current_user['id']}" +
              (f" in session {session_id}" if session_id else ""))
        return recent_chats
    except Exception as e:
        print(f"Error fetching recent chats: {e}")
        # Return empty array on error
        return []

@app.get("/history/session/{session_id}")
async def get_session_history(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get complete chat history for a specific session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all chats for the specific session
        cursor.execute("""
            SELECT id, user_query, timestamp, execution_results, quality_score, status, procedure_code
            FROM query_history
            WHERE user_id = %s AND session_id = %s AND user_query IS NOT NULL AND user_query != ''
            ORDER BY timestamp ASC
        """, (current_user["id"], session_id))

        results = cursor.fetchall()
        session_history = []

        for row in results:
            # Parse execution results
            execution_results = []
            if row[3]:  # execution_results
                try:
                    execution_results = json.loads(row[3]) if isinstance(row[3], str) else row[3]
                except:
                    execution_results = [str(row[3])]

            session_history.append({
                'id': row[0],
                'query': row[1],
                'timestamp': row[2].isoformat() if row[2] else '',
                'response': execution_results,
                'quality_score': row[4] if row[4] else None,
                'status': row[5] if row[5] else 'completed',
                'procedure_code': row[6] if row[6] else ''
            })

        cursor.close()
        conn.close()

        print(f"Found {len(session_history)} messages in session {session_id}")
        return session_history
    except Exception as e:
        print(f"Error fetching session history: {e}")
        return []

@app.get("/debug/check_database")
async def check_database():
    """Check what's in the query_history table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check table structure
        cursor.execute("DESCRIBE query_history")
        columns = cursor.fetchall()

        # Check recent data with user_query
        cursor.execute("""
            SELECT user_query, timestamp, session_id, quality_score, status
            FROM query_history
            WHERE user_query IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent_data = cursor.fetchall()

        # Count total rows
        cursor.execute("SELECT COUNT(*) FROM query_history WHERE user_query IS NOT NULL")
        total_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "columns": [{"Field": col[0], "Type": col[1]} for col in columns],
            "recent_data": [list(row) for row in recent_data],
            "total_rows": total_count,
            "sample_queries": [row[0] for row in recent_data if row[0]]
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/analyze_query")
async def analyze_query(request: QueryAnalysisRequest):
    """Analyze user query and provide suggestions."""
    try:
        user_query = request.query.strip()

        if not user_query:
            raise HTTPException(status_code=400, detail='Query cannot be empty')

        # Analyze query
        query_type = get_query_type_from_text(user_query)
        optimal_formulas = suggest_optimal_formulas_for_query(query_type)
        performance_suggestions = suggest_performance_formulas(user_query)

        return {
            'query_type': query_type,
            'optimal_formulas': optimal_formulas[:10],  # Limit to top 10
            'performance_suggestions': performance_suggestions[:5],  # Limit to top 5
            'available_formulas': MATH_FORMULAS
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute_query", response_model=ExecutionResponse)
async def execute_query(request: QueryRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Execute the SQL procedure generation and execution with authenticated user session."""
    try:
        user_query = request.query.strip()
        user_id = current_user["id"]

        # Get user's active session
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id FROM user_sessions
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))

        session_data = cursor.fetchone()
        session_id = session_data[0] if session_data else str(uuid.uuid4())
        cursor.close()
        conn.close()

        if not user_query:
            raise HTTPException(status_code=400, detail='Query cannot be empty')

        # Generate unique ID for this execution
        execution_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Store initial data
        query_data = {
            'id': execution_id,
            'timestamp': timestamp,
            'user_query': user_query,
            'query_type': get_query_type_from_text(user_query),
            'suggested_formulas': suggest_optimal_formulas_for_query(get_query_type_from_text(user_query)),
            'procedure_code': '',
            'execution_results': [],
            'quality_score': 0,
            'status': 'processing',
            'session_id': session_id,
            'user_id': user_id,
            'user_email': current_user['email']
        }

        # Save initial state
        save_query_history(query_data)

        # Execute in background thread to avoid timeout
        def execute_in_background():
            try:
                # Process the query using our simple backend with user context
                result = process_user_query(user_query, session_id, str(user_id))

                if result['success']:
                    query_data['status'] = 'completed'
                    query_data['quality_score'] = result['quality_score']
                    query_data['procedure_code'] = 'Query processed successfully'
                    query_data['execution_results'] = result['results']
                else:
                    query_data['status'] = 'error'
                    query_data['quality_score'] = 0
                    query_data['procedure_code'] = 'Query processing failed'
                    query_data['execution_results'] = result['results']

                save_query_history(query_data)

            except Exception as e:
                query_data['status'] = 'error'
                query_data['execution_results'] = [f'System error: {str(e)}']
                save_query_history(query_data)

        # Start background execution
        thread = threading.Thread(target=execute_in_background)
        thread.start()

        return ExecutionResponse(
            execution_id=execution_id,
            status='processing',
            message='Query execution started. Check status for updates.'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/execution_status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get the status of a query execution."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, timestamp, user_query, query_type, suggested_formulas,
                   procedure_code, execution_results, quality_score, status, session_id
            FROM query_history WHERE id = %s
        ''', (execution_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail='Execution not found')

        return {
            'id': row[0],
            'timestamp': row[1].isoformat() if row[1] else '',
            'user_query': row[2],
            'query_type': row[3],
            'suggested_formulas': json.loads(row[4]) if row[4] else [],
            'procedure_code': row[5],
            'execution_results': json.loads(row[6]) if row[6] else [],
            'quality_score': row[7],
            'status': row[8],
            'session_id': row[9] if len(row) > 9 else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history_endpoint(limit: int = 50, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get query execution history for authenticated user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, timestamp, user_query, query_type, suggested_formulas,
                   procedure_code, execution_results, quality_score, status, session_id, user_id
            FROM query_history
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (current_user["id"], limit))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'timestamp': row[1].isoformat() if row[1] else '',
                'user_query': row[2],
                'query_type': row[3],
                'suggested_formulas': json.loads(row[4]) if row[4] else [],
                'procedure_code': row[5],
                'execution_results': json.loads(row[6]) if row[6] else [],
                'quality_score': row[7],
                'status': row[8],
                'session_id': row[9],
                'user_id': row[10]
            })

        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete_history/{history_id}")
async def delete_history_item(history_id: str):
    """Delete a specific history item."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM query_history WHERE id = %s', (history_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {'message': 'History item deleted successfully'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clear_history")
async def clear_all_history():
    """Clear all query history."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM query_history')
        conn.commit()
        cursor.close()
        conn.close()

        return {'message': 'All history cleared successfully'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
