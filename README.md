# Project Configuration

## Environment Variables

1. Copy the `.env.example` file to `.env`:
```bash
cp srcs/env_example.md srcs/.env
```

2. Edit the `.env` file with your credentials and specific configurations.

3. Make sure to never commit the `.env` file to the repository.

For more details about each variable, check the comments in `.env.example`.

## API Keys and Sensitive Credentials

To configure the project, you'll need to create an `.env` file in the `srcs/` directory with the following credentials:

1. 42 OAuth Credentials:
   - Obtain from 42 developers portal
   - Configure FORTYTWO_CLIENT_ID and FORTYTWO_CLIENT_SECRET

2. SendGrid API Key:
   - Create a SendGrid account
   - Generate a new API key in the control panel

3. JWT Secret:
   - Generate a secure and unique secret key

4. Vault Token:
   - Configure according to HashiCorp Vault documentation

IMPORTANT: Never commit the .env file with real credentials to the repository.