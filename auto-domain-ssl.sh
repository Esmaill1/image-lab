#!/usr/bin/env bash

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (e.g., sudo $0)"
  exit 1
fi

echo "=== Reverse Proxy + HTTPS Setup (nginx + Let's Encrypt) ==="

read -rp "Enter your domain name (e.g. example.com): " DOMAIN
read -rp "Enter upstream address (e.g. http://127.0.0.1:3000): " UPSTREAM
read -rp "Enter your email for Let's Encrypt (used for renewal notifications): " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$UPSTREAM" ] || [ -z "$EMAIL" ]; then
  echo "Domain, upstream, and email are required."
  exit 1
fi

echo
echo "Domain:   $DOMAIN"
echo "Upstream: $UPSTREAM"
echo "Email:    $EMAIL"
echo

# Basic checks
echo "Updating package index..."
apt update -y

# Install nginx
if ! command -v nginx >/dev/null 2>&1; then
  echo "Installing nginx..."
  apt install -y nginx
else
  echo "nginx already installed."
fi

# Install certbot + nginx plugin
if ! command -v certbot >/dev/null 2>&1; then
  echo "Installing certbot and nginx plugin..."
  apt install -y certbot python3-certbot-nginx
else
  echo "certbot already installed."
fi

NGINX_SITE="/etc/nginx/sites-available/$DOMAIN.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN.conf"

echo "Creating nginx HTTP reverse proxy config: $NGINX_SITE"

cat > "$NGINX_SITE" <<EOF
server {
    listen 80;
    listen [::]:80;

    server_name $DOMAIN;

    location / {
        proxy_pass $UPSTREAM;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
ln -sf "$NGINX_SITE" "$NGINX_ENABLED"

echo "Testing nginx configuration..."
nginx -t

echo "Reloading nginx..."
systemctl reload nginx

echo
echo "=== Obtaining Let's Encrypt certificate via certbot ==="
echo "IMPORTANT:"
echo " - Your domain ($DOMAIN) must point (DNS A record) to this server's IP."
echo " - Ports 80 and 443 must be open in any firewall."
echo

# Run certbot to get cert and auto-config nginx (with HTTP->HTTPS redirect)
certbot --nginx \
  -d "$DOMAIN" \
  --non-interactive \
  --redirect \
  --agree-tos \
  -m "$EMAIL"

echo
echo "=== Done! ==="
echo "Your reverse proxy is now set up with HTTPS."
echo " - URL:   https://$DOMAIN"
echo " - Proxy: $UPSTREAM"
echo
echo "Certbot has also installed an automatic renewal timer (systemd timer/cron)."
