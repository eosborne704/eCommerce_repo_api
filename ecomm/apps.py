from django.apps import AppConfig

class EcommerceConfig(AppConfig):
    name = 'ecomm'
    def ready(self):
        from .functions.tweet import Tweet
        Tweet()
