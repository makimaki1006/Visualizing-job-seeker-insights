import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


def main() -> None:
    # load .env next to this script
    env = Path(__file__).resolve().parent / ".env"
    if env.exists():
        load_dotenv(env)

    url = os.getenv("TURSO_DATABASE_URL", "")
    token = os.getenv("TURSO_AUTH_TOKEN", "")
    if url.startswith("libsql://"):
        url = url.replace("libsql://", "https://")

    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT prefecture, municipality FROM job_seeker_data WHERE row_type='SUMMARY' LIMIT 5"
                },
            }
        ]
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = httpx.post(f"{url}/v2/pipeline", headers=headers, json=payload, timeout=15)
    print("status", resp.status_code)
    print(resp.text[:400])


if __name__ == "__main__":
    main()
