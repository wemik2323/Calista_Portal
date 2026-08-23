import time

import psutil
from flask import jsonify, render_template

from services.base import BaseService


class MonitoringService(BaseService):
    name = "Мониторинг"
    url_prefix = "/status"
    order = 2
    available = True

    def register_routes(self):
        bp = self.blueprint

        @bp.route("/")
        def index():
            return render_template(
                "status.html",
                current_service_name=self.name,
            )

        @bp.route("/api/stats")
        def get_stats():
            return jsonify(
                {
                    "cpu": psutil.cpu_percent(interval=0.1),
                    "memory": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage("/").percent,
                    "uptime": self._get_uptime(),
                }
            )

    def _get_uptime(self):
        uptime_seconds = time.time() - psutil.boot_time()
        return {
            "days": int(uptime_seconds // 86400),
            "hours": int((uptime_seconds % 86400) // 3600),
            "minutes": int((uptime_seconds % 3600) // 60),
            "seconds": int(uptime_seconds % 60),
        }
