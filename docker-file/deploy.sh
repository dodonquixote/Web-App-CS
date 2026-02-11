#!/bin/bash
# Deployment script for VPS production

set -e  # Exit on error

echo "🚀 Starting deployment to production..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Copy .env.production.template to .env and configure it first:"
    echo "  cp .env.production.template .env"
    echo "  nano .env"
    exit 1
fi

# Check if DEBUG=False
if grep -q "DJANGO_DEBUG=True" .env; then
    echo "⚠️  WARNING: DEBUG=True detected in .env"
    read -p "Are you sure you want to deploy with DEBUG=True? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled. Please set DJANGO_DEBUG=False in .env"
        exit 1
    fi
fi

# Pull latest code (if using git)
if [ -d "../.git" ]; then
    echo "📥 Pulling latest code..."
    cd ..
    git pull
    cd docker-file
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml down

# Build and start containers
echo "🏗️  Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "✅ Checking service status..."
docker compose -f docker-compose.prod.yml ps

# Show logs
echo ""
echo "📋 Recent logs:"
docker compose -f docker-compose.prod.yml logs --tail=50

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Access your application:"
echo "   HTTP:  http://$(hostname -I | awk '{print $1}')"
echo "   Check logs: docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "📝 Next steps:"
echo "   1. Create superuser: docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo "   2. Setup SSL certificate (see DEPLOYMENT_VPS.md)"
echo "   3. Configure domain DNS"
echo ""
