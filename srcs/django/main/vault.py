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
_secrets_loaded = False  # Flag to track if secrets have been loaded


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

    def is_vault_sealed(self) -> bool:
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
                if self.is_vault_sealed():
                    print("Vault is sealed, waiting for unseal...")
                    time.sleep(2)
                    retries += 1
                    continue

                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point="secret"
                )
                secrets = response["data"]["data"]
                _secrets_cache[path] = secrets  # Save secrets in cache
                return secrets
            except Exception as e:
                if (
                    retries == max_retries - 1
                ):  # Show error only on last retry to avoid spamming
                    print(f"Error fetching secrets from Vault: {e}")
                retries += 1
                time.sleep(2)
        return {}


def get_client():
    try:
        token_file = "/tmp/ssl/django_token"
        with open(token_file, "r") as f:
            token = f.read().strip()
            print(f"Using token: {token}")  # Debug line

        client = hvac.Client(url="https://waf:8200", token=token, verify=False)

        # Verify authentication
        if client.is_authenticated():
            print("Successfully authenticated with Vault")
            try:
                # Test read access
                client.secrets.kv.v2.read_secret_version(
                    path="django/database", mount_point="secret"
                )
                print("Successfully read test secret")
            except Exception as e:
                print(f"Failed to read test secret: {e}")
        else:
            print("Failed to authenticate with Vault")
            return None

        return client
    except Exception as e:
        print(f"Error initializing Vault client: {e}")
        return None


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

    for name, path in paths.items():
        try:
            print(f"Attempting to read {path}...")  # Debug line
            response = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point="secret"
            )
            secrets = response["data"]["data"]
            print(f"✓ {name} - Found {len(secrets)} values")
            os.environ.update(secrets)
            success += 1
        except Exception as e:
            print(f"✗ {name}: {str(e)}")
            if hasattr(e, "response") and e.response:
                print(f"Response details: {e.response.text}")

    print(f"\n{success}/{total} secrets loaded successfully")
    print("=================================\n")

    if success < total:
        print("Warning: Some secrets missing, using .env as fallback")
        from dotenv import load_dotenv

        load_dotenv()
