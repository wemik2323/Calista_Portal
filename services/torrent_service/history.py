import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.Lock()
_HISTORY_FILE = Path(__file__).resolve().parents[2] / "data" / "torrent_history.json"


def _ensure_file() -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _HISTORY_FILE.exists():
        _HISTORY_FILE.write_text("[]", encoding="utf-8")


def add_entry(
    *,
    who: str,
    device: str,
    title: str,
    size_bytes: int | None,
    magnet: str,
    info_hash: str
) -> dict:
    _ensure_file()
    entry = {
        "who": who,
        "device": device,
        "title": title,
        "size_bytes": size_bytes,
        "size_human": _human_size(size_bytes),
        "magnet": magnet[:120] + ("…" if len(magnet) > 120 else ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hash": (info_hash or "").lower() or None,
    }
    with _LOCK:
        data = json.loads(_HISTORY_FILE.read_text(encoding="utf-8") or "[]")
        data.insert(0, entry)
        data = data[:200]  # последние 200
        _HISTORY_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return entry


def list_entries(limit: int = 50) -> list[dict]:
    _ensure_file()
    with _LOCK:
        data = json.loads(_HISTORY_FILE.read_text(encoding="utf-8") or "[]")
    return data[:limit]


def _human_size(n: int | None) -> str:
    if not n or n <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f} {u}" if u != "B" else f"{int(x)} B"
        x /= 1024
    return "—"
