from flask import jsonify, render_template, request

from services.base import BaseService

from . import manager
from .properties_util import FIELD_SCHEMA


class MinecraftService(BaseService):
    name = "Minecraft"
    url_prefix = "/minecraft"
    order = 6
    available = True

    def register_routes(self):
        bp = self.blueprint

        @bp.route("/")
        def index():
            return render_template(
                "minecraft.html",
                current_service_name=self.name,
                servers=manager.list_servers(),
            )

        @bp.route("/api/servers")
        def api_servers():
            return jsonify({"status": "success", "items": manager.list_servers()})

        @bp.route("/api/versions")
        def api_versions():
            try:
                return jsonify(
                    {"status": "success", "items": manager.available_versions()}
                )
            except (OSError, RuntimeError, ValueError) as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @bp.route("/api/servers", methods=["POST"])
        def api_create():
            data = request.get_json(silent=True) or {}
            kind = (data.get("type") or "vanilla").strip()
            if kind != "vanilla":
                return jsonify(
                    {"status": "error", "message": "Модифицированные сервера — скоро"}
                ), 400

            version = (data.get("version") or "").strip()
            name = (data.get("name") or "").strip() or None

            if not version:
                return jsonify({"status": "error", "message": "Не указана версия"}), 400

            try:
                meta = manager.create_vanilla_server(version, name=name)
            except (OSError, RuntimeError, ValueError) as e:
                return jsonify({"status": "error", "message": str(e)}), 500

            meta["running"] = False
            meta["status"] = "stopped"
            return jsonify({"status": "success", "server": meta})

        @bp.route("/api/servers/<server_id>", methods=["DELETE"])
        def api_delete(server_id):
            if not manager.get_server(server_id):
                return jsonify({"status": "error", "message": "Не найден"}), 404
            try:
                manager.delete_server(server_id)
            except (OSError, RuntimeError) as e:
                return jsonify({"status": "error", "message": str(e)}), 500
            return jsonify({"status": "success", "message": "Удалён"})

        @bp.route("/api/servers/<server_id>/start", methods=["POST"])
        def api_start(server_id):
            if not manager.get_server(server_id):
                return jsonify({"status": "error", "message": "Не найден"}), 404
            try:
                manager.start_server(server_id)
            except (OSError, RuntimeError, ValueError) as e:
                return jsonify({"status": "error", "message": str(e)}), 500
            return jsonify({"status": "success", "message": "Запущен"})

        @bp.route("/api/servers/<server_id>/stop", methods=["POST"])
        def api_stop(server_id):
            if not manager.get_server(server_id):
                return jsonify({"status": "error", "message": "Не найден"}), 404
            try:
                manager.stop_server(server_id)
            except (OSError, RuntimeError, ValueError) as e:
                return jsonify({"status": "error", "message": str(e)}), 500
            return jsonify({"status": "success", "message": "Остановлен"})

        @bp.route("/api/servers/<server_id>/settings")
        def api_settings_get(server_id):
            if not manager.get_server(server_id):
                return jsonify({"status": "error", "message": "Не найден"}), 404
            props = manager.get_properties(server_id)
            return jsonify(
                {
                    "status": "success",
                    "properties": props,
                    "schema": FIELD_SCHEMA,
                }
            )

        @bp.route("/api/servers/<server_id>/settings", methods=["POST"])
        def api_settings_set(server_id):
            if not manager.get_server(server_id):
                return jsonify({"status": "error", "message": "Не найден"}), 404
            data = request.get_json(silent=True) or {}
            updates = data.get("properties") or {}
            if not isinstance(updates, dict):
                return jsonify(
                    {"status": "error", "message": "Некорректные данные"}
                ), 400
            # bool → true/false строки для properties
            clean = {}
            for k, v in updates.items():
                if isinstance(v, bool):
                    clean[k] = "true" if v else "false"
                else:
                    clean[k] = str(v)
            try:
                props = manager.set_properties(server_id, clean)
            except (OSError, RuntimeError, ValueError) as e:
                return jsonify({"status": "error", "message": str(e)}), 500
            return jsonify({"status": "success", "properties": props})
