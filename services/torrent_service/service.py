from flask import jsonify, render_template, request

from services.base import BaseService

from .history import add_entry, list_entries
from .qbittorrent_client import (
    QBittorrentClient,
    QBittorrentClientError,
    _hash_from_magnet,
)


class TorrentService(BaseService):
    name = "Торренты"
    url_prefix = "/torrents"
    order = 5
    available = True

    def __init__(self):
        self.qbit = QBittorrentClient()
        super().__init__()

    def register_routes(self):
        bp = self.blueprint

        @bp.route("/")
        def index():
            return render_template(
                "torrents.html",
                current_service_name=self.name,
                history=list_entries(50),
            )

        @bp.route("/api/history")
        def api_history():
            return jsonify({"status": "success", "items": list_entries(50)})

        @bp.route("/api/add", methods=["POST"])
        def api_add():
            data = request.get_json(silent=True) or {}
            magnet = (data.get("magnet") or "").strip()

            if not magnet.startswith("magnet:?"):
                return jsonify(
                    {"status": "error", "message": "Нужна корректная magnet-ссылка"}
                ), 400

            who = _who(request, data)
            device = _device(request, data)

            try:
                self.qbit.add_magnet(magnet)
            except QBittorrentClientError as e:
                return jsonify({"status": "error", "message": str(e)}), 500

            title = "Без названия"
            size_bytes = None
            info_hash = None
            info = self.qbit.find_torrent_by_magnet(magnet, wait_sec=4.0)
            if info:
                title = info.get("name") or title
                size_bytes = info.get("total_size") or info.get("size")
                info_hash = info.get("hash")
            if not info_hash:
                info_hash = _hash_from_magnet(magnet)

            entry = add_entry(
                who=who,
                device=device,
                title=title,
                size_bytes=size_bytes,
                magnet=magnet,
                info_hash=info_hash,
            )
            return jsonify(
                {
                    "status": "success",
                    "message": "Торрент добавлен",
                    "entry": entry,
                }
            )

        @bp.route("/api/torrents")
        def api_torrents():
            try:
                raw = self.qbit.list_torrents()
                items = [_format_torrent(t) for t in raw]
                return jsonify({"status": "success", "items": items})
            except QBittorrentClientError as e:
                return jsonify({"status": "error", "message": str(e)}), 500


def _who(req, data=None) -> str:
    data = data or {}
    custom = (data.get("device_name") or "").strip()
    if custom:
        return custom[:64]

    auth = req.authorization
    if auth and auth.username:
        return auth.username

    for h in ("X-Remote-User", "X-Forwarded-User", "Remote-User"):
        v = req.headers.get(h)
        if v:
            return v

    return req.headers.get("X-Real-IP") or req.remote_addr or "anonymous"


def _device(req, data=None) -> str:
    data = data or {}
    custom = (data.get("device_name") or "").strip()
    if custom:
        return custom[:64]

    ua = (req.headers.get("User-Agent") or "").lower()
    if "android" in ua:
        return "Android"
    if "iphone" in ua or "ipad" in ua:
        return "iOS"
    if "windows" in ua:
        return "Windows"
    if "mac os" in ua or "macintosh" in ua:
        return "macOS"
    if "linux" in ua:
        return "Linux"
    return "Unknown"


_STATE_MAP = {
    "downloading": "Скачивается",
    "stalledDL": "Скачивается (нет пиров)",
    "metaDL": "Метаданные",
    "forcedDL": "Скачивается",
    "queuedDL": "В очереди",
    "pausedDL": "Пауза",
    "uploading": "Раздаётся",
    "stalledUP": "Раздаётся",
    "forcedUP": "Раздаётся",
    "queuedUP": "Очередь раздачи",
    "pausedUP": "Пауза (раздача)",
    "checkingDL": "Проверка",
    "checkingUP": "Проверка",
    "checkingResumeData": "Проверка",
    "moving": "Перемещение",
    "error": "Ошибка",
    "missingFiles": "Нет файлов",
    "unknown": "Неизвестно",
}


def _format_torrent(t: dict) -> dict:
    progress = float(t.get("progress") or 0) * 100
    state = t.get("state") or "unknown"
    # «скачан» — progress ~100% и уже не качает
    if progress >= 99.9 and state in {
        "uploading",
        "stalledUP",
        "forcedUP",
        "pausedUP",
        "queuedUP",
    }:
        status = "Скачан"
    else:
        status = _STATE_MAP.get(state, state)

    return {
        "hash": t.get("hash"),
        "title": t.get("name") or "—",
        "size_bytes": t.get("size") or t.get("total_size") or 0,
        "progress": round(progress, 1),
        "status": status,
        "state": state,
        "dlspeed": t.get("dlspeed") or 0,
        "eta": t.get("eta") or 0,
    }
