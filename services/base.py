from flask import Blueprint


class ServiceBase:
    def __init__(self, name, url_prefix, template_folder='templates'):
        self.name = name
        self.url_prefix = url_prefix
        self.blueprint = Blueprint(
            name,
            __name__,
            url_prefix=url_prefix,
            template_folder=template_folder
        )
        self.register_routes()
    
    def register_routes(self):
        """Переопределяется в дочерних классах"""
    
    def get_info(self):
        """Возвращает информацию о сервисе для отображения в меню"""
        return {
            'name': self.name,
            'url': self.url_prefix,
            'available': True
        }
