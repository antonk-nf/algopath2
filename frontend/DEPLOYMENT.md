# Deployment Guide

This guide covers deploying the Interview Prep Dashboard frontend application.

## Prerequisites

- Node.js 18+ and npm
- Docker (optional, for containerized deployment)
- Web server (nginx, Apache, or similar)

## Environment Configuration

### 1. Environment Files

Copy the appropriate environment file for your deployment:

```bash
# For development
cp .env.development .env.local

# For staging
cp .env.example .env.staging
# Edit .env.staging with your staging configuration

# For production
cp .env.example .env.production
# Edit .env.production with your production configuration
```

### 2. Required Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_APP_ENV` | Application environment | `development` | Yes |
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `60000` | No |
| `VITE_ENABLE_ANALYTICS` | Enable analytics features | `true` | No |
| `VITE_ENABLE_ONBOARDING` | Enable user onboarding | `true` | No |
| `VITE_ENABLE_ERROR_REPORTING` | Enable error reporting | `false` | No |

### 3. Production Configuration Example

```env
# Production Environment
VITE_APP_ENV=production
VITE_API_URL=https://api.yourcompany.com
VITE_API_TIMEOUT=60000
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_ONBOARDING=true
VITE_ENABLE_ERROR_REPORTING=true
VITE_CACHE_DURATION=7200000
VITE_MAX_CACHE_SIZE=209715200
```

## Build Process

### 1. Manual Build

```bash
# Install dependencies
npm ci

# Run linting and type checking
npm run lint
npm run type-check

# Build for production
npm run build:prod

# Preview the build locally
npm run preview:prod
```

### 2. Automated Build Script

Use the provided deployment script:

```bash
# Make the script executable
chmod +x deploy.sh

# Deploy for production
./deploy.sh production

# Deploy for staging
./deploy.sh staging
```

The script will:
- Clean previous builds
- Install dependencies
- Run linting and type checking
- Build the application
- Create Docker image (if Docker is available)
- Generate deployment summary

## Deployment Options

### Option 1: Static File Hosting

1. **Build the application:**
   ```bash
   npm run build:prod
   ```

2. **Upload the `dist` folder** to your web server

3. **Configure your web server** to:
   - Serve static files from the `dist` directory
   - Handle client-side routing (redirect all routes to `index.html`)
   - Proxy API requests to your backend server

#### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://your-backend-server:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Option 2: Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t interview-prep-dashboard .
   ```

2. **Run the container:**
   ```bash
   docker run -p 80:80 interview-prep-dashboard
   ```

3. **Or use Docker Compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Option 3: CDN Deployment

For global distribution, deploy to a CDN like:

- **Netlify:** Connect your Git repository for automatic deployments
- **Vercel:** Similar to Netlify with Git integration
- **AWS CloudFront + S3:** Upload build files to S3 and serve via CloudFront
- **Azure Static Web Apps:** Deploy directly from GitHub

#### Netlify Configuration

Create a `netlify.toml` file:

```toml
[build]
  publish = "dist"
  command = "npm run build:prod"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[redirects]]
  from = "/api/*"
  to = "https://your-api-domain.com/api/:splat"
  status = 200
  force = true
```

## Health Checks and Monitoring

### 1. Application Health

The application includes built-in health monitoring:

- **Health endpoint:** `/health` (when using nginx configuration)
- **API status:** Monitored via the health indicator in the app header
- **Error boundaries:** Catch and display application errors gracefully

### 2. Performance Monitoring

Monitor these metrics:

- **Bundle size:** Check build output for size warnings
- **Load time:** Monitor initial page load performance
- **API response times:** Track backend API performance
- **Error rates:** Monitor JavaScript errors and API failures

### 3. Logging

Configure logging based on environment:

- **Development:** Full debug logging to console
- **Production:** Error-level logging only
- **Error reporting:** Enable `VITE_ENABLE_ERROR_REPORTING` for production

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files with sensitive data
- Use different configurations for each environment
- Validate all environment variables on startup

### 2. Content Security Policy

The nginx configuration includes basic security headers. For enhanced security, configure CSP:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://your-api-domain.com;";
```

### 3. HTTPS

Always use HTTPS in production:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check `VITE_API_URL` configuration
   - Verify CORS settings on backend
   - Check network connectivity

2. **Build Failures**
   - Run `npm run type-check` to identify TypeScript errors
   - Check `npm run lint` for code quality issues
   - Verify all dependencies are installed

3. **Routing Issues**
   - Ensure web server is configured for SPA routing
   - Check that all routes redirect to `index.html`

4. **Performance Issues**
   - Enable gzip compression
   - Configure proper caching headers
   - Monitor bundle size and optimize if needed

### Debug Mode

Enable debug mode for troubleshooting:

```env
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
```

This will:
- Enable detailed console logging
- Show configuration information
- Display additional debugging information

## Rollback Strategy

1. **Keep previous builds:** Archive successful builds for quick rollback
2. **Blue-green deployment:** Maintain two identical environments
3. **Feature flags:** Use environment variables to disable problematic features
4. **Database compatibility:** Ensure frontend changes are backward compatible

## Maintenance

### Regular Tasks

1. **Update dependencies:** Run `npm audit` and update packages regularly
2. **Monitor performance:** Check build sizes and load times
3. **Review logs:** Monitor error rates and performance metrics
4. **Security updates:** Keep all dependencies up to date

### Scaling Considerations

- Use CDN for global distribution
- Implement proper caching strategies
- Monitor and optimize bundle sizes
- Consider code splitting for large applications

For additional support or questions, refer to the main project documentation or contact the development team.