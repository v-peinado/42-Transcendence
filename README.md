# Pong Game Platform

A modern web-based implementation of the classic Pong game built with Django and vanilla JavaScript. This comprehensive gaming platform features real-time multiplayer capabilities, AI opponents, tournament system, and a complete social gaming experience.

## Features

- **Classic Pong Gameplay**: Traditional paddle-and-ball mechanics with modern responsive design
- **Multiple Game Modes**: 
  - Online multiplayer with matchmaking system
  - Local games against AI opponents
  - Private matches via chat invitations
- **Tournament System**: Organized competitive brackets with multiple players
- **Real-time Chat System**: Integrated messaging with game invitation functionality
- **User Authentication**: Secure login system with 42 OAuth integration
- **Data Protection**: GDPR-compliant user data handling and privacy controls
- **Containerized Architecture**: Full Docker deployment with microservices
- **Security Features**: WAF (Web Application Firewall) protection and secure communications
- **Responsive Design**: Optimized for desktop and mobile gaming

## Tech Stack

- **Backend**: Django (Python)
- **Frontend**: Vanilla JavaScript, HTML5 Canvas
- **Database**: PostgreSQL
- **Infrastructure**: Docker containers
- **Security**: WAF, JWT authentication, data encryption
- **Real-time**: WebSocket connections for chat and gaming

---

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