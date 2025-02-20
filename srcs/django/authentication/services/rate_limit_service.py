"""
Rate Limiting System with Redis
------------------------------

This system implements a rate limiting mechanism using Redis as a temporary storage solution.
Here's how it works:

1. Redis Connection:
   - Connects to a Redis container running on host 'redis' at port 6379
   - Used for storing temporary counters and block states

2. Configuration Parameters:
   - MAX_ATTEMPTS (5): Maximum number of tries within the time window
   - WINDOW_TIME (300): Time window of 5 minutes to track attempts
   - BLOCK_TIME (900): Block duration of 15 minutes after exceeding limits

3. How Rate Limiting Works:
   - Each user/IP is tracked using a unique key combining the action and identifier
   - When a user performs an action:
     a) First checks if they're currently blocked
     b) If not blocked, checks and increments their attempt counter
     c) If attempts exceed MAX_ATTEMPTS, user gets blocked for BLOCK_TIME
     d) After WINDOW_TIME, attempt counters automatically expire

4. Key Features:
   - Distributed rate limiting across multiple application instances
   - Automatic cleanup of expired entries (Redis TTL)
   - Separate tracking for different actions
   - Block/unblock functionality
   - Logging of all rate limit events

5. Usage Example:
   rate_limiter = RateLimitService()
   is_limited, time_remaining = rate_limiter.is_rate_limited("user123", "login")
   if is_limited:
       # Block access and show remaining time
   else:
       # Allow access

This implementation helps protect against brute force attacks and ensures
fair usage of the application's resources.
"""

import redis
import logging

logger = logging.getLogger(__name__)


class RateLimitService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host="redis", port=6379, db=0, decode_responses=True
        )
        # Limits of attempts by action type
        self.LIMITS = {
            'login': {'max_attempts': 5, 'window': 300, 'block': 900},        # 5 attempts / 5 min, block 15 min
            'manual_login': {'max_attempts': 3, 'window': 300, 'block': 900}, # 3 attempts / 5 min, block 15 min
            'password_reset': {'max_attempts': 3, 'window': 600, 'block': 1800},  # 3 attempts / 10 min, block 30 min
            'email_verification': {'max_attempts': 3, 'window': 1800, 'block': 3600},  # 3 attempts / 30 min, block 1h
            'two_factor': {'max_attempts': 3, 'window': 300, 'block': 900},  # 3 attempts / 5 min, block 15 min
            'token_refresh': {'max_attempts': 10, 'window': 600, 'block': 300},  # 10 attempts / 10 min, block 5 min
        }
        self.LIMITS.update({
            'email_change': {'max_attempts': 2, 'window': 3600, 'block': 7200},  # 2 attempts / hour, block 2h
            'profile_update': {'max_attempts': 5, 'window': 300, 'block': 900},  # 5 attempts / 5 min, block 15 min
            'email_send': {'max_attempts': 5, 'window': 3600, 'block': 7200},    # 5 attempts / hour, block 2h
        })
        # Token expiration times (in minutes)
        self.TOKEN_EXPIRY = {
            'auth': 15,             # Standard authentication token
            'password_reset': 30,    # Password reset token
            'email_verify': 1440,   # Email verification token (24h)
            'two_factor': 5,        # 2FA code
            'refresh': 10080        # Refresh token (7 days)
        }

    def get_limit_config(self, action: str) -> dict:
        """Get rate limit configuration for an action"""
        return self.LIMITS.get(action, self.LIMITS['login'])  # default to login limits

    def get_token_expiry(self, token_type: str) -> int:
        """Get token expiration time in minutes"""
        return self.TOKEN_EXPIRY.get(token_type, 15)  # default 15 minutes

    def _get_key(self, identifier: str, action: str) -> str:
        """ Get the key for the rate limit """
        return f"ratelimit:{action}:{identifier}"

    def is_rate_limited(self, identifier: str, action: str) -> tuple[bool, int]:
        """
        Check if the action is rate limited
        Returns: (is_limited, remaining_time)
        """
        limits = self.get_limit_config(action)
        key = self._get_key(identifier, action)
        
        try:
            # Check if blocked
            block_key = f"{key}:blocked"
            if self.redis_client.exists(block_key):
                ttl = int(self.redis_client.ttl(block_key))
                logger.warning(f"Access blocked for {identifier} on {action}. Remaining block time: {ttl}s")
                return True, ttl

            # Get current attempts
            attempts = self.redis_client.get(key)
            if not attempts:
                logger.info(f"New rate limit created for {identifier} on {action}")
                self.redis_client.setex(key, limits['window'], 1)
                return False, limits['max_attempts'] - 1

            attempts = int(attempts)
            if attempts >= limits['max_attempts']:
                logger.error(f"Rate limit exceeded for {identifier} on {action}. Blocking for {limits['block']}s")
                self.redis_client.setex(block_key, limits['block'], 1)
                self.redis_client.delete(key)
                return True, limits['block']

            # Increment attempts
            new_attempts = self.redis_client.incr(key)
            logger.info(f"Rate limit increment for {identifier} on {action}: {new_attempts}/{limits['max_attempts']}")
            return False, limits['max_attempts'] - new_attempts
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limit: {str(e)}")
            return False, limits['max_attempts']

    def reset_limit(self, identifier: str, action: str):
        """ Reset the rate limit for the identifier on the action """
        try:
            key = self._get_key(identifier, action)
            self.redis_client.delete(key)
            self.redis_client.delete(f"{key}:blocked")
            logger.info(f"Rate limit reset for {identifier} on {action}")
        except redis.RedisError as e:
            logger.error(f"Redis error when resetting rate limit: {str(e)}")
