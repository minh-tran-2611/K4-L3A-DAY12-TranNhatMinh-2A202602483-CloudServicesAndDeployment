"""Exercise the running local stack without printing credentials."""
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

import httpx
from dotenv import dotenv_values
import redis

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = dotenv_values(ROOT / ".env")
    user = "verify-" + uuid.uuid4().hex[:12]
    headers = {"X-API-Key": env["AGENT_API_KEY"], "X-User-Id": user}
    report = {"timestamp": datetime.now(timezone.utc).isoformat()}
    with httpx.Client(base_url="http://localhost:8000", timeout=10) as client:
        for endpoint in ("health", "ready"):
            r = client.get("/" + endpoint)
            assert r.status_code == 200, r.text
            report[endpoint] = {"status_code": r.status_code, "body": r.json()}
        r = client.post("/ask", json={"question": "Hello"})
        assert r.status_code == 401
        report["missing_key"] = r.status_code
        codes, history = [], []
        for _ in range(15):
            r = client.post("/ask", headers=headers, json={"question": "Docker la gi?"})
            codes.append(r.status_code)
            if r.status_code == 200:
                history.append(r.json()["history_length"])
        assert codes == [200] * 10 + [429] * 5, codes
        assert history == list(range(0, 20, 2)), history
        report["rate_limit_codes"] = codes
        report["history_lengths"] = history
        db = redis.from_url(env["REDIS_URL"], decode_responses=True)
        budget_user = user + "-budget"
        key = f"cost:{budget_user}:{datetime.now(timezone.utc):%Y-%m}"
        db.set(key, "999", ex=120)
        r = client.post("/ask", headers={**headers, "X-User-Id": budget_user},
                        json={"question": "Budget test"})
        assert r.status_code == 402, r.text
        report["budget_exceeded"] = r.status_code
    output = json.dumps(report, ensure_ascii=False, indent=2)
    (ROOT / "evidence" / "local-verification.json").write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
