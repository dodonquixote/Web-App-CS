#!/bin/bash
# Quick SSL setup script using Let's Encrypt

set -e

# Check required variables
if [ -z "$1" ]; then
    echo "Usage: ./setup-ssl.sh yourdomain.com your-email@example.com"
    echo "Example: ./setup-ssl.sh example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-""}

if [ -z "$EMAIL" ]; then
    read -p "Enter your email address: " EMAIL
fi

echo "🔒 Setting up SSL for $DOMAIN..."

# Create directories
mkdir -p certbot/conf certbot/www

# Temporarily disable SSL in nginx for initial certificate
echo "📝 Configuring nginx for HTTP challenge..."
cat > nginx.conf.temp << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    upstream django {
        server web:8000;
    }
    server {
        listen 80;
        server_name _;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
        }
    }
}
EOF

# Backup current nginx.conf
cp nginx.conf nginx.conf.backup

# Use temporary config
mv nginx.conf.temp nginx.conf

# Restart nginx
echo "🔄 Restarting nginx..."
docker compose -f docker-compose.prod.yml restart nginx

# Wait for nginx to start
sleep 5

# Get certificate
echo "📜 Requesting SSL certificate from Let's Encrypt..."
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Restore full nginx config
echo "✅ Certificate obtained! Restoring full nginx configuration..."
mv nginx.conf.backup nginx.conf

# Update nginx.conf with your domain
sed -i "s/yourdomain.com/$DOMAIN/g" nginx.conf

# Restart nginx with SSL
docker compose -f docker-compose.prod.yml restart nginx

echo ""
echo "🎉 SSL setup complete!"
echo "Your site is now available at: https://$DOMAIN"
echo ""
echo "📝 Certificate auto-renewal:"
echo "Add this to crontab (crontab -e):"
echo "0 0 * * 0 cd $(pwd) && docker compose -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.prod.yml restart nginx"
echo ""
