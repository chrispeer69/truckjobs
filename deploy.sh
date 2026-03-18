#!/bin/bash

# Configuration - REPLACE THESE WITH YOUR VPS DETAILS
VPS_USER="your_vps_user"      # e.g., root, ubuntu
VPS_IP="your_vps_ip"         # e.g., 123.456.78.90
PROJECT_DIR="~/Chris-Truckjobs" # The directory where the project is on your VPS

echo "🚀 Starting deployment to $VPS_IP..."

# 1. Commit and push local changes
echo "📤 Pushing changes to GitHub..."
git add .
git commit -m "Deploy update: $(date)"
git push origin main

# 2. SSH into VPS and update
echo "🌐 Updating VPS..."
ssh $VPS_USER@$VPS_IP << EOF
    cd $PROJECT_DIR
    git pull origin main
    
    # Rebuild and restart containers
    echo "🐳 Restarting Docker containers..."
    docker-compose down
    docker-compose up -d --build
    
    # Run migrations (optional but recommended)
    echo "🔧 Running migrations..."
    docker-compose exec -T web python manage.py migrate
    
    echo "✅ VPS updated successfully!"
EOF

echo "✨ Deployment complete!"
