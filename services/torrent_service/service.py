from flask import jsonify, render_template, request

from services.base import BaseService


class TorrentService(BaseService):
    name = "Торренты"
    url_prefix = "/torrents"
    order = 3
    available = True

    def register_routes(self):
        bp = self.blueprint

        @bp.route("/")
        def index():
            return render_template(
                "torrents.html",
                current_service_name=self.name,
            )

        @bp.route("/api/search")
        def search():
            query = request.args.get("q", "").strip()
            if not query:
                return jsonify({"status": "error", "message": "Пустой запрос"}), 400

            # Пока заглушка. Потом подключим Rutracker.
            results = [
                {
                    "id": "1",
                    "title": f"Пример результата для: {query}",
                    "size": "1.2 GB",
                    "seeds": 10,
                    "peers": 2,
                }
            ]
            return jsonify({"status": "success", "results": results})

        @bp.route("/api/download", methods=["POST"])
        def download():
            data = request.get_json(silent=True) or {}
            torrent_id = data.get("id")
            title = data.get("title", "unknown")

            if not torrent_id:
                return jsonify({"status": "error", "message": "Не выбран торрент"}), 400

            # Пока заглушка
            return jsonify({
                "status": "success",
                "message": f"Заглушка: скачивание «{title}» будет здесь",
            })