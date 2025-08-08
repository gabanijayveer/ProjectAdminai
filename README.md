# AI Data Chat

An intelligent AI-powered data analysis and SQL query system that automatically generates and executes SQL procedures based on natural language queries. The system combines a FastAPI backend with a React frontend to provide an intuitive interface for database analysis and insights.

## 🚀 Features

### Core Functionality
- **Natural Language to SQL**: Convert plain English queries into optimized SQL procedures
- **AI-Powered Analysis**: Uses Google Gemini AI for intelligent query interpretation
- **Real-time Chat Interface**: Interactive chat-based data exploration
- **Automated Procedure Generation**: Creates and executes MySQL stored procedures dynamically
- **Smart Context Awareness**: Maintains conversation context for follow-up queries

### Advanced Analytics
- **Mathematical Formulas**: Built-in statistical, aggregation, and business formulas
- **Performance Ranking**: Employee performance analysis and ranking systems
- **Interview Analytics**: Candidate evaluation and hiring metrics
- **Financial Calculations**: ROI, profit margins, and growth rate analysis
- **Data Quality Metrics**: Comprehensive data validation and quality scoring

### User Experience
- **Modern React Frontend**: Responsive TypeScript-based UI with authentication
- **Dual Interface Support**: Both Flask (legacy) and FastAPI (modern) backends
- **Session Management**: Secure user sessions with JWT authentication
- **Query History**: Persistent storage and retrieval of analysis history
- **Real-time Updates**: Live status updates during query execution

## 🏗️ Architecture

### Backend Components
- **FastAPI Application** (`fastapi_app.py`): Modern async API with authentication
- **Flask Application** (`app.py`): Legacy web interface (backward compatibility)
- **Procedure Manager** (`Proceduremanager.py`): Core AI-powered SQL generation engine
- **Configuration** (`config.py`): Centralized settings management

### Frontend Components
- **React Application** (`frontend/`): Modern TypeScript-based SPA
- **Authentication System**: JWT-based user management
- **Chat Interface**: Real-time conversation with AI
- **History Management**: Query tracking and retrieval
- **Formula Reference**: Built-in mathematical formula library

### Database Schema
- **MySQL Database**: Stores user data, query history, and session information
- **Dynamic Tables**: Supports orders, products, users, employees, and custom schemas
- **Query History**: Tracks all interactions with quality scoring
- **User Management**: Secure authentication and session handling

## 📋 Prerequisites

### System Requirements
- **Python 3.8+**
- **Node.js 16+** and npm
- **MySQL 5.7+** or **MariaDB 10.3+**
- **Google API Key** for Gemini AI

### Database Setup
1. Install MySQL/MariaDB
2. Create a database (default: `custom`)
3. Update database credentials in `config.py`

## 🛠️ Installation

### Quick Start (Development)
```bash
# Clone the repository
git clone <repository-url>
cd AIDataChat

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Configure database settings
# Edit config.py with your database credentials

# Run setup script
python setup.py

# Start development environment (both backend and frontend)
python start_dev.py
```

### Manual Setup

#### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure database (edit config.py)
# Set your MySQL credentials and Google API key

# Initialize database
python setup.py

# Start FastAPI server
python run_fastapi.py
# OR start Flask server
python app.py
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## 🔧 Configuration

### Database Configuration (`config.py`)
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'custom',
    'port': 3306,
    'charset': 'utf8mb4'
}
```

### API Configuration
```python
FASTAPI_CONFIG = {
    'SECRET_KEY': 'your-secret-key-here',
    'HOST': '0.0.0.0',
    'PORT': 8000,
    'DEBUG': False
}
```

### Google AI Setup
Set your Google API key in `Proceduremanager.py`:
```python
os.environ["GOOGLE_API_KEY"] = "your_google_api_key_here"
```

## 🚀 Usage

### Starting the Application

#### Development Mode
```bash
# Start both backend and frontend
python start_dev.py

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

#### Production Mode
```bash
# Build frontend
cd frontend && npm run build && cd ..

# Start FastAPI server
python run_fastapi.py

# Or use production server
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
uvicorn fastapi_app:app --port 8000
```

### Authentication
- **Default Admin Account**: `admin@example.com` / `admin123`
- **Registration**: Create new accounts via `/auth/register`
- **JWT Tokens**: Secure session management

### Example Queries

#### Basic Data Analysis
```
"Show me the top 5 customers by total orders"
"What are the sales trends for the last quarter?"
"Find employees with performance rating above 4.0"
```

