# Finance Tools Frontend

A modern React-based web interface for the Finance Tools ETF analysis system.

## Features

### Data Repository
- **Database Statistics**: View total records, unique funds, last download date, and data range
- **Data Download**: Initiate TEFAS data downloads with real-time progress tracking
- **Database Information**: Comprehensive overview of data source and status

### Data Explorer
- **Advanced Table View**: Paginated data table with sorting and filtering
- **Dynamic Filtering**: Filter on any column with multiple operators (equals, contains, greater than, less than, between)
- **Search Functionality**: Global search across code and title fields
- **Data Visualization**: Interactive plotting of numeric data with multiple chart types
- **Responsive Design**: Mobile-friendly interface with Material-UI components

## Technology Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for UI components
- **Recharts** for data visualization
- **React Query** for data fetching and caching
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8070

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open http://localhost:3000 in your browser

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8070
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `GET /api/database/stats` - Get database statistics
- `POST /api/database/download` - Initiate data download
- `GET /api/database/download-progress` - Get download progress
- `GET /api/data/records` - Get paginated records with filtering
- `GET /api/data/columns` - Get available column names
- `GET /api/data/plot` - Get data for plotting

## Component Structure

```
src/
├── components/
│   ├── DataRepository.tsx    # Database stats and download
│   ├── DataExplorer.tsx      # Main data exploration interface
│   ├── FilterDialog.tsx      # Advanced filtering dialog
│   └── PlotViewer.tsx        # Data visualization component
├── services/
│   └── api.ts                # API service layer
├── types/
│   └── index.ts              # TypeScript type definitions
├── App.tsx                   # Main application component
└── index.tsx                 # Application entry point
```

## Features in Detail

### Data Repository
- Real-time database statistics with auto-refresh
- Progress tracking for data downloads
- Comprehensive database information display
- Error handling and user feedback

### Data Explorer
- **Pagination**: Configurable page sizes (25, 50, 100, 200 records)
- **Sorting**: Click column headers to sort ascending/descending
- **Filtering**: 
  - Multiple filter types: equals, contains, greater than, less than, between
  - Dynamic filter application with visual indicators
  - Filter combination and removal
- **Search**: Global search across code and title fields
- **Visualization**: 
  - Interactive charts (line, scatter, bar)
  - Automatic chart type selection based on data
  - Configurable X and Y axes
  - Tooltip information and formatting

### Responsive Design
- Mobile-first approach
- Adaptive layouts for different screen sizes
- Touch-friendly interface elements
- Optimized for both desktop and mobile usage

## Development

### Code Structure
- Modular component architecture
- TypeScript for type safety
- Material-UI for consistent design
- React Query for efficient data management
- Centralized API service layer

### State Management
- React Query for server state
- Local state for UI interactions
- Optimistic updates and caching
- Error boundary handling

### Performance
- Lazy loading of components
- Efficient data pagination
- Chart data optimization
- Memoized calculations

## Deployment

### Production Build
```bash
npm run build
```

### Environment Configuration
- Development: `http://localhost:8000`
- Production: Configure `REACT_APP_API_URL` environment variable

## Contributing

1. Follow the existing code structure and patterns
2. Use TypeScript for all new components
3. Follow Material-UI design guidelines
4. Add proper error handling and loading states
5. Write tests for new functionality

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Ensure backend is running on port 8000
2. **CORS Issues**: Backend should have CORS configured for localhost:3000
3. **Build Errors**: Check Node.js version compatibility
4. **Chart Rendering**: Ensure data is properly formatted for Recharts

### Debug Mode
Enable debug logging by setting `REACT_APP_DEBUG=true` in your environment.
