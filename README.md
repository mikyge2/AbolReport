# 🏭 Factory Portal - Production & Sales Management System

A comprehensive web-based factory management system for tracking production, sales, downtime, and analytics across multiple manufacturing facilities.

![Factory Portal](https://img.shields.io/badge/Factory-Portal-blue?style=for-the-badge&logo=factory&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 Core Functionality
- **Multi-Factory Support**: Manage multiple manufacturing facilities from a single dashboard
- **Role-Based Access Control**: Headquarters and factory-level user permissions
- **Real-Time Analytics**: Interactive charts and performance metrics
- **Production Tracking**: Monitor daily production across different product lines
- **Sales Management**: Track sales data with revenue calculations
- **Downtime Monitoring**: Multi-reason downtime tracking with detailed reporting

### 📊 Dashboard & Analytics
- **Interactive Charts**: Click on data points for detailed information
- **Factory Comparison**: Side-by-side performance analysis
- **Trend Analysis**: 30-day production and sales trends
- **Efficiency Metrics**: Real-time factory efficiency calculations
- **Export Capabilities**: Excel report generation with role-based filtering

### 👥 User Management
- **Authentication System**: Secure login with JWT tokens
- **User Roles**: Headquarters and factory-level access control
- **Profile Management**: User creation and management interface
- **Session Management**: Secure session handling

### 📈 Reporting Features
- **Daily Log Management**: Create, edit, and delete daily production logs
- **Excel Export**: Comprehensive data export with proper formatting
- **Advanced Filtering**: Filter by date range, factory, and user
- **Report ID System**: Sequential report numbering (RPT-XXXXX format)

## 🛠 Tech Stack

### Frontend
- **React 18** - Modern JavaScript library for building user interfaces
- **TailwindCSS** - Utility-first CSS framework for rapid UI development
- **Chart.js & React-Chartjs-2** - Beautiful, responsive charts and graphs
- **React Hot Toast** - Elegant toast notifications
- **Axios** - HTTP client for API communication

### Backend
- **FastAPI** - Modern, fast Python web framework
- **MongoDB** - NoSQL database for flexible data storage
- **PyMongo** - MongoDB driver for Python
- **Pydantic** - Data validation using Python type annotations
- **OpenPyXL** - Excel file generation and manipulation

### Infrastructure
- **Supervisor** - Process control system for managing services
- **Kubernetes** - Container orchestration (deployment ready)
- **Docker** - Containerization support

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB 4.4+
- Yarn package manager

### One-Command Setup
```bash
# Clone the repository
git clone <repository-url>
cd factory-portal

# Start all services
sudo supervisorctl restart all
```

## 📦 Installation

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB connection string
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
yarn install

# Set up environment variables
cp .env.example .env
# Edit .env with your backend URL
```

### 3. Database Setup
```bash
# Start MongoDB service
sudo systemctl start mongodb

# The application will automatically create required collections
```

### 4. Start Services
```bash
# Start backend (from backend directory)
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Start frontend (from frontend directory)
yarn start

# Or use supervisor to manage all services
sudo supervisorctl start all
```

## 🎯 Usage

### Default Login Credentials
```
Username: admin
Password: admin1234
Role: headquarters
```

### Factory Data Structure
The system supports multiple factories:
- **Wakene Food Complex** - Food manufacturing
- **Amen (Victory) Water** - Beverage production  
- **Mintu Plast** - Plastic manufacturing (Preforms & Caps)
- **Mintu Export** - Export operations

### Key Workflows

#### 1. Daily Logging
1. Navigate to **Daily Logging** tab
2. Select **Create New Log**
3. Fill in production, sales, downtime, and stock data
4. Support for multiple downtime reasons with hour allocation
5. Submit and track daily operations

#### 2. Dashboard Analytics
1. **Factory Comparison**: View today's performance across all factories
2. **All Factories Overview**: Interactive 30-day trend analysis
3. **Click on chart data points** for detailed daily information
4. Export comprehensive Excel reports

#### 3. User Management (Headquarters Only)
1. Navigate to **User Management** tab
2. Create new factory users with specific factory assignments
3. Manage user profiles and permissions
4. Role-based access control enforcement

## 📚 API Documentation

### Authentication
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin1234"
}
```

### Daily Logs
```http
# Get daily logs with filtering
GET /api/daily-logs?factory_id=wakene_food&start_date=2025-08-01&created_by_me=true

# Create new daily log
POST /api/daily-logs
Authorization: Bearer <token>

# Update existing log (only creator)
PUT /api/daily-logs/{log_id}
Authorization: Bearer <token>

# Delete log (only creator)
DELETE /api/daily-logs/{log_id}
Authorization: Bearer <token>
```

### Analytics
```http
# Get factory trends (30-day data)
GET /api/analytics/trends?days=30
Authorization: Bearer <token>

# Get factory comparison (today's data)
GET /api/analytics/factory-comparison
Authorization: Bearer <token>

# Get dashboard summary
GET /api/dashboard-summary
Authorization: Bearer <token>
```

### Excel Export
```http
# Export data to Excel
GET /api/export-excel?start_date=2025-08-01&end_date=2025-08-21&factory_id=wakene_food
Authorization: Bearer <token>
```

## 📁 Project Structure

```
factory-portal/
├── backend/
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Dashboard.js   # Main dashboard container
│   │   │   ├── DashboardTab.js # Analytics and charts
│   │   │   ├── LoggingTab.js  # Daily logging interface
│   │   │   ├── ReportsTab.js  # Reports and analytics
│   │   │   ├── UserManagementTab.js # User management
│   │   │   └── DataDetailModal.js # Popup details
│   │   ├── context/           # React context providers
│   │   │   └── AuthContext.js # Authentication context
│   │   ├── App.js             # Main React component
│   │   └── index.js           # Application entry point
│   ├── package.json           # Node.js dependencies
│   ├── tailwind.config.js     # TailwindCSS configuration
│   └── .env                   # Frontend environment variables
├── scripts/                   # Utility scripts
├── tests/                     # Test files
├── test_result.md            # Testing documentation
└── README.md                 # Project documentation
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017/factory_portal
JWT_SECRET_KEY=your_jwt_secret_key_here
```

#### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Supervisor Configuration
The project uses Supervisor to manage services:
- **Backend**: FastAPI server on port 8001
- **Frontend**: React development server on port 3000  
- **MongoDB**: Database service
- **Code Server**: Development environment

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Run Frontend Tests
```bash
cd frontend
yarn test
```

### Manual Testing
1. Login with admin credentials
2. Test dashboard functionality
3. Verify chart interactions
4. Test Excel export
5. Validate user management (HQ users only)

## 🚀 Deployment

### Production Deployment
1. **Database**: Set up MongoDB cluster
2. **Backend**: Deploy FastAPI with Gunicorn/Uvicorn
3. **Frontend**: Build and serve static files
4. **Environment**: Configure production environment variables
5. **SSL**: Set up HTTPS certificates
6. **Monitoring**: Configure logging and monitoring

### Docker Deployment
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add some amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow Python PEP 8 style guide for backend
- Use ESLint and Prettier for frontend code formatting
- Write unit tests for new features
- Update documentation for API changes
- Test across different user roles

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- 📧 **Email**: support@abolconsortium.com
- 📖 **Documentation**: Check the `/docs` directory
- 🐛 **Issues**: Create an issue in the repository
- 💬 **Discussions**: Use GitHub Discussions for questions

## 🏆 Acknowledgments

- **Chart.js** for beautiful data visualization
- **TailwindCSS** for rapid UI development
- **FastAPI** for modern Python web framework
- **React** for powerful frontend development
- **MongoDB** for flexible data storage

---

**Built with ❤️ for efficient factory management**

*Last updated: August 2025*
