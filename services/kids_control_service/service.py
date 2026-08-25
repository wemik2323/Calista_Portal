from flask import jsonify, render_template, request

from services.base import BaseService


class KidsControlService(BaseService):
    name = "Контроль детского ПК"
    url_prefix = "/pc"
    order = 4
    available = True

    # Пока храним в памяти. Потом вынесем в файл/БД.
    access_enabled = True
    last_session_text = "—"

    def register_routes(self):
        bp = self.blueprint

        @bp.route("/")
        def index():
            return render_template(
                "pc.html",
                current_service_name=self.name,
                access_enabled=self.access_enabled,
                last_session_text=self.last_session_text,
                online=False,  # позже сделаем реальную проверку
            )

        @bp.route("/api/status")
        def status():
            return jsonify(
                {
                    "online": False,
                    "access_enabled": self.access_enabled,
                    "last_session_text": self.last_session_text,
                }
            )

        @bp.route("/api/access", methods=["POST"])
        def set_access():
            data = request.get_json(silent=True) or {}
            enabled = bool(data.get("enabled"))
            self.access_enabled = enabled

            # TODO: если enabled=False -> сразу lock по SSH
            return jsonify(
                {
                    "status": "success",
                    "access_enabled": self.access_enabled,
                    "message": "Доступ включён" if enabled else "Доступ выключен",
                }
            )

        @bp.route("/api/power", methods=["POST"])
        def power():
            data = request.get_json(silent=True) or {}
            action = (data.get("action") or "").strip()

            if action not in {"on", "off", "reboot", "lock"}:
                return jsonify({"status": "error", "message": "Неизвестная команда"}), 400

            # TODO: реальные WOL/SSH команды
            labels = {
                "on": "Включение (WOL) — заглушка",
                "off": "Выключение — заглушка",
                "reboot": "Перезапуск — заглушка",
                "lock": "Блокировка экрана — заглушка",
            }
            return jsonify({"status": "success", "message": labels[action]})

        @bp.route("/api/processes")
        def processes():
            # TODO: tasklist по SSH
            demo = [
                {"name": "chrome.exe", "pid": 1234, "memory_mb": 120},
                {"name": "steam.exe", "pid": 2345, "memory_mb": 80},
                {"name": "javaw.exe", "pid": 3456, "memory_mb": 900},
            ]
            return jsonify({"status": "success", "processes": demo})

        @bp.route("/api/kill", methods=["POST"])
        def kill():
            data = request.get_json(silent=True) or {}
            pid = data.get("pid")
            name = data.get("name")

            if not pid and not name:
                return jsonify({"status": "error", "message": "Не указан процесс"}), 400

            # TODO: taskkill по SSH
            target = name or f"PID {pid}"
            return jsonify(
                {
                    "status": "success",
                    "message": f"Заглушка: убит процесс {target}",
                }
            )

        @bp.route("/api/notify", methods=["POST"])
        def notify():
            data = request.get_json(silent=True) or {}
            text = (data.get("text") or "").strip()

            if not text:
                return jsonify({"status": "error", "message": "Пустое сообщение"}), 400

            # TODO: msg/уведомление по SSH
            return jsonify(
                {
                    "status": "success",
                    "message": f"Заглушка: отправлено «{text}»",
                }
            )
