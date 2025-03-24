import logging
import redis

# This service implements a rate limiting mechanism using Redis as a temporary storage backend.
# It is used to prevent brute force attacks and ensure fair usage of the application's resources.

# Redis Connection:
#    - Connects to a Redis container running on host 'redis' at port 6379
#    - Used for storing temporary counters and block states

# Configuration Macros:
#    - MAX_ATTEMPTS: Maximum number of tries allowed for an action in a time window
#    - WINDOW_TIME: Time window in seconds for trying an action
#    - BLOCK_TIME: Block time in seconds after exceeding the maximum attempts

# How Rate Limiting Works:
#    - Each user/IP is tracked using a unique key combining the action and identifier
#    - When a user performs an action:
#      	a) First checks if they're currently blocked
#      	b) If not blocked, checks and increments their attempt counter
#      	c) If attempts exceed MAX_ATTEMPTS, user gets blocked for BLOCK_TIME
#     	d) After WINDOW_TIME, attempt counters automatically expire

logger = logging.getLogger(__name__)

class RateLimitService:
    def __init__(self):
        self.redis_client = redis.Redis(	# Redis connection
             # db=0 -> default database, decode_responses=True -> decode bytes to strings
            host="redis", port=6379, db=0, decode_responses=True)
        
        # Authentication rate limits
        self.LIMITS = { 
            'login': {'max_attempts': 5, 'window': 300, 'block': 900},        # 5 attempts / 5 min, block 15 min
            'password_reset': {'max_attempts': 3, 'window': 600, 'block': 1800},  # 3 attempts / 10 min, block 30 min
            'email_verification': {'max_attempts': 3, 'window': 1800, 'block': 3600},  # 3 attempts / 30 min, block 1h
            'two_factor': {'max_attempts': 3, 'window': 300, 'block': 900},  # 3 attempts / 5 min, block 15 min
        }
        
        # Profile management rate limits
        self.LIMITS.update({
            'email_change': {'max_attempts': 2, 'window': 3600, 'block': 7200},  # 2 attempts / hour, block 2h
            'profile_update': {'max_attempts': 5, 'window': 300, 'block': 900},  # 5 attempts / 5 min, block 15 min
            'email_send': {'max_attempts': 5, 'window': 3600, 'block': 7200},    # 5 attempts / hour, block 2h
        })
        
        # QR code rate limits
        self.LIMITS.update({
            'qr_generation': {'max_attempts': 10, 'window': 3600, 'block': 900},  # 10 intentos/hora
            'qr_validation': {'max_attempts': 5, 'window': 300, 'block': 900},   # 5 intentos/5min
        })
        # Token expiration times (in minutes)
        self.TOKEN_EXPIRY = { # Token expiration times
            'auth': 15,             # Authentication token (15 min)
            'password_reset': 30,   # Password reset token (30 min)
            'email_verify': 1440,   # Email verification token (24h)
            'two_factor': 5,        # 2FA code (5 min)
        }

    def get_limit_config(self, action: str) -> dict:
        """Get rate limit configuration for an action"""
        return self.LIMITS.get(action, self.LIMITS['login'])  # default to login limits if not found

    def get_token_expiry(self, token_type: str) -> int:
        """Get token expiration time in minutes"""
        return self.TOKEN_EXPIRY.get(token_type, 15)  # default 15 minutes

    def _get_key(self, identifier: str, action: str) -> str:
        """ Get the key (identifier) for the rate limit """
        return f"ratelimit:{action}:{identifier}"

    def is_rate_limited(self, identifier: str, action: str) -> tuple[bool, int]:
        """ Checks if the action is rate limited for the identifier """
        limits = self.get_limit_config(action)
        key = self._get_key(identifier, action)
        
        try:
            # Check if user is blocked first
            block_key = f"{key}:blocked"
            if self.redis_client.exists(block_key):
                ttl = int(self.redis_client.ttl(block_key)) # Time to live
                logger.warning(f"Access blocked for {identifier} on {action}. Remaining block time: {ttl}s")
                return True, ttl

            # Get current attempts for the identifier
            attempts = self.redis_client.get(key)
            if not attempts:
                logger.info(f"New rate limit created for {identifier} on {action}")
                self.redis_client.setex(key, limits['window'], 1)
                return False, limits['max_attempts'] - 1

			# Check if attempts exceed the limit
            attempts = int(attempts)
            if attempts >= limits['max_attempts']:
                logger.error(f"Rate limit exceeded for {identifier} on {action}. Blocking for {limits['block']}s")
                self.redis_client.setex(block_key, limits['block'], 1)
                self.redis_client.delete(key)
                return True, limits['block']

            # Increment attempts if not blocked
            new_attempts = self.redis_client.incr(key)
            logger.info(f"Rate limit increment for {identifier} on {action}: {new_attempts}/{limits['max_attempts']}")
            return False, limits['max_attempts'] - new_attempts
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limit: {str(e)}")
            return False, limits['max_attempts']

    def reset_limit(self, identifier: str, action: str):
        """ Reset the rate limit for the identifier on the action (after successful action) """
        try:
            key = self._get_key(identifier, action)
            self.redis_client.delete(key)
            self.redis_client.delete(f"{key}:blocked")
            logger.info(f"Rate limit reset for {identifier} on {action}")
        except redis.RedisError as e:
            logger.error(f"Redis error when resetting rate limit: {str(e)}")
