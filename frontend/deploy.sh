#!/bin/bash

# Interview Prep Dashboard Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
BUILD_DIR="dist"
DOCKER_IMAGE_NAME="interview-prep-dashboard"
DOCKER_TAG="${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}🚀 Starting deployment for ${ENVIRONMENT} environment${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

# Check if required files exist
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found. Are you in the frontend directory?${NC}"
    exit 1
fi

if [ ! -f ".env.${ENVIRONMENT}" ]; then
    echo -e "${YELLOW}⚠️  .env.${ENVIRONMENT} not found. Using default configuration.${NC}"
fi

# Clean previous build
echo -e "${BLUE}🧹 Cleaning previous build...${NC}"
npm run clean

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
npm ci

# Run linting
echo -e "${BLUE}🔍 Running linter...${NC}"
npm run lint

# Run type checking
echo -e "${BLUE}🔧 Running type check...${NC}"
npm run type-check

# Build the application
echo -e "${BLUE}🏗️  Building application for ${ENVIRONMENT}...${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    npm run build:prod
elif [ "$ENVIRONMENT" = "staging" ]; then
    npm run build:staging
else
    npm run build
fi

# Verify build output
if [ ! -d "$BUILD_DIR" ]; then
    echo -e "${RED}❌ Build failed - $BUILD_DIR directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build completed successfully${NC}"

# Build size analysis
BUILD_SIZE=$(du -sh $BUILD_DIR | cut -f1)
echo -e "${BLUE}📊 Build size: $BUILD_SIZE${NC}"

# List build artifacts
echo -e "${BLUE}📁 Build artifacts:${NC}"
ls -la $BUILD_DIR/

# Docker deployment (optional)
if command -v docker &> /dev/null; then
    echo -e "${BLUE}🐳 Building Docker image...${NC}"
    
    # Build Docker image
    docker build -t "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}" -t "${DOCKER_IMAGE_NAME}:${ENVIRONMENT}-latest" .
    
    echo -e "${GREEN}✅ Docker image built: ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}${NC}"
    
    # Optional: Push to registry
    if [ "$PUSH_TO_REGISTRY" = "true" ]; then
        echo -e "${BLUE}📤 Pushing to Docker registry...${NC}"
        docker push "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
        docker push "${DOCKER_IMAGE_NAME}:${ENVIRONMENT}-latest"
        echo -e "${GREEN}✅ Images pushed to registry${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found. Skipping Docker build.${NC}"
fi

# Generate deployment summary
echo -e "${BLUE}📋 Deployment Summary${NC}"
echo "=================================="
echo "Environment: $ENVIRONMENT"
echo "Build Time: $(date)"
echo "Build Size: $BUILD_SIZE"
echo "Docker Image: ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
echo "=================================="

# Success message
echo -e "${GREEN}🎉 Deployment preparation completed successfully!${NC}"

# Next steps
echo -e "${BLUE}📝 Next Steps:${NC}"
if command -v docker &> /dev/null; then
    echo "1. Test the Docker image: docker run -p 80:80 ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
    echo "2. Deploy using: docker-compose -f docker-compose.prod.yml up -d"
else
    echo "1. Copy the $BUILD_DIR folder to your web server"
    echo "2. Configure your web server to serve the static files"
    echo "3. Set up API proxy to your backend server"
fi

echo "4. Update your DNS records if needed"
echo "5. Monitor the application logs after deployment"

exit 0