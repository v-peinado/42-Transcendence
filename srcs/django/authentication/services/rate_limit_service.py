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
                self.redis_client.setex(key, self.WINDOW_TIME, 1)
                return False, self.MAX_ATTEMPTS - 1

            attempts = int(attempts)
            if attempts >= self.MAX_ATTEMPTS:
                logger.error(f"Rate limit exceeded for {identifier} on {action}. Blocking for {self.BLOCK_TIME}s")
                self.redis_client.setex(block_key, self.BLOCK_TIME, 1)
                self.redis_client.delete(key)
                return True, self.BLOCK_TIME

            # Increment attempts
            new_attempts = self.redis_client.incr(key)
            logger.info(f"Rate limit increment for {identifier} on {action}: {new_attempts}/{self.MAX_ATTEMPTS}")
            return False, self.MAX_ATTEMPTS - new_attempts
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limit: {str(e)}")
            return False, self.MAX_ATTEMPTS

    def reset_limit(self, identifier: str, action: str):
        """ Reset the rate limit for the identifier on the action """
        try:
            key = self._get_key(identifier, action)
            self.redis_client.delete(key)
            self.redis_client.delete(f"{key}:blocked")
            logger.info(f"Rate limit reset for {identifier} on {action}")
        except redis.RedisError as e:
            logger.error(f"Redis error when resetting rate limit: {str(e)}")
