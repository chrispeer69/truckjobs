# Deployment Guide

This guide explains how to deploy the TruckJobs application to your VPS.

## Prerequisites
- Docker and Docker Compose installed on your VPS.
- Git repository cloned on your VPS.
- SSH access to your VPS configured (preferably with SSH keys).

## Using the Deployment Script
We've created a `deploy.sh` script to automate the process.

1.  **Configure the script**: Open `deploy.sh` and replace the placeholders with your VPS details:
    -   `VPS_USER`: Your SSH username.
    -   `VPS_IP`: Your VPS IP address.
    -   `PROJECT_DIR`: Path to the project on your VPS.
2.  **Make it executable**:
    ```bash
    chmod +x deploy.sh
    ```
3.  **Run the script**:
    ```bash
    ./deploy.sh
    ```

## Manual Deployment Steps
If you prefer to deploy manually, follow these steps:

1.  **Push changes locally**:
    ```bash
    git add .
    git commit -m "Your message"
    git push origin main
    ```
2.  **SSH into your VPS**:
    ```bash
    ssh your_user@your_ip
    ```
3.  **Update the code**:
    ```bash
    cd ~/Chris-Truckjobs
    git pull origin main
    ```
4.  **Restart the application**:
    ```bash
    docker-compose down
    docker-compose up -d --build
    ```
5.  **Run migrations**:
    ```bash
    docker-compose exec web python manage.py migrate
    ```

## Production Environment Variables
Ensure your `.env` file on the VPS includes the following for production:
```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,your_vps_ip
DJANGO_SECRET_KEY=yoursecretkey
```
