# Finance Tools Backend API

FastAPI-based backend service for the Finance Tools ETF analysis system.

## Features

### Database Management
- **Statistics API**: Get database metrics, record counts, and date ranges
- **Data Download**: Asynchronous TEFAS data crawling and storage
- **Progress Tracking**: Real-time download progress monitoring

### Data Access
- **Paginated Records**: Efficient data retrieval with pagination
- **Advanced Filtering**: Multi-column filtering with various operators
- **Search Functionality**: Full-text search across relevant fields
- **Data Visualization**: Plot data preparation for frontend charts

### API Endpoints

#### Database Management
- `GET /api/database/stats` - Get database statistics
- `POST /api/database/download` - Initiate data download
- `GET /api/database/download-progress` - Get download progress

#### Data Access
- `GET /api/data/records` - Get paginated records with filtering
- `GET /api/data/columns` - Get available column names
- `GET /api/data/plot` - Get data for plotting

## Technology Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Pandas** - Data manipulation and analysis
- **Uvicorn** - ASGI server for production

## Getting Started

### Prerequisites

- Python 3.8+
- pip3
- SQLite database with TEFAS data

### Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install finance_tools package:
```bash
cd ..
pip install -e .
```

4. Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8070 --reload
```

### Using the Startup Script

```bash
# Start with existing environment (recommended)
./start_backend.sh

# Clean and recreate environment
./start_backend.sh --clean

# Show help
./start_backend.sh --help
```

The startup script is smart and will:
- Use existing virtual environment if available
- Only install dependencies if requirements.txt has changed
- Provide options for cleaning and recreating the environment

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8070/docs
- **ReDoc**: http://localhost:8070/redoc

## Database Integration

The API integrates with the existing TEFAS database through:

- **TefasRepository**: Extended with new methods for API functionality
- **DatabaseEngineProvider**: Centralized database configuration
- **TefasPersistenceService**: Data persistence operations

### New Repository Methods

- `get_total_records_count()` - Total record count
- `get_unique_funds_count()` - Unique fund count
- `get_date_range()` - Data date range
- `get_last_download_date()` - Most recent download
- `get_paginated_records()` - Paginated data with filtering
- `get_plot_data()` - Data for visualization

## API Usage Examples

### Get Database Statistics
```bash
curl http://localhost:8070/api/database/stats
```

### Get Paginated Records
```bash
curl "http://localhost:8070/api/data/records?page=1&pageSize=50&search=ETF"
```

### Filter Records
```bash
curl "http://localhost:8070/api/data/records?filters[0][column]=price&filters[0][operator]=greater_than&filters[0][value]=100"
```

### Get Plot Data
```bash
curl "http://localhost:8070/api/data/plot?xColumn=date&yColumn=price"
```

## Configuration

### Environment Variables

The API uses the centralized configuration from `finance_tools.config`:

- `DATABASE_TYPE` - Database type (sqlite, postgresql, etc.)
- `DATABASE_NAME` - Database name or file path
- `DATABASE_ECHO` - SQL query logging

### CORS Configuration

Configured for frontend development:
- Origins: `http://localhost:3000`, `http://127.0.0.1:3000`
- Methods: All HTTP methods
- Headers: All headers

## Error Handling

- **HTTP Exceptions**: Proper status codes and error messages
- **Database Errors**: Graceful handling of database issues
- **Validation**: Input validation and sanitization
- **Logging**: Comprehensive error logging

## Performance Considerations

- **Pagination**: Efficient data retrieval with LIMIT/OFFSET
- **Filtering**: Database-level filtering for performance
- **Caching**: Query result caching where appropriate
- **Async Operations**: Non-blocking download operations

## Security

- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **CORS**: Configured for specific origins
- **Error Sanitization**: Safe error message responses

## Development

### Code Structure
```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Adding New Endpoints

1. Define Pydantic models for request/response
2. Add endpoint function with proper typing
3. Implement repository methods if needed
4. Add error handling and validation
5. Update API documentation

### Database Operations

All database operations go through the `TefasRepository` class:
- Use dependency injection for session management
- Implement proper error handling
- Add logging for debugging
- Follow existing patterns

## Deployment

### Production Considerations

1. **Environment Variables**: Set production database configuration
2. **CORS**: Update allowed origins for production domains
3. **Logging**: Configure production logging levels
4. **Monitoring**: Add health checks and metrics
5. **Security**: Review and harden security settings

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8070"]
```

## Monitoring and Logging

- **Structured Logging**: JSON-formatted logs
- **Request Tracking**: Unique request IDs
- **Performance Metrics**: Response time tracking
- **Error Monitoring**: Comprehensive error logging

## Troubleshooting

### Common Issues

1. **Database Connection**: Check database configuration and connectivity
2. **Import Errors**: Ensure finance_tools package is installed
3. **CORS Issues**: Verify frontend URL in CORS configuration
4. **Port Conflicts**: Check if port 8070 is available

### Debug Mode

Enable debug logging:
```bash
export DATABASE_ECHO=true
uvicorn main:app --reload --log-level debug
```

### Health Check

```bash
curl http://localhost:8070/
```

## Contributing

1. Follow existing code patterns and structure
2. Add proper type hints and documentation
3. Implement comprehensive error handling
4. Add tests for new functionality
5. Update API documentation
