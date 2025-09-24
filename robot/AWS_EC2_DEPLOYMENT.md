# AWS EC2 Production Deployment Guide

## 🚀 SSL Certificate Options for AWS EC2

### Option 1: Self-Signed Certificates (Quick Setup)

**Pros:**
- ✅ Quick and easy setup
- ✅ Works immediately
- ✅ No external dependencies

**Cons:**
- ❌ Browser security warnings
- ❌ Users must manually accept certificate
- ❌ Not trusted by default

**Setup:**
1. Update `.env` with your domain:
   ```env
   DOMAIN_NAME=your-domain.com
   FLASK_HOST=172.31.x.x  # Your EC2 private IP
   EC2_PUBLIC_IP=x.x.x.x  # Your EC2 Elastic IP (optional)
   ```

2. Generate certificate:
   ```bash
   python generate_ec2_ssl_cert.py
   ```

3. Configure DNS: Point `your-domain.com` to your EC2 Elastic IP

### Option 2: Let's Encrypt Certificates (Recommended for Production)

**Pros:**
- ✅ Trusted by all browsers
- ✅ No security warnings
- ✅ Auto-renewal
- ✅ Free

**Cons:**
- ❌ Requires domain verification
- ❌ Need port 80 temporarily open
- ❌ Slightly more complex setup

**Setup:**
1. **Prerequisites:**
   ```bash
   # On your EC2 instance
   sudo apt update
   sudo apt install certbot
   ```

2. **Open ports in Security Group:**
   - Port 80 (HTTP) - temporarily for verification
   - Port 443 (HTTPS) - for production
   - Port 5000 - for your Flask app

3. **Generate Let's Encrypt certificate:**
   ```bash
   # Stop any service using port 80
   sudo systemctl stop apache2 2>/dev/null || true
   
   # Generate certificate
   sudo certbot certonly --standalone -d your-domain.com
   ```

4. **Update .env for Let's Encrypt:**
   ```env
   DOMAIN_NAME=your-domain.com
   FLASK_HOST=172.31.x.x  # Your EC2 private IP
   SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
   SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
   ```

5. **Set permissions:**
   ```bash
   # Allow your user to read certificates
   sudo chmod 644 /etc/letsencrypt/live/your-domain.com/fullchain.pem
   sudo chmod 600 /etc/letsencrypt/live/your-domain.com/privkey.pem
   sudo chown root:ssl-cert /etc/letsencrypt/live/your-domain.com/privkey.pem
   sudo usermod -a -G ssl-cert $USER
   ```

6. **Auto-renewal setup:**
   ```bash
   # Test renewal
   sudo certbot renew --dry-run
   
   # Add to crontab
   echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
   ```

## 🔧 Complete AWS EC2 Deployment Steps

### 1. EC2 Instance Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip git -y

# Clone your repository
git clone <your-repo-url>
cd crypto-robot/robot5

# Install dependencies
pip3 install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

**For production, update these values:**
```env
# Change domain to your actual domain
DOMAIN_NAME=your-actual-domain.com

# Set to EC2 private IP for network binding
FLASK_HOST=172.31.x.x

# Production settings
FLASK_DEBUG=False
FLASK_ENV=production

# Choose certificate option:
# Option A: Self-signed
SSL_CERT_PATH=certs/cert.pem
SSL_KEY_PATH=certs/key.pem

# Option B: Let's Encrypt
# SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
# SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 3. Security Group Configuration

Allow these inbound rules:
- **Port 22**: SSH (your IP only)
- **Port 80**: HTTP (0.0.0.0/0) - for Let's Encrypt verification
- **Port 443**: HTTPS (0.0.0.0/0) - for direct Flask HTTPS access
- **Port 5000**: Custom TCP (0.0.0.0/0) - for Flask app

### 4. DNS Configuration

Point your domain's A record to your EC2 Elastic IP:
```
Type: A
Name: your-domain.com
Value: x.x.x.x (your EC2 Elastic IP)
TTL: 300
```

### 5. Start the Application

```bash
# Generate SSL certificates (if using self-signed)
python3 generate_ec2_ssl_cert.py

# Start the HTTPS server
python3 start_https_server.py
```

### 6. Create Systemd Service (Optional)

For auto-start and management:

```bash
# Create service file
sudo nano /etc/systemd/system/crypto-robot.service
```

```ini
[Unit]
Description=Crypto Robot HTTPS Web Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crypto-robot/robot5
Environment=PATH=/home/ubuntu/.local/bin
ExecStart=/usr/bin/python3 start_https_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable crypto-robot
sudo systemctl start crypto-robot

# Check status
sudo systemctl status crypto-robot
```

## 🎯 Testing Your Deployment

1. **DNS Resolution:**
   ```bash
   nslookup your-domain.com
   # Should return your EC2 Elastic IP
   ```

2. **SSL Certificate:**
   ```bash
   openssl s_client -connect your-domain.com:5000 -servername your-domain.com
   ```

3. **Web Access:**
   - Navigate to `https://your-domain.com:5000`
   - For self-signed: Accept security warning
   - For Let's Encrypt: Should load without warnings

## 🔍 Troubleshooting

### Common Issues:

1. **Connection Refused:**
   - Check security group allows port 5000
   - Verify FLASK_HOST is set to EC2 private IP

2. **SSL Certificate Errors:**
   - Ensure certificate files exist and are readable
   - Check certificate domain matches your actual domain

3. **DNS Issues:**
   - Verify A record points to correct Elastic IP
   - Wait for DNS propagation (up to 24 hours)

4. **Let's Encrypt Failures:**
   - Ensure port 80 is open during verification
   - Check domain is properly pointing to your server

### Log Locations:
- Application logs: Terminal output or systemd journal
- Let's Encrypt logs: `/var/log/letsencrypt/`
- System logs: `sudo journalctl -u crypto-robot`

## 📚 Additional Resources

- [AWS EC2 Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/working-with-security-groups.html)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot User Guide](https://certbot.eff.org/docs/using.html)
