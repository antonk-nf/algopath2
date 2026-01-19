import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')

  // Use base path for GitHub Pages deployment only
  // Set VITE_DEPLOY=github to enable the base path
  const isGitHubDeploy = env.VITE_DEPLOY === 'github' || process.env.GITHUB_ACTIONS === 'true';
  const base = isGitHubDeploy ? '/algopath2/' : '/';

  return {
    plugins: [react()],

    // Base path for deployment (GitHub Pages uses repo name as subdirectory)
    base,

    // Define global constants
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },
    
    server: {
      port: parseInt(env.VITE_PORT) || 5173,
      host: env.VITE_HOST || 'localhost',
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          timeout: 60000, // 60 second timeout for slow API responses
        },
      },
    },
    
    build: {
      outDir: 'dist',
      sourcemap: mode === 'development',
      minify: mode === 'production',
      
      // Optimize bundle splitting
      rollupOptions: {
        output: {
          manualChunks: {
            // Vendor chunks
            vendor: ['react', 'react-dom'],
            ui: ['@mui/material', '@mui/icons-material', '@mui/x-date-pickers'],
            charts: ['recharts'],
            utils: ['date-fns'],
          },
        },
      },
      
      // Build performance optimizations
      chunkSizeWarningLimit: 1000,
      
      // Asset optimization
      assetsInlineLimit: 4096, // 4kb
    },
    
    // Optimize dependencies
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        '@mui/material',
        '@mui/icons-material',
        'recharts',
        'date-fns'
      ],
    },
    
    // Preview server configuration (for production builds)
    preview: {
      port: parseInt(env.VITE_PREVIEW_PORT) || 4173,
      host: env.VITE_PREVIEW_HOST || 'localhost',
    },
    
    // Environment variables prefix
    envPrefix: 'VITE_',
  }
})
