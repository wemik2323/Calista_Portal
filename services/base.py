from abc import ABC, abstractmethod

from flask import Blueprint


class BaseService(ABC):
    name: str = "Unnamed Service"
    url_prefix: str = "/"
    available: bool = True
    order: int = 100

    def __init__(self):
        self.blueprint = Blueprint(
            self.__class__.__name__,
            __name__,
            url_prefix=self.url_prefix,
            template_folder="templates",
            static_folder="static",
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
