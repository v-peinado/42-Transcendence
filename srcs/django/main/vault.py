import hvac
import requests
import os
import time
import warnings
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, Any

# Disable SSL warnings for Vault connection (self-signed certificate)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

_secrets_cache = {}  # Cache for secrets


class VaultClient:
    def __init__(self):
        token_file = "/tmp/ssl/django_token"
        try:
            with open(token_file, "r") as f:
                token = f.read().strip()
        except Exception as e:
            print(f"Error reading Vault token: {e}")
            token = None

        # Config client with token
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.client = hvac.Client(url="https://waf:8200", verify=False, token=token)

    def _is_vault_sealed(self) -> bool:  # Private method
        try:
            response = requests.get("https://waf:8200/v1/sys/seal-status", verify=False)
            return response.json().get("sealed", True)
        except Exception:
            return True

    def get_secrets(self, path: str) -> Dict[str, Any]:
        # Check cache first
        if path in _secrets_cache:
            return _secrets_cache[path]

        retries = 0
        max_retries = 5

        while retries < max_retries:
            try:
                if self._is_vault_sealed():  # Using private method
                    print("Vault is sealed, waiting for unseal...")
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
                    print(f"Error fetching secrets from Vault: {e}")
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
                        print(f"Found Vault token after {attempt + 1} attempts")
                        return token
            print(f"Waiting for token file... ({attempt + 1}/{max_attempts})")
            time.sleep(delay)
        except Exception as e:
            print(f"Error reading token: {e}")
            time.sleep(delay)
    return None


def get_client():
    token = wait_for_token()
    if not token:
        print("Failed to get Vault token")
        return None

    try:
        client = hvac.Client(url="https://waf:8200", token=token, verify=False)

        if not client.is_authenticated():
            print("Failed to authenticate with token")
            return None

        # Test the connection
        try:
            client.sys.read_health_status()
            print("Successfully connected to Vault")
            return client
        except Exception as e:
            print(f"Error connecting to Vault: {e}")
            return None

    except Exception as e:
        print(f"Error creating Vault client: {e}")
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
                print(f"Failed to read {path} after {max_retries} attempts: {e}")
            time.sleep(
                delay * (1.5**attempt)
            )  # Exponential backoff with smaller factor
    return {}


def load_vault_secrets():
    print("\n=== Loading secrets from Vault ===")

    client = get_client()
    if not client:
        print("✗ Failed to initialize Vault client")
        print("=================================\n")
        return

    paths = {
        "Database": "django/database",
        "OAuth": "django/oauth",
        "Email": "django/email",
        "Settings": "django/settings",
        "JWT": "django/jwt",
    }

    success = 0
    total = len(paths)

    # Wait for vault to be fully ready
    time.sleep(5)  # Give vault time to initialize

    for name, path in paths.items():
        print(f"Attempting to read {path}...")
        secrets = wait_for_secrets(client, path)

        if secrets:
            print(f"✓ {name} - Found {len(secrets)} values")
            os.environ.update(secrets)
            _secrets_cache[path] = secrets
            success += 1
        else:
            print(f"✗ {name}: Failed to read secrets")

    print(f"\n{success}/{total} secrets loaded successfully")
    print("=================================\n")

    if success < total:
        print("Warning: Some secrets missing, using .env as fallback")
        from dotenv import load_dotenv

        load_dotenv()
