# Deployment & GitHub Setup Guide

## GitHub Push Instructions

The repository structure is ready. To push to your GitHub account, follow these steps:

### Option 1: Using Personal Access Token (HTTPS)

1. **Create a Personal Access Token on GitHub:**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `write:repo_hook`
   - Copy the token

2. **Configure Git with your email:**
   ```bash
   cd /home/kali/Desktop/devnavigator
   
   # Make your GitHub email public or use GitHub-provided noreply email:
   # Go to https://github.com/settings/emails
   
   git config user.email "your_github_username@users.noreply.github.com"
   git config user.name "Your Name"
   ```

3. **Amend the last commit and push:**
   ```bash
   git commit --amend --no-edit
   git push -u origin main
   ```

   When prompted for password, use your Personal Access Token.

### Option 2: Using SSH (Recommended)

1. **Generate SSH key (if you don't have one):**
   ```bash
   ssh-keygen -t ed25519 -C "your_github_username@users.noreply.github.com"
   ```

2. **Add SSH key to GitHub:**
   - Copy your public key: `cat ~/.ssh/id_ed25519.pub`
   - Go to GitHub → Settings → SSH and GPG keys
   - Click "New SSH key" and paste

3. **Set up Git with SSH:**
   ```bash
   cd /home/kali/Desktop/devnavigator
   
   # Change remote URL from HTTPS to SSH
   git remote set-url origin git@github.com:batman-hash/campaign_people.git
   
   # Configure email
   git config user.email "batman-hash@users.noreply.github.com"
   git config user.name "batman-hash"
   ```

4. **Push:**
   ```bash
   git commit --amend --no-edit
   git push -u origin main
   ```

### Option 3: Quick Fix for Email Privacy

If you don't want to deal with email settings:

```bash
cd /home/kali/Desktop/devnavigator

# Reset and use GitHub noreply email from start
git reset --soft HEAD~1
git config user.email "batman-hash@users.noreply.github.com"
git config user.name "batman-hash"
git commit -m "Initial commit: DevNavigator email campaign platform"
git push -u origin main
```

## Installation & Setup

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get install -y python3 python3-pip nodejs npm cmake sqlite3 libcurl4-openssl-dev

# macOS
brew install python3 nodejs cmake sqlite3 curl
```

### Quick Setup

```bash
cd /home/kali/Desktop/devnavigator

# Make scripts executable
chmod +x scripts/build/setup.sh scripts/build/build.sh scripts/extraction/extract-emails.sh

# Run setup (installs all dependencies)
./scripts/build/setup.sh
```

This will:
- Install Python packages
- Install Node packages
- Initialize database
- Create default templates
- Build C++ email sender

### Manual Setup (if needed)

```bash
# Python setup
pip install -r requirements.txt
python3 devnavigator.py init-db
python3 python_engine/template_manager.py

# Node setup
npm install

# C++ setup
./scripts/build/build.sh
```

## Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your SMTP credentials:**
   ```env
   SMTP_URL=smtp://smtp.gmail.com:587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   SMTP_FROM=your_email@gmail.com
   ```

3. **For Gmail Users:**
   - Enable 2FA: https://myaccount.google.com/security
   - Create App Password: https://myaccount.google.com/apppasswords
   - Use App Password in `.env`

## Running the System

### 1. Extract Emails

```bash
# From a text file with emails (one per line)
./scripts/extraction/extract-emails.sh contacts.txt

# Or using Python CLI
python3 devnavigator.py extract-emails --file emails.txt --store

# From JSON
echo '["test@example.com", "user@company.com"]' | python3 devnavigator.py extract-emails --text "$1" --store
```

### 2. View Statistics

```bash
python3 devnavigator.py stats
```

### 3. Manage Templates

```bash
# List all templates
python3 devnavigator.py list-templates

# Add custom template
python3 devnavigator.py add-template --name "my_template" --subject "Hello $name"
```

### 4. Send Emails

```bash
# Build C++ sender
./scripts/build/build.sh

# Send emails
npm run send:emails

# Monitor progress in logs
tail -f database/*.log
```

## Docker Deployment

### Build Docker Image

```bash
npm run docker:build
```

### Run Container

```bash
npm run docker:run
```

This mounts your `.env` and `database/` for persistence.

## Cloud Deployment

### AWS EC2

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Clone repository
git clone https://github.com/batman-hash/campaign_people.git
cd campaign_people

# Run setup
./scripts/build/setup.sh

# Start email sender (in background)
nohup npm run send:emails &
```

### Heroku

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create campaign-people

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Set environment variables in App settings
3. Add build and run commands:
   - Build: `./scripts/build/setup.sh`
   - Run: `npm run send:emails`

## Database Backup

```bash
# Backup SQLite database
cp database/devnav.db database/backups/devnav_$(date +%Y%m%d_%H%M%S).db

# Restore from backup
cp database/backups/devnav_20260329_101000.db database/devnav.db
```

## Monitoring & Logging

```bash
# Check email send logs
sqlite3 database/devnav.db "SELECT * FROM email_logs LIMIT 20;"

# View campaign statistics
sqlite3 database/devnav.db "SELECT status, COUNT(*) FROM campaigns GROUP BY status;"

# Check failed emails
sqlite3 database/devnav.db "SELECT email, error_message FROM email_logs WHERE status = 'failed';"
```

## Troubleshooting

### SMTP Connection Issues

```bash
# Test SMTP connection
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your@gmail.com', 'your_app_password')
print('✓ Connected successfully')
server.quit()
"
```

### Database Locked

```bash
# Close any open connections and restart
pkill -f devnavigator
sleep 5
npm run send:emails
```

### Import Errors

```bash
# Reinstall Python packages
pip install --upgrade -r requirements.txt

# Verify installation
python3 -c "import sqlite3, dotenv; print('OK')"
```

## Security Best Practices

1. **Keep .env secure:**
   ```bash
   chmod 600 .env
   ```

2. **Regular database backups:**
   ```bash
   # Automate with cron
   0 2 * * * /path/to/backup.sh
   ```

3. **Update dependencies regularly:**
   ```bash
   npm update
   pip install --upgrade -r requirements.txt
   ```

4. **Monitor email logs for failures:**
   ```bash
   sqlite3 database/devnav.db "SELECT COUNT(*) FROM email_logs WHERE status = 'failed';"
   ```

## Support

- Documentation: See [README.md](README.md)
- Issues: Report on GitHub
- Email: matteopennacchia43@gmail.com

## License

MIT License
