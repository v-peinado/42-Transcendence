from cryptography.fernet import Fernet
from .vault import VaultClient
import logging
import os

# This file is used to retrieve and validate the encryption key from Vault or environment.
# The key is used to encrypt and decrypt email directions in the database,
# following the GDPR guidelines.

# The key is stored in Vault and retrieved at runtime to ensure security.
# If the key is not found in Vault, it falls back to the environment variable.

logger = logging.getLogger(__name__)

def get_encryption_key():
    """
    Retrieves and validates the encryption key from Vault or environment.
    Returns the validated encryption key or raises an exception if invalid.
    """
    try:
        # First try to get from Vault
        vault = VaultClient()
        gdpr_secrets = vault.get_secrets('django/gdpr')
        
        if gdpr_secrets and 'ENCRYPTION_KEY' in gdpr_secrets:
            key = gdpr_secrets['ENCRYPTION_KEY']
            # Ensure key is properly padded
            if not key.endswith('='):
                key += '=' * (-len(key) % 4)
            encryption_key = key.encode()
            logger.info("Successfully loaded ENCRYPTION_KEY from Vault")
        else:
            # If not in Vault, try environment variable
            env_key = os.environ.get('ENCRYPTION_KEY')
            if not env_key:
                logger.critical("ENCRYPTION_KEY not found in Vault or environment")
                raise ValueError("ENCRYPTION_KEY not found in Vault or environment")
                
            if not env_key.endswith('='):
                env_key += '=' * (-len(env_key) % 4)
            encryption_key = env_key.encode()
            logger.warning("Using ENCRYPTION_KEY from environment (Vault not available)")

        # Validate the key format
        try:
            Fernet(encryption_key)
            logger.info("ENCRYPTION_KEY validation successful")
            return encryption_key
        except Exception as e:
            logger.error(f"Invalid ENCRYPTION_KEY format: {e}")
            raise ValueError("Invalid ENCRYPTION_KEY format")

    except Exception as e:
        logger.critical(f"Failed to set up ENCRYPTION_KEY: {e}")
        raise SystemExit("Cannot start without valid ENCRYPTION_KEY")
