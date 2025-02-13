import hvac
import os
import time
from typing import Dict, Any


class VaultClient:
    def __init__(self):
        token_file = "/tmp/ssl/django_token"
        retries = 0
        max_retries = 5

        while retries < max_retries:
            try:
                with open(token_file, "r") as f:
                    token = f.read().strip()
                if token:
                    break
            except Exception as e:
                print(
                    f"Attempt {retries + 1}/{max_retries}: Error reading Vault token: {e}"
                )
                retries += 1
                time.sleep(2)
                token = None

        self.client = hvac.Client(url="https://waf:8200", verify=False, token=token)

    def is_vault_sealed(self) -> bool:
        try:
            response = requests.get("https://waf:8200/v1/sys/seal-status", verify=False)
            return response.json().get("sealed", True)
        except Exception:
            return True

    def get_secrets(self, path: str) -> Dict[str, Any]:
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
                return response["data"]["data"]
            except Exception as e:
                print(
                    f"Attempt {retries + 1}/{max_retries}: Error fetching secrets from Vault: {e}"
                )
                retries += 1
                time.sleep(2)

        return {}


def load_vault_secrets():
    client = VaultClient()

    # Cargar secretos de diferentes rutas
    django_db = client.get_secrets("django/database")
    django_oauth = client.get_secrets("django/oauth")
    django_email = client.get_secrets("django/email")
    django_settings = client.get_secrets("django/settings")
    django_jwt = client.get_secrets("django/jwt")

    # Actualizar variables de entorno con los secretos
    os.environ.update(django_db)
    os.environ.update(django_oauth)
    os.environ.update(django_email)
    os.environ.update(django_settings)
    os.environ.update(django_jwt)
