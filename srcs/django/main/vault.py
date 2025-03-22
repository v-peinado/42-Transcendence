from urllib3.exceptions import InsecureRequestWarning
from dotenv import load_dotenv
from typing import Dict, Any
import requests
import warnings
import logging
import hvac # HashiCorp Vault client (connect to Vault)
import time # to wait for Vault to be unsealed
import os # to read the token file

# This file is to connect to Vault and retrieve secrets from it (client)

# Configure logger
logger = logging.getLogger(__name__)

# Disable SSL warnings for Vault connection (because is a self-signed certificate)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

_secrets_cache = {}  # Cache for secrets

class VaultClient:
    def __init__(self):
        
        # Wait for token file
        token_file = "/tmp/ssl/django_token" # store token...
        
        # Read token from file
        try:
            with open(token_file, "r") as f:
                token = f.read().strip()
        except Exception as e:
            logger.error(f"Error reading Vault token: {e}")
            token = None

        # Config client with token - Updated URL to point to vault service
        with warnings.catch_warnings(): # Ignore warnings of self-signed certificate
            warnings.simplefilter("ignore")
            self.client = hvac.Client(url="https://vault:8200", verify=False, token=token) # Connect to Vault

    def _is_vault_sealed(self) -> bool:
        """Check if the Vault server is sealed"""
        try:
            response = requests.get("https://vault:8200/v1/sys/seal-status", verify=False) 
            return response.json().get("sealed", True) # Check if the server is sealed and return True if it is and False if it is not
        except Exception: # If there is an exception, return True too (to wait for unseal)
            return True

    def get_secrets(self, path: str) -> Dict[str, Any]:
        """Get secrets from Vault"""
        if path in _secrets_cache:
            return _secrets_cache[path]

        retries = 0 # initialize retries
        max_retries = 5	# maximum number of retries 

        while retries < max_retries:
            try:
                if self._is_vault_sealed():  # Using private method
                    logger.info("⌛️Vault is sealed, waiting for unseal...")
                    time.sleep(2)
                    retries += 1
                    continue

                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point="secret"
                )
                secrets = response["data"]["data"]
                _secrets_cache[path] = secrets
                return secrets
            except Exception as e:
                if retries == max_retries - 1:
                    logger.error(f"❌Error fetching secrets from Vault: {e}")
                retries += 1
                time.sleep(2)
        return {}


def wait_for_token(max_attempts=30, delay=2):
    """Wait for Vault token file to be available"""
    token_file = "/tmp/ssl/django_token"

    for attempt in range(max_attempts):
        try:
            if os.path.exists(token_file):
                with open(token_file, "r") as f:
                    token = f.read().strip()
                    if token:
                        logger.info(f"✅Found Vault token after {attempt + 1} attempts")
                        return token
            logger.info(f"⌛️Waiting for token file... ({attempt + 1}/{max_attempts})")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"❌Error reading token: {e}")
            time.sleep(delay)
    return None


def get_client():
    """Create a Vault client and authenticate with token"""
    token = wait_for_token()
    if not token:
        logger.error("❌Failed to get Vault token")
        return None

    try:
        client = hvac.Client(url="https://vault:8200", token=token, verify=False)

        if not client.is_authenticated():
            logger.error("❌Failed to authenticate with token")
            return None

        # Test the connection
        try:
            client.sys.read_health_status()
            logger.info("✅Successfully connected to Vault")
            return client
        except Exception as e:
            logger.error(f"❌Error connecting to Vault: {e}")
            return None

    except Exception as e:
        logger.error(f"❌Error creating Vault client: {e}")
        return None


def wait_for_secrets(client, path: str, max_retries=10, delay=2) -> Dict[str, Any]:
    """Wait for secrets to be available with exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point="secret"
            )
            if response and "data" in response and "data" in response["data"]:
                return response["data"]["data"]
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌Failed to read {path} after {max_retries} attempts: {e}")
            time.sleep(
                delay * (1.5**attempt)
            )  # Exponential backoff (it means that the delay will increase exponentially 
            	# with each attempt to read, because is much more likely that the server is busy
    return {}


def load_vault_secrets():
    logger.info("\n=== Loading secrets from Vault ===")

    client = get_client()
    if not client:
        logger.error("❌Failed to initialize Vault client")
        return

    paths = {
        "Database": "django/database",
        "OAuth": "django/oauth",
        "Email": "django/email",
        "Settings": "django/settings",
        "JWT": "django/jwt",
    }

    success = 0 # initialize success
    total = len(paths) # total number of paths

    # Intentar leer los secretos inmediatamente, sin espera adicional
    for name, path in paths.items():
        logger.info(f"⌛️Attempting to read {path}...")
        secrets = wait_for_secrets(client, path)

        if secrets:
            logger.info(f"✅ {name} - Found {len(secrets)} values")
            os.environ.update(secrets)
            _secrets_cache[path] = secrets
            success += 1
        else:
            logger.error(f"❌ {name}: Failed to read secrets")

    logger.info(f"\n{success}/{total} secrets loaded successfully✅")
    logger.info("=================================\n")

    if success < total:
        logger.warning("⚠️Some secrets missing, using .env as fallback")

        load_dotenv()
