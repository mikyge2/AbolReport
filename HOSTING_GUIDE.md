# 🚀 Complete Self-Hosting Guide for Factory Portal

This guide will help you deploy and host the Factory Portal application on your own server or cloud platform.

## 📋 Prerequisites

### System Requirements
- **Operating System:** Ubuntu 20.04+ or CentOS 8+ (Linux recommended)
- **RAM:** Minimum 2GB, Recommended 4GB+
- **Storage:** Minimum 10GB free space
- **Network:** Public IP address for web access

### Required Software
- Node.js 18+ and npm/yarn
- Python 3.9+
- MongoDB 5.0+
- Nginx (for reverse proxy)
- PM2 (for process management)
- SSL Certificate (Let's Encrypt recommended)

## 🎯 Step-by-Step Deployment

### Step 1: Server Setup

#### 1.1 Update System
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 1.2 Install Required Software
```bash
# Install Node.js 18 (Ubuntu)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.9+ and pip
sudo apt install python3 python3-pip python3-venv -y

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Install Nginx
sudo apt install nginx -y

# Install PM2 globally
sudo npm install -g pm2 yarn
```

#### 1.3 Start and Enable Services
```bash
sudo systemctl start mongod
sudo systemctl enable mongod
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 2: Application Deployment

#### 2.1 Create Application Directory
```bash
sudo mkdir -p /var/www/factory-portal
sudo chown $USER:$USER /var/www/factory-portal
cd /var/www/factory-portal
```

#### 2.2 Copy Your Application Files
```bash
# Method 1: Using Git (if you have a repository)
git clone https://your-repo-url.git .

# Method 2: Upload files manually
# - Use SCP, SFTP, or file upload to copy your entire /app directory
# - Ensure all files from your current /app directory are copied
```

#### 2.3 Setup Backend Environment
```bash
cd backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create production environment file
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=factory_portal_prod
STRIPE_API_KEY=your_stripe_key_here
SECRET_KEY=your-super-secret-key-change-this-in-production
EOF
```

#### 2.4 Setup Frontend Environment
```bash
cd ../frontend

# Install dependencies
yarn install

# Create production environment file
cat > .env << EOF
REACT_APP_BACKEND_URL=https://yourdomain.com/api
EOF

# Build production version
yarn build
```

### Step 3: Database Setup

#### 3.1 Create Production Database
```bash
# Connect to MongoDB
mongosh

# Create database and user
use factory_portal_prod
db.createUser({
  user: "factory_user",
  pwd: "secure_password_here",
  roles: [{ role: "readWrite", db: "factory_portal_prod" }]
})

# Exit MongoDB shell
exit
```

#### 3.2 Import Initial Data (Optional)
```bash
# If you have existing data to import
cd /var/www/factory-portal
python3 populate_dummy_data.py  # Run your data population script
```

### Step 4: Process Management with PM2

#### 4.1 Create PM2 Configuration
```bash
cd /var/www/factory-portal

# Create ecosystem.config.js
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'factory-portal-backend',
      script: 'venv/bin/python',
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8001',
      cwd: './backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend-combined.log'
    },
    {
      name: 'factory-portal-frontend',
      script: 'serve',
      args: '-s build -l 3000',
      cwd: './frontend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log'
    }
  ]
}
EOF

# Install serve globally for frontend
sudo npm install -g serve

# Create logs directory
mkdir -p logs

# Start applications with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Step 5: Nginx Configuration

#### 5.1 Create Nginx Site Configuration
```bash
sudo cat > /etc/nginx/sites-available/factory-portal << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;

    # API routes - proxy to backend
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Frontend - serve React build
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        
        # Fallback for React Router
        try_files \$uri \$uri/ /index.html;
    }

    # Static assets optimization
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/factory-portal /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 6: SSL Certificate Setup

#### 6.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

#### 6.2 Obtain SSL Certificate
```bash
# Replace yourdomain.com with your actual domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow the prompts to complete SSL setup
```

#### 6.3 Auto-renewal Setup
```bash
# Test auto-renewal
sudo certbot renew --dry-run

