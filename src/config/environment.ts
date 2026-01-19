// Environment configuration management
export interface EnvironmentConfig {
  // Application
  appEnv: 'development' | 'staging' | 'production';
  
  // API Configuration
  apiUrl: string;
  apiTimeout: number;
  
  // Feature Flags
  enableAnalytics: boolean;
  enableOnboarding: boolean;
  enableErrorReporting: boolean;
  
  // Cache Configuration
  cacheDuration: number;
  maxCacheSize: number;
  
  // Performance Configuration
  enableServiceWorker: boolean;
  enableOfflineMode: boolean;
  
  // Debug Configuration
  debugMode: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  
  // Build Information
  version: string;
  buildTime: string;
}

// Default configuration
const defaultConfig: EnvironmentConfig = {
  appEnv: 'development',
  apiUrl: 'http://localhost:8000',
  apiTimeout: 60000,
  enableAnalytics: true,
  enableOnboarding: true,
  enableErrorReporting: false,
  cacheDuration: 3600000, // 1 hour
  maxCacheSize: 104857600, // 100MB
  enableServiceWorker: false,
  enableOfflineMode: false,
  debugMode: false,
  logLevel: 'info',
  version: '1.0.0',
  buildTime: new Date().toISOString()
};

// Load configuration from environment variables
function loadEnvironmentConfig(): EnvironmentConfig {
  return {
    appEnv: (import.meta.env.VITE_APP_ENV as EnvironmentConfig['appEnv']) || defaultConfig.appEnv,
    
    apiUrl: import.meta.env.VITE_API_URL || defaultConfig.apiUrl,
    apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || defaultConfig.apiTimeout,
    
    enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    enableOnboarding: import.meta.env.VITE_ENABLE_ONBOARDING !== 'false', // Default true
    enableErrorReporting: import.meta.env.VITE_ENABLE_ERROR_REPORTING === 'true',
    
    cacheDuration: parseInt(import.meta.env.VITE_CACHE_DURATION) || defaultConfig.cacheDuration,
    maxCacheSize: parseInt(import.meta.env.VITE_MAX_CACHE_SIZE) || defaultConfig.maxCacheSize,
    
    enableServiceWorker: import.meta.env.VITE_ENABLE_SERVICE_WORKER === 'true',
    enableOfflineMode: import.meta.env.VITE_ENABLE_OFFLINE_MODE === 'true',
    
    debugMode: import.meta.env.VITE_DEBUG_MODE === 'true' || import.meta.env.DEV,
    logLevel: (import.meta.env.VITE_LOG_LEVEL as EnvironmentConfig['logLevel']) || 
              (import.meta.env.DEV ? 'debug' : 'info'),
    
    version: (globalThis as any).__APP_VERSION__ || defaultConfig.version,
    buildTime: (globalThis as any).__BUILD_TIME__ || defaultConfig.buildTime
  };
}

// Export the configuration
export const config = loadEnvironmentConfig();

// Validation function
export function validateConfig(config: EnvironmentConfig): string[] {
  const errors: string[] = [];
  
  if (!config.apiUrl) {
    errors.push('API URL is required');
  }
  
  if (config.apiTimeout < 1000) {
    errors.push('API timeout must be at least 1000ms');
  }
  
  if (config.cacheDuration < 0) {
    errors.push('Cache duration must be non-negative');
  }
  
  if (config.maxCacheSize < 1024 * 1024) {
    errors.push('Max cache size must be at least 1MB');
  }
  
  return errors;
}

// Environment-specific utilities
export const isDevelopment = config.appEnv === 'development';
export const isProduction = config.appEnv === 'production';
export const isStaging = config.appEnv === 'staging';

// API endpoint builder
export function buildApiUrl(path: string): string {
  const baseUrl = config.apiUrl.replace(/\/$/, ''); // Remove trailing slash
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
}

// Feature flag checker
export function isFeatureEnabled(feature: keyof Pick<EnvironmentConfig, 
  'enableAnalytics' | 'enableOnboarding' | 'enableErrorReporting' | 
  'enableServiceWorker' | 'enableOfflineMode'>): boolean {
  return config[feature];
}

// Logger utility
export const logger = {
  debug: (...args: any[]) => {
    if (config.logLevel === 'debug' || config.debugMode) {
      console.debug('[DEBUG]', ...args);
    }
  },
  info: (...args: any[]) => {
    if (['debug', 'info'].includes(config.logLevel)) {
      console.info('[INFO]', ...args);
    }
  },
  warn: (...args: any[]) => {
    if (['debug', 'info', 'warn'].includes(config.logLevel)) {
      console.warn('[WARN]', ...args);
    }
  },
  error: (...args: any[]) => {
    console.error('[ERROR]', ...args);
  }
};

// Configuration summary for debugging
export function getConfigSummary(): Record<string, any> {
  return {
    environment: config.appEnv,
    apiUrl: config.apiUrl,
    version: config.version,
    buildTime: config.buildTime,
    features: {
      analytics: config.enableAnalytics,
      onboarding: config.enableOnboarding,
      errorReporting: config.enableErrorReporting,
      serviceWorker: config.enableServiceWorker,
      offlineMode: config.enableOfflineMode
    },
    debug: {
      debugMode: config.debugMode,
      logLevel: config.logLevel
    }
  };
}

// Validate configuration on load
const configErrors = validateConfig(config);
if (configErrors.length > 0) {
  console.error('Configuration validation errors:', configErrors);
  if (isProduction) {
    throw new Error(`Invalid configuration: ${configErrors.join(', ')}`);
  }
}

// Log configuration in development
if (isDevelopment) {
  logger.debug('Application configuration:', getConfigSummary());
}