# Interview Prep Dashboard - Frontend

A comprehensive React TypeScript frontend for the LeetCode Analytics & Company Research Platform.

## Features

- **React 18** with TypeScript for type safety
- **Material-UI (MUI)** for consistent, professional UI components
- **Vite** for fast development and optimized builds
- **Context API** for simple state management
- **Custom API Client** with retry logic and 45-second timeouts
- **Health Monitoring** for API status tracking
- **Error Handling** with graceful degradation

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── HealthStatus.tsx # API health monitoring component
├── context/            # React Context for state management
│   └── AppContext.tsx  # Main application state
├── hooks/              # Custom React hooks
│   └── useApi.ts       # API integration hooks
├── services/           # External service integrations
│   └── apiClient.ts    # HTTP client with retry logic
├── theme/              # Material-UI theme configuration
│   └── theme.ts        # Custom theme setup
└── App.tsx             # Main application component
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development

The development server runs on http://localhost:5173 with:
- Hot Module Replacement (HMR)
- API proxy to backend (http://localhost:8000)
- TypeScript type checking
- ESLint code quality checks

### API Integration

The frontend is designed to work with the LeetCode Analytics API:

- **Working Endpoints**: `/api/v1/health/*` (fully functional)
- **Failing Endpoints**: `/api/v1/companies/*` (500 errors - see backend verification)
- **Timeout Handling**: 45-second timeouts with exponential backoff retry
- **Error Handling**: Graceful degradation with fallback UI states

### State Management

Uses React Context API for simple state management:

```typescript
// Access global state
const { state, dispatch } = useAppContext();

// Use specific state slices
const apiHealth = useApiHealth();
const loading = useLoading('companies');
const error = useError('companies');
```

### API Usage

```typescript
// Use the health check hook
const { data, loading, error, refetch } = useHealthCheck();

// Use generic API hook
const { data, loading, error } = useApi<CompanyData[]>('/api/v1/companies/stats');
```

## Architecture Decisions

### Why Context API over Redux?
- Simpler setup and maintenance
- Sufficient for current complexity
- Easy to migrate to Redux Toolkit later if needed

### Why 45-second timeouts?
- Backend has 30+ second cold starts (verified)
- Provides buffer for slow responses
- Better user experience than premature timeouts

### Why Material-UI?
- Comprehensive component library
- Built-in accessibility features
- Professional design system
- Excellent TypeScript support

## Error Handling Strategy

The frontend is designed with "error-first" architecture:

1. **Assume endpoints may fail** (75% failure rate currently)
2. **Provide fallback UI states** for all data-dependent components
3. **Cache successful responses** aggressively
4. **Show meaningful error messages** to users
5. **Graceful degradation** when features are unavailable

## Performance Optimizations

- **Code splitting** with dynamic imports (planned)
- **Memoization** of expensive computations
- **Virtual scrolling** for large datasets (planned)
- **Aggressive caching** of API responses
- **Optimized bundle** with Vite's tree shaking

## Testing

```bash
# Run tests (when implemented)
npm run test

# Run linting
npm run lint
```

## Deployment

```bash
# Build for production
npm run build

# The dist/ folder contains the built application
# Serve with any static file server
```

## Environment Variables

Create a `.env` file for configuration:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCK_DATA=false
VITE_CACHE_DURATION=3600000
```

## Contributing

1. Follow TypeScript strict mode
2. Use Material-UI components consistently
3. Add error handling for all API calls
4. Test with both working and failing endpoints
5. Maintain responsive design principles

## Known Issues

- Company endpoints return 500 errors (backend issue)
- Some features require mock data for development
- Error handling system needs comprehensive testing

See `PHASE1_VERIFICATION_SUMMARY.md` for detailed backend status.