# Set up cron job for auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### Step 7: Firewall Configuration

```bash
# Install and configure UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 27017  # MongoDB (only if external access needed)
sudo ufw status
```

### Step 8: Monitoring and Logs

#### 8.1 Setup Log Rotation
```bash
sudo cat > /etc/logrotate.d/factory-portal << EOF
/var/www/factory-portal/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        pm2 reload all
    endscript
}
EOF
```

#### 8.2 Monitoring Commands
```bash
# Check PM2 processes
pm2 status
pm2 logs

# Check Nginx status
sudo systemctl status nginx

# Check MongoDB status
sudo systemctl status mongod

# Check system resources
htop
df -h
```

## 🔧 Production Optimizations

### Database Optimization
```bash
# Connect to MongoDB and create indexes
mongosh factory_portal_prod
db.daily_logs.createIndex({ "date": 1 })
db.daily_logs.createIndex({ "factory_id": 1 })
db.daily_logs.createIndex({ "created_by": 1 })
db.users.createIndex({ "username": 1 }, { unique: true })
```

### Backend Performance
```python
# In your backend/.env file, add:
WORKERS=4  # Number of CPU cores
MAX_CONNECTIONS=100
```

### Frontend Optimization
```bash
# Already done during build, but ensure these are optimized:
# - Code splitting
# - Lazy loading
# - Image optimization
# - Bundle analysis
yarn build --analyze
```

## 🛡️ Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY in backend
- [ ] Enable MongoDB authentication
- [ ] Configure firewall properly
- [ ] Set up SSL certificates
- [ ] Regular security updates
- [ ] Backup strategy implemented
- [ ] Monitor application logs
- [ ] Rate limiting configured
- [ ] Environment variables secured

## 📁 Backup Strategy

### Daily Backup Script
```bash
#!/bin/bash
# Create backup script
cat > /var/www/factory-portal/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/factory-portal"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db factory_portal_prod --out $BACKUP_DIR/mongo_$DATE

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /var/www/factory-portal

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /var/www/factory-portal/backup.sh

# Add to crontab for daily backups at 2 AM
echo "0 2 * * * /var/www/factory-portal/backup.sh" | crontab -
```

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] Domain name configured and DNS pointing to server
- [ ] Server meets minimum requirements
- [ ] All required software installed
- [ ] Application files uploaded
- [ ] Environment variables configured

### Deployment
- [ ] Backend dependencies installed
- [ ] Frontend built for production
- [ ] Database setup and populated
- [ ] PM2 processes started
- [ ] Nginx configured and running
- [ ] SSL certificate installed

### Post-deployment
- [ ] Application accessible via domain
- [ ] All features working correctly
- [ ] Logs are being generated
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Security measures in place

## 🆘 Troubleshooting

### Common Issues and Solutions

**Application not starting:**
```bash
pm2 logs  # Check application logs
sudo nginx -t  # Test Nginx configuration
sudo systemctl status nginx  # Check Nginx status
```

**Database connection issues:**
```bash
sudo systemctl status mongod  # Check MongoDB status
mongosh  # Test MongoDB connection
```

**SSL certificate issues:**
```bash
sudo certbot certificates  # Check certificate status
sudo certbot renew  # Renew if needed
```

**Performance issues:**
```bash
htop  # Check system resources
pm2 monit  # Monitor PM2 processes
sudo netstat -tlnp  # Check port usage
```

## 📞 Support

For additional support:
1. Check application logs in `/var/www/factory-portal/logs/`
2. Review Nginx logs: `/var/log/nginx/`
3. Check system logs: `journalctl -f`
4. Monitor resource usage: `htop`, `df -h`

---

**🎉 Congratulations!** Your Factory Portal should now be live and accessible at your domain with SSL encryption, automatic backups, and production-grade configuration.