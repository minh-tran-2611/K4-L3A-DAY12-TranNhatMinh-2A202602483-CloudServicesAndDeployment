"""Verify the limiter admits exactly its quota under concurrent requests."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fakeredis
from fastapi import HTTPException
from app.rate_limiter import RateLimiter


def main():
    client = fakeredis.FakeRedis(decode_responses=True)
    limiter = RateLimiter(client, 10)

    def attempt(_):
        try:
            limiter.check("concurrent-user", now=1000.0)
            return 200
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=20) as workers:
        codes = list(workers.map(attempt, range(100)))
    assert codes.count(200) == 10, codes
    assert codes.count(429) == 90, codes
    assert limiter.hit_count("concurrent-user", now=1000.0) == 10
    print("100 concurrent attempts: 10 admitted, 90 rate limited; 10 unique entries.")


if __name__ == "__main__":
    main()
