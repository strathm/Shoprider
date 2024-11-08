import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'  # Change as needed
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Set your environment variables
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Set your environment variables
    ADMINS = ['your_admin_email@example.com']
    
    # Pagination settings for groups, loans, and other records
    POSTS_PER_PAGE = 20

    # File upload settings
    UPLOADED_PHOTOS_DEST = os.environ.get('UPLOADED_PHOTOS_DEST', 'static/images/uploads')

    # Timezone settings
    TIMEZONE = os.environ.get('TIMEZONE', 'UTC')

    # Loan interest rate settings (configurable per SACCO)
    LOAN_INTEREST_RATE = float(os.environ.get('LOAN_INTEREST_RATE', '5.0'))  # Default interest rate 5%

    # Savings withdrawal limit per day
    DAILY_WITHDRAWAL_LIMIT = float(os.environ.get('DAILY_WITHDRAWAL_LIMIT', '1000.00'))

    # M-Pesa API configuration
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')  # M-Pesa Consumer Key
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')  # M-Pesa Consumer Secret
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')  # M-Pesa Shortcode
    MPESA_LIVE_URL = 'https://api.safaricom.co.ke/'
    MPESA_TOKEN_URL = f'{MPESA_LIVE_URL}oauth/v1/generate?grant_type=client_credentials'
    MPESA_PAYBILL_URL = f'{MPESA_LIVE_URL}mpesa/paybill/v1/processpayment'  # Paybill endpoint

# Example for different environments
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Enable SQL query logging in development
    # Additional development-specific settings can be added here

class ProductionConfig(Config):
    DEBUG = False
    # Ensure production uses a strong secret key from environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_production_secret_key'
    # Additional production-specific settings can be added here

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for testing
    DEBUG = True
    # Additional testing-specific settings can be added here

# You can add configurations for staging, QA, etc., as necessary
