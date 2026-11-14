"""Update cached Opinet prices in docs/data/stations.json via GitHub Actions or CLI."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import urllib.request

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = ROOT / "docs" / "data" / "stations.json"

VALID_FUELS = {
    "B027": "휘발유",
    "D047": "경유",
    "B034": "고급휘발유",
    "K015": "LPG",
}


def fetch_around_all(api_key: str, x: float, y: float, prodcd: str, radius: int = 5000) -> list[dict]:
    """Query Opinet aroundAll.do for a cover circle center."""
    url = (
        "https://www.opinet.co.kr/api/aroundAll.do"
        f"?out=json&code={api_key}&x={x}&y={y}&radius={radius}&prodcd={prodcd}&sort=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    result = payload.get("RESULT")
    if not isinstance(result, dict) or "OIL" not in result:
        raise RuntimeError(f"Opinet API error for {prodcd}: {payload}")
    return result["OIL"]


def refresh_dataset(data_path: Path, api_key: str, fuels: list[str]) -> dict:
    """Refresh specified fuel types in stations.json using minimal cover points."""
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("OPINET_API_KEY is empty.")

    with data_path.open("r", encoding="utf-8") as f:
        master = json.load(f)

    master.setdefault("last_refresh", {})
    now_dt = datetime.now(KST)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    now_kst = f"{now_str} KST"
    dt_str = now_dt.strftime("%Y%m%d")
    tm_str = now_dt.strftime("%H%M%S")

    total_calls = 0
    per_fuel_updated: dict[str, int] = {}

    for prodcd in fuels:
        if prodcd not in VALID_FUELS:
            raise ValueError(f"Unsupported fuel code: {prodcd}")
        cover_key = "lpg" if prodcd == "K015" else "gas_diesel"
        centers = master["cover_points"][cover_key]

        latest_by_uid: dict[str, dict] = {}
        for cx, cy in centers:
            rows = fetch_around_all(api_key, cx, cy, prodcd, radius=5000)
            total_calls += 1
            for item in rows:
                uid = item.get("UNI_ID")
                price = item.get("PRICE")
                if uid and isinstance(price, (int, float)) and price > 0:
                    latest_by_uid[uid] = item

        updated = 0
        for station in master["stations"]:
            uid = station["uni_id"]
            if uid in latest_by_uid:
                item = latest_by_uid[uid]
                station.setdefault("prices", {})[prodcd] = {
                    "price": int(item["PRICE"]),
                    "dt": dt_str,
                    "tm": tm_str,
                    "refreshed_at": now_str,
                }
                if item.get("POLL_DIV_CD"):
                    station["brand"] = item["POLL_DIV_CD"]
                updated += 1

        master["last_refresh"][prodcd] = now_str
        per_fuel_updated[prodcd] = updated

    meta = master.setdefault("meta", {})
    meta["last_updated_kst"] = now_kst
    master["generated_at"] = now_dt.isoformat(timespec="seconds")

    with data_path.open("w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    return {
        "total_calls": total_calls,
        "updated": per_fuel_updated,
        "last_updated_kst": now_kst,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh cached Daejeon cashback gas prices.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path to stations.json")
    parser.add_argument(
        "--fuels",
        default="B027,D047,B034,K015",
        help="Comma-separated fuel codes to update (default: B027,D047,B034,K015)",
    )
    parser.add_argument("--api-key", default=os.environ.get("OPINET_API_KEY", ""), help="Opinet API Key")
    args = parser.parse_args()

    fuels = [x.strip().upper() for x in args.fuels.split(",") if x.strip()]
    summary = refresh_dataset(args.data, args.api_key, fuels)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
