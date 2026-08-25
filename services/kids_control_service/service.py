from flask import jsonify, render_template, request

from services.base import BaseService

from .windows_ssh import WindowsSSHClient


class KidsControlService(BaseService):
    name = "Контроль детского ПК"
    url_prefix = "/pc"
    order = 4
    available = True

    # Пока храним в памяти. Потом вынесем в файл/БД.
    access_enabled = True
    last_session_text = "—"

    def __init__(self):
        self.ssh = WindowsSSHClient()
        super().__init__()

    def register_routes(self):
        bp = self.blueprint

        @bp.route("/")
        def index():
            return render_template(
                "pc.html",
                current_service_name=self.name,
                access_enabled=self.access_enabled,
                last_session_text=self.last_session_text,
                online=self.ssh.is_online(),
            )

        @bp.route("/api/status")
        def status():
            return jsonify(
                {
                    "online": self.ssh.is_online(),
                    "access_enabled": self.access_enabled,
                    "last_session_text": self.last_session_text,
                }
            )

        @bp.route("/api/access", methods=["POST"])
        def set_access():
            data = request.get_json(silent=True) or {}
            enabled = bool(data.get("enabled"))
            self.access_enabled = enabled

            if not enabled:
                self.ssh.lock()

            return jsonify(
                {
                    "status": "success",
                    "access_enabled": self.access_enabled,
                    "message": "Доступ включён"
                    if enabled
                    else "Доступ выключен, экран заблокирован",
                }
            )

        @bp.route("/api/power", methods=["POST"])
        def power():
            data = request.get_json(silent=True) or {}
            action = (data.get("action") or "").strip()

            if action == "on":
                return jsonify({"status": "error", "message": "WOL недоступен"}), 400

            actions = {
                "off": self.ssh.shutdown,
                "reboot": self.ssh.reboot,
                "lock": self.ssh.lock,
            }
            if action not in actions:
                return jsonify(
                    {"status": "error", "message": "Неизвестная команда"}
                ), 400

            result = actions[action]()
            if not result.ok:
                return jsonify(
                    {"status": "error", "message": result.error or "Ошибка"}
                ), 500

            return jsonify(
                {"status": "success", "message": f"Команда {action} выполнена"}
            )

        @bp.route("/api/processes")
        def processes():
            result = self.ssh.list_processes()
            if not result.ok:
                return jsonify(
                    {"status": "error", "message": result.error or "Нет доступа к ПК"}
                ), 500

            items = []
            for line in result.output.splitlines():
                parts = line.split("|")
                if len(parts) != 3:
                    continue
                name, pid, mem = parts
                items.append(
                    {
                        "name": name if name.endswith(".exe") else name + ".exe",
                        "pid": int(pid),
                        "memory_mb": int(mem),
                    }
                )
            return jsonify({"status": "success", "processes": items})

        @bp.route("/api/notify", methods=["POST"])
        def notify():
            data = request.get_json(silent=True) or {}
            text = (data.get("text") or "").strip()
            if not text:
                return jsonify({"status": "error", "message": "Пустое сообщение"}), 400

            result = self.ssh.notify(text)
            if not result.ok:
                return jsonify(
                    {
                        "status": "error",
                        "message": result.error or "Не удалось отправить",
                    }
                ), 500

            return jsonify({"status": "success", "message": "Сообщение отправлено"})

        @bp.route("/api/kill", methods=["POST"])
        def kill():
            data = request.get_json(silent=True) or {}
            pid = data.get("pid")
            name = data.get("name")

            if pid:
                result = self.ssh.kill_pid(int(pid))
            elif name:
                result = self.ssh.kill_name(str(name))
            else:
                return jsonify({"status": "error", "message": "Не указан процесс"}), 400

            if not result.ok:
                return jsonify(
                    {
                        "status": "error",
                        "message": result.error
                        or result.output
                        or "Не удалось убить процесс",
                    }
                ), 500

            return jsonify({"status": "success", "message": "Процесс завершён"})
