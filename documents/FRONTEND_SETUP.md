# Finance Tools Frontend Setup Guide

This guide will help you set up and run the Finance Tools web application.

## Quick Start

### 1. Start the Backend API

```bash
# Terminal 1 - Start the backend (uses existing environment)
./start_backend.sh

# Or clean and recreate environment if needed
./start_backend.sh --clean

# Show help for more options
./start_backend.sh --help
```

The backend will start on http://localhost:8070

### 2. Start the Frontend

```bash
# Terminal 2 - Start the frontend
./start_frontend.sh
```

The frontend will start on http://localhost:3000

### 3. Access the Application

Open your browser and go to http://localhost:3000

## Prerequisites

### Backend Requirements
- Python 3.8+
- pip3
- SQLite database with TEFAS data

### Frontend Requirements
- Node.js 18+
- npm or yarn

## Detailed Setup

### Backend Setup

1. **Install Python Dependencies**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Finance Tools Package**
   ```bash
   cd ..
   pip install -e .
   ```

3. **Start the API Server**
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8070 --reload
   ```

### Frontend Setup

1. **Install Node.js Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the Development Server**
   ```bash
   npm start
   ```

## Features Overview

### Data Repository Tab
- **Database Statistics**: View total records, unique funds, last download date
- **Data Download**: Initiate TEFAS data downloads with progress tracking
- **Database Information**: Comprehensive overview of data source and status

### Data Explorer Tab
- **Data Table**: Paginated view of all records with sorting
- **Advanced Filtering**: Filter on any column with multiple operators
- **Search**: Global search across code and title fields
- **Data Visualization**: Interactive charts for numeric data
- **Export**: Download filtered data (coming soon)

## API Endpoints

The frontend communicates with these backend endpoints:

- `GET /api/database/stats` - Database statistics
- `POST /api/database/download` - Initiate data download
- `GET /api/database/download-progress` - Download progress
- `GET /api/data/records` - Paginated records with filtering
- `GET /api/data/columns` - Available column names
- `GET /api/data/plot` - Data for plotting

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8070
```

### Database Configuration

The backend uses the existing finance_tools configuration:
- Database type and connection details
- TEFAS data source settings
- Logging configuration

## Troubleshooting

### Common Issues

1. **Backend Won't Start**
   - Check if Python 3.8+ is installed
   - Verify all dependencies are installed
   - Check if port 8070 is available
   - Ensure database file exists
   - Try cleaning environment: `./start_backend.sh --clean`

2. **Frontend Won't Start**
   - Check if Node.js 18+ is installed
   - Verify npm dependencies are installed
   - Check if port 3000 is available
   - Clear npm cache: `npm cache clean --force`

3. **API Connection Errors**
   - Ensure backend is running on port 8070
   - Check CORS configuration
   - Verify API endpoints are accessible
   - Check browser console for errors

4. **Database Errors**
   - Ensure TEFAS database exists
   - Check database permissions
   - Verify data integrity
   - Check backend logs for errors

### Debug Mode

**Backend Debug:**
```bash
export DATABASE_ECHO=true
uvicorn main:app --reload --log-level debug
```

**Frontend Debug:**
```bash
export REACT_APP_DEBUG=true
npm start
```

### Logs and Monitoring

- **Backend Logs**: Check terminal output for API errors
- **Frontend Logs**: Check browser console for client errors
- **Database Logs**: Enable SQL echo for query debugging

## Development

### Code Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   ├── services/           # API service layer
│   ├── types/              # TypeScript definitions
│   └── App.tsx             # Main application
├── public/                 # Static assets
└── package.json           # Dependencies

backend/
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
└── README.md             # Backend documentation
```

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Create components in `src/components/`
3. **API Integration**: Update `src/services/api.ts`
4. **Types**: Add TypeScript definitions in `src/types/`

### Testing

**Backend Testing:**
```bash
cd backend
python -m pytest
```

**Frontend Testing:**
```bash
cd frontend
npm test
```

## Production Deployment

### Backend Deployment

1. **Environment Setup**
   ```bash
   export DATABASE_TYPE=postgresql
   export DATABASE_NAME=your_production_db
   ```

2. **Install Production Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Production Server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8070
   ```

### Frontend Deployment

1. **Build for Production**
   ```bash
   npm run build
   ```

2. **Serve Static Files**
   ```bash
   npx serve -s build
   ```

3. **Configure Environment**
   ```bash
   export REACT_APP_API_URL=https://your-api-domain.com
   ```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Verify all prerequisites are installed
4. Check the API documentation at http://localhost:8070/docs

## Next Steps

- Add user authentication and authorization
- Implement data export functionality
- Add more chart types and visualizations
- Implement real-time data updates
- Add mobile app support
