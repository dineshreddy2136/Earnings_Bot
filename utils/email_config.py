"""Email Configuration Loader"""
import os
from pathlib import Path
from typing import Dict, List, Optional


def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from .env file"""
    if env_path is None:
        # Look for .env in project root
        current_dir = Path(__file__).parent.parent
        env_path = current_dir / '.env'
    else:
        env_path = Path(env_path)
    
    env_vars = {}
    
    if not env_path.exists():
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def get_email_config() -> Dict:
    """Get email configuration from .env file or config.yaml"""
    from utils.config_loader import config
    
    # Check if we should use .env file
    use_env = config.get('email', 'use_env_file', default=True)
    
    if use_env:
        # Try to load from .env file
        env_vars = load_env_file()
        
        if env_vars:
            # Parse recipients (comma-separated in .env)
            recipients_str = env_vars.get('RECIPIENT_EMAILS', '')
            recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
            
            return {
                'smtp_server': env_vars.get('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(env_vars.get('SMTP_PORT', 587)),
                'sender_email': env_vars.get('SENDER_EMAIL', ''),
                'sender_password': env_vars.get('SENDER_PASSWORD', ''),
                'recipients': recipients
            }
    
    # Fallback to config.yaml
    return {
        'smtp_server': config.get('email', 'smtp_server', default='smtp.gmail.com'),
        'smtp_port': config.get('email', 'smtp_port', default=587),
        'sender_email': config.get('email', 'sender_email', default=''),
        'sender_password': config.get('email', 'sender_password', default=''),
        'recipients': config.get('email', 'recipients', default=[])
    }


def is_email_configured() -> bool:
    """Check if email is properly configured"""
    email_config = get_email_config()
    
    sender_email = email_config.get('sender_email', '')
    sender_password = email_config.get('sender_password', '')
    recipients = email_config.get('recipients', [])
    
    # Check if credentials are filled in (not empty or example values)
    if not sender_email or 'your_email' in sender_email or 'example.com' in sender_email:
        return False
    
    if not sender_password or 'your_' in sender_password or len(sender_password) < 10:
        return False
    
    if not recipients or any('example.com' in r for r in recipients):
        return False
    
    return True
