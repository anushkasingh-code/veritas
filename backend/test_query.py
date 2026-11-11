"""Exercise the running analysis API and validate its completed response."""

import json
import time
import urllib.request


API_URL = "http://127.0.0.1:8000/api/v1/analyze"
QUERY = "Global Semiconductor Supply Chain"


def main() -> None:
    payload = json.dumps({"query": QUERY}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))
    elapsed = time.perf_counter() - started

    claims = result.get("claims", [])
    sources = result.get("sources", [])
    report = result.get("report_markdown") or ""
    errors = result.get("errors", [])
    valid_urls = [
        source.get("url", "")
        for source in sources
        if source.get("url", "").startswith(("http://", "https://"))
    ]
    verdicts = [claim.get("verdict") for claim in claims]

    assert result.get("status") == "completed", f"Unexpected status: {result.get('status')}"
    assert errors == [], f"Pipeline errors: {errors}"
    assert claims and all(verdicts), f"Claims missing verdicts: {verdicts}"
    assert valid_urls, "No sources with HTTP(S) URLs were returned"
    assert report and report.rstrip()[-1] in ".!?`)]}", "Report appears cut off mid-sentence"

    print(f"Status: {result['status']}")
    print(f"Claims: {len(claims)}; verdicts present: yes")
    print(f"Sources: {len(sources)}; HTTP(S) URLs: {len(valid_urls)}")
    print(f"Report characters: {len(report)}; final character: {report.rstrip()[-1]}")
    print(f"Errors: {errors}")
    print(f"End-to-end seconds: {elapsed:.2f}")


if __name__ == "__main__":
    main()
