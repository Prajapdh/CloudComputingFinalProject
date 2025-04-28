import os, sys
sys.path.insert(0, '/var/www/CloudComputingFinalProject/app')

os.environ.setdefault('DB_USER', 'admin')
os.environ.setdefault('DB_PASS', 'admin')
os.environ.setdefault('DB_HOST', '34.45.4.119')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_NAME', '400_transactions')

from flaskapp import app as application
