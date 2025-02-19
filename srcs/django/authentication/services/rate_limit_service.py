import redis
import logging

logger = logging.getLogger(__name__)


class RateLimitService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host="redis", port=6379, db=0, decode_responses=True
        )
        self.MAX_ATTEMPTS = 5
        self.WINDOW_TIME = 300  # 5 minutes in seconds
        self.BLOCK_TIME = 900  # 15 minutes in seconds

    def _get_key(self, identifier: str, action: str) -> str:
        return f"ratelimit:{action}:{identifier}"

    def is_rate_limited(self, identifier: str, action: str) -> tuple[bool, int]:
        """
        Check if the action is rate limited
        Returns: (is_limited, remaining_time)
        """
        key = self._get_key(identifier, action)

        # Check if blocked
        block_key = f"{key}:blocked"
        if self.redis_client.exists(block_key):
            return True, int(self.redis_client.ttl(block_key))

        # Get current attempts
        attempts = self.redis_client.get(key)
        if not attempts:
            self.redis_client.setex(key, self.WINDOW_TIME, 1)
            return False, self.MAX_ATTEMPTS - 1

        attempts = int(attempts)
        if attempts >= self.MAX_ATTEMPTS:
            # Block the user
            self.redis_client.setex(block_key, self.BLOCK_TIME, 1)
            self.redis_client.delete(key)
            logger.warning(f"Rate limit exceeded for {identifier} on {action}")
            return True, self.BLOCK_TIME

        # Increment attempts
        self.redis_client.incr(key)
        return False, self.MAX_ATTEMPTS - attempts - 1

    def reset_limit(self, identifier: str, action: str):
        """Reset rate limit for successful actions"""
        key = self._get_key(identifier, action)
        self.redis_client.delete(key)
        self.redis_client.delete(f"{key}:blocked")
