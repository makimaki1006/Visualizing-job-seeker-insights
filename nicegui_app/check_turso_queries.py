import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


def run_query(url: str, token: str, sql: str) -> str:
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}]}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = httpx.post(f"{url}/v2/pipeline", headers=headers, json=payload, timeout=20)
    return f"status {resp.status_code}\n{resp.text[:800]}"


def main() -> None:
    env = Path(__file__).resolve().parent / ".env"
    if env.exists():
        load_dotenv(env)

    url = os.getenv("TURSO_DATABASE_URL", "")
    token = os.getenv("TURSO_AUTH_TOKEN", "")
    if not url or not token:
        print("[ERROR] URL or TOKEN missing.")
        return
    if url.startswith("libsql://"):
        url = url.replace("libsql://", "https://")

    queries = {
        "total_rows": "SELECT COUNT(*) as cnt FROM job_seeker_data WHERE row_type='SUMMARY'",
        "distinct_pref": "SELECT COUNT(DISTINCT prefecture) as cnt FROM job_seeker_data WHERE row_type='SUMMARY'",
        "pref_counts": "SELECT prefecture, COUNT(*) as rows FROM job_seeker_data WHERE row_type='SUMMARY' GROUP BY prefecture ORDER BY rows DESC LIMIT 10",
        "muni_sample_tokyo": "SELECT prefecture, municipality FROM job_seeker_data WHERE row_type='SUMMARY' AND prefecture='東京都' LIMIT 10",
    }

    for name, sql in queries.items():
        print(f"\n## {name}")
        try:
            print(run_query(url, token, sql))
        except Exception as exc:
            print(f"error: {exc}")


if __name__ == "__main__":
    main()
