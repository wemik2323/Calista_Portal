from flask import Flask, render_template
import importlib
import pkgutil
from pathlib import Path

from services.base import BaseService

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 МБ


def load_services(app):
    services = []
    services_path = Path(__file__).parent / "services"

    for module_info in pkgutil.iter_modules([str(services_path)]):
        # Пропускаем служебные модули
        if module_info.name in ("base",) or module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"services.{module_info.name}")

        # Ищем классы-наследники BaseService
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if (
                isinstance(attr, type)
                and issubclass(attr, BaseService)
                and attr is not BaseService
            ):
                service = attr()
                service.init_app(app)
                services.append(service.get_info())

    services.sort(key=lambda s: s.get("order", 100))
    return services


services = load_services(app)


@app.context_processor
def inject_services():
    return {"services": services}


@app.route("/")
def index():
    return render_template(
        "index.html", services=services, current_service_name=None, content=None
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
