from flask import Flask, render_template

from services.monitoring_service import init_service as init_monitoring_service
from services.print_service import init_service as init_print_service

app = Flask(__name__)

# Общие ограничения приложения
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 МБ

services = [
    {
        "name": "Печать документов",
        "endpoint": "print_service.index",
        "available": True,
        "active": False,
    },
    {
        "name": "Файлы",
        "endpoint": None,
        "available": False,
        "active": False,
    },
    {
        "name": "Мониторинг",
        "endpoint": "monitoring_service.index",
        "available": True,
        "active": False,
    },
]

@app.context_processor
def inject_services():
    return {'services': services}


@app.route("/")
def index():
    return render_template(
        "index.html",
        services=services,
        current_service_name=None,
        content=None
    )


init_print_service(app)
init_monitoring_service(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
