"""Prepare clean mobile static JSON dataset from parent cashback_stations_master.json."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
SRC_MASTER = ROOT.parent / "cashback_stations_master.json"
DST_JSON = ROOT / "docs" / "data" / "stations.json"


def build_mobile_dataset(src_path: Path = SRC_MASTER, dst_path: Path = DST_JSON) -> dict:
    with src_path.open("r", encoding="utf-8") as f:
        master = json.load(f)

    master.setdefault("last_refresh", {})
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    master["meta"] = {
        "app_name": "대전 캐시백 주유 지도",
        "version": "1.0.0",
        "last_updated_kst": now_kst,
        "auto_refresh_schedule": "매일 약 2~3시간 간격 자동 갱신 (06:15~21:30 KST)",
        "source": "한국석유공사 오피넷(Opinet) Open API · 대전 온통대전(대전사랑카드) 캐시백 가맹점 기준",
    }

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with dst_path.open("w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)
    return master


if __name__ == "__main__":
    data = build_mobile_dataset()
    print(f"Built {DST_JSON} ({len(data['stations'])} stations)")
