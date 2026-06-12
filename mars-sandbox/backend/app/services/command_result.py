"""Command result cache service — shared by commands and nodes routers."""
import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Result cache with TTL: {request_id: (result_dict, timestamp)}
_result_cache: dict = {}
_RESULT_TTL = 300  # 5 minutes


def cache_result(request_id: str, result: dict):
    """Cache a command execution result with TTL cleanup."""
    now = time.time()
    _result_cache[request_id] = (result, now)
    # Cleanup expired entries
    expired = [k for k, (_, ts) in _result_cache.items() if now - ts > _RESULT_TTL]
    for k in expired:
        del _result_cache[k]
    logger.debug("Result cached: request_id=%s (cleaned %d expired)", request_id, len(expired))


async def wait_for_result(request_id: str, timeout: int) -> Optional[dict]:
    """Poll the result cache until a result is found or timeout.

    Args:
        request_id: The unique request ID to wait for.
        timeout: Maximum seconds to wait.

    Returns:
        The result dict, or None if timed out.
    """
    start_time = time.time()
    poll_interval = 0.1  # 100ms

    while time.time() - start_time < timeout:
        if request_id in _result_cache:
            result, _ = _result_cache.pop(request_id)
            return result
        await asyncio.sleep(poll_interval)

    return None
