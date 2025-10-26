import { createContext } from 'react';

// Types for our application state
export interface ApiHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  lastCheck: string;
  endpointStatus: Record<string, 'working' | 'slow' | 'error'>;
}

export interface AppState {
  // API Status
  apiHealth: ApiHealth;
  
  // UI State
  loading: Record<string, boolean>;
  errors: Record<string, string | null>;
  
  // User Preferences
  selectedCompanies: string[];
  currentView: 'overview' | 'company' | 'topics' | 'study' | 'analytics' | 'discovery' | 'bookmarks';
}

// Action types
export type AppAction =
  | { type: 'SET_API_HEALTH'; payload: ApiHealth }
  | { type: 'SET_LOADING'; payload: { key: string; loading: boolean } }
  | { type: 'SET_ERROR'; payload: { key: string; error: string | null } }
  | { type: 'SET_SELECTED_COMPANIES'; payload: string[] }
  | { type: 'SET_CURRENT_VIEW'; payload: AppState['currentView'] }
  | { type: 'CLEAR_ERRORS' };

// Context
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);