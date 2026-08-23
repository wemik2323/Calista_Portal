from abc import ABC, abstractmethod
from pathlib import Path

from flask import Blueprint


class BaseService(ABC):
    name: str = "Unnamed Service"
    url_prefix: str = "/"
    available: bool = True
    order: int = 100

    def __init__(self):
        service_package = self.__module__.split(".")[1]
        root_path = Path(__file__).resolve().parent / service_package

        self.blueprint = Blueprint(
            self.__module__.split(".")[1],
            self.__module__,
            url_prefix=self.url_prefix,
            template_folder="templates",
            static_folder="static",
            root_path=str(root_path),
        )
        self.register_routes()

    @abstractmethod
    def register_routes(self):
        """Каждый сервис обязан зарегистрировать свои роуты здесь."""

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "endpoint": f"{self.blueprint.name}.index",
            "available": self.available,
            "order": self.order,
            "url_prefix": self.url_prefix,
        }

    def init_app(self, app):
        app.register_blueprint(self.blueprint)
