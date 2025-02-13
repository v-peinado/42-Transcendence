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

    def is_vault_sealed(self) -> bool:
        try:
            response = requests.get("https://waf:8200/v1/sys/seal-status", verify=False)
            return response.json().get("sealed", True)
        except Exception:
            return True

    def get_secrets(self, path: str) -> Dict[str, Any]:
        # Verify if secrets are already in cache
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


def load_vault_secrets():
    if _secrets_cache:  # If secrets are already loaded
        for secrets in _secrets_cache.values():
            os.environ.update(secrets)
        return

    client = VaultClient()
    secrets = {
        "Database": client.get_secrets("django/database"),
        "OAuth": client.get_secrets("django/oauth"),
        "Email": client.get_secrets("django/email"),
        "Settings": client.get_secrets("django/settings"),
        "JWT": client.get_secrets("django/jwt"),
    }

    print("\n=== Loading secrets from Vault ===")
    for name, data in secrets.items():
        if data:
            print(f"✓ {name}")
            os.environ.update(data)
        else:
            print(f"✗ {name}")
    print("=================================\n")