#### Advanced Analytics
```
"Rank employees by performance with statistical analysis"
"Calculate ROI for each product category"
"Show hiring success rate by department"
"Generate performance percentiles for all staff"
```

#### Business Intelligence
```
"Compare revenue growth year over year"
"Identify top performing sales representatives"
"Analyze customer retention rates"
"Calculate average order value by region"
```

## 📊 Built-in Formulas

### Statistical Analysis
- Mean, Median, Mode calculations
- Standard deviation and variance
- Percentile analysis (25th, 75th)
- Coefficient of variation

### Business Metrics
- Growth rate calculations
- Moving averages
- Cumulative sums
- ROI and profit margins

### Performance Ranking
- Employee performance scoring
- Department-wise rankings
- Percentile rankings
- Top performer identification

### Interview Analytics
- Technical skill assessment
- Communication scoring
- Overall candidate ranking
- Hire recommendation system

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Current user info
- `POST /auth/logout` - User logout

### Chat & Analysis
- `POST /api/execute_query` - Execute natural language query
- `POST /api/analyze_query` - Analyze query type and suggestions
- `GET /api/execution_status/{id}` - Check query execution status

### History Management
- `GET /api/history` - Get query history
- `GET /history/recent` - Get recent chat history
- `DELETE /api/clear_history` - Clear all history

### Formulas & Reference
- `GET /formulas` - Mathematical formulas reference
- `GET /api/formulas` - Available formula categories

## 🗂️ Project Structure

```
AIDataChat/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.py                # Configuration settings
├── setup.py                 # Setup and installation script
├── start_dev.py             # Development startup script
│
├── Backend/
│   ├── app.py               # Flask application (legacy)
│   ├── fastapi_app.py       # FastAPI application (modern)
│   ├── Proceduremanager.py  # AI-powered SQL generation engine
│   ├── run_fastapi.py       # FastAPI server runner
│   └── run_frontend.py      # Flask server runner
│
├── frontend/                # React TypeScript application
│   ├── package.json         # Node.js dependencies
│   ├── tsconfig.json        # TypeScript configuration
│   ├── public/              # Static assets
│   └── src/                 # React source code
│       ├── components/      # Reusable UI components
│       ├── pages/           # Application pages
│       ├── contexts/        # React contexts (Auth, etc.)
│       ├── services/        # API service layer
│       └── styles/          # CSS styling
│
├── templates/               # Flask HTML templates (legacy)
│   ├── base.html
│   ├── chat.html
│   ├── history.html
│   └── formulas.html
│
└── static/                  # Static assets for Flask
    ├── css/
    ├── js/
    └── images/
```

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Secure password hashing (SHA256)
- Session management with expiration
- Protected API endpoints

### Data Security
- SQL injection prevention
- Input validation and sanitization
- CORS configuration for cross-origin requests
- Secure database connections

### Session Management
- Automatic session expiration
- Token-based authentication
- User activity tracking
- Secure logout functionality

## 🧪 Testing

### Backend Testing
```bash
# Test database connection
python test_network_access.py

# Test authentication flow
python test_auth_flow.py

# Test complete system
python test_complete_auth_flow.py
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Deployment
1. **Environment Setup**:
   ```bash
   export FASTAPI_ENV=production
   export SECRET_KEY=your-production-secret-key
   export DB_HOST=your-production-db-host
   ```

2. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

3. **Start Production Server**:
   ```bash
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Deployment (Optional)
```dockerfile
# Example Dockerfile structure
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **TypeScript**: Use ESLint configuration
- **Documentation**: Update README for new features
- **Testing**: Add tests for new functionality

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support & Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check MySQL service
sudo systemctl status mysql

# Verify credentials in config.py
# Ensure database exists and user has permissions
```

#### Frontend Build Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### API Key Issues
- Verify Google API key is valid
- Check API quotas and billing
- Ensure Gemini AI API is enabled

### Getting Help
- Check the `/docs` endpoint for API documentation
- Review query history for debugging
- Enable debug mode in configuration
- Check application logs for detailed error messages

## 🔄 Version History

- **v1.0.0**: Initial release with FastAPI backend and React frontend
- **v0.9.0**: Flask-based prototype with basic functionality
- **v0.8.0**: Core AI engine and procedure generation

## 🎯 Roadmap

### Upcoming Features
- [ ] Advanced visualization dashboards
- [ ] Export functionality (PDF, Excel)
- [ ] Multi-database support (PostgreSQL, SQLite)
- [ ] Custom formula builder
- [ ] Real-time collaboration features
- [ ] Advanced caching mechanisms
- [ ] Mobile application support

---

**Built with ❤️ using FastAPI, React, and Google Gemini AI**
