import { useReducer } from 'react';
import type { ReactNode } from 'react';
import { AppContext } from './AppContextDefinition';
import type { AppState, AppAction } from './AppContextDefinition';

// Initial state
const initialState: AppState = {
  apiHealth: {
    status: 'healthy',
    lastCheck: new Date().toISOString(),
    endpointStatus: {},
  },
  loading: {},
  errors: {},
  selectedCompanies: [],
  currentView: 'overview',
};

// Reducer function
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_API_HEALTH':
      return {
        ...state,
        apiHealth: action.payload,
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        loading: {
          ...state.loading,
          [action.payload.key]: action.payload.loading,
        },
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        errors: {
          ...state.errors,
          [action.payload.key]: action.payload.error,
        },
      };
    
    case 'SET_SELECTED_COMPANIES':
      return {
        ...state,
        selectedCompanies: action.payload,
      };
    
    case 'SET_CURRENT_VIEW':
      return {
        ...state,
        currentView: action.payload,
      };
    
    case 'CLEAR_ERRORS':
      return {
        ...state,
        errors: {},
      };
    
    default:
      return state;
  }
}

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}



