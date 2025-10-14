"""
Configuration settings for PDF Parsing Project
"""
import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    UPLOAD_FOLDER = 'downloads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

    # Selenium settings
    SELENIUM_TIMEOUT = 120
    SELENIUM_RETRIES = 3
    CHROME_HEADLESS = True  # Set to False for debugging

    # AI model settings
    AI_MODEL_NAME = "ml6team/mt5-small-german-finetune-mlsum"

    # Logging settings
    LOG_FILE = 'logs/german_processor.log'
    LOG_LEVEL = 'INFO'

    # Directory settings
    TEMPLATES_FOLDER = 'templates'
    STATIC_FOLDER = 'static'

    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('static/js', exist_ok=True)
        os.makedirs('backend', exist_ok=True)
