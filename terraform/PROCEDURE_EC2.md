# Operaton to run for one simple robot

## Start EC2

./start-stop-ec2.sh start


## connecting to EC2
export EC2_IP=$(terraform output -raw ec2_eip_address)
ssh -i web-crypto-robot-key.pem ec2-user@$EC2_IP

In case of receration of EC2:
ssh-keygen -R $EC2_IP

## creating the first time the SSH key for git clone
cat .ssh/id_rsa.pub

-- créer dans jmontiel-fr un SSH key et y copier la clé ssh pub précédente


## check verisons
git --version
python -V
pip -V

git clone git@github.com:jmontiel-fr/crypto-robot.git
cd crypto-robot
sudo yum update


## Other times
git pull

## configure & start Robot5 ou Robot6
cd robot5
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

## Setup .env
cp .env-prod .env

# OR manually ensure .env has correct production settings:
# DOMAIN_NAME=jack.crypto-robot-itechsource.com
# SSL_CERT_PATH=/etc/letsencrypt/live/jack.crypto-robot-itechsource.com/fullchain.pem
# SSL_KEY_PATH=/etc/letsencrypt/live/jack.crypto-robot-itechsource.com/privkey.pem
# FLASK_ENV=production

## generate Letsencrypt certificate

chmod a+x setup-letsencrypt.sh
sudo ./setup-letsencrypt.sh jack.crypto-robot-itechsource.com \
    jacky.montiel@gmail.com

# Start webapp (HTTPS flask server with Let's Encrypt)
##### python main.py --mode web --port 5000 --host 54.228.239.198

# Initialize database (first time only - IMPORTANT!)
python init_database.py

# Start the HTTPS server
sudo $(which python) start_https_server.py


# Start robot
TBC


