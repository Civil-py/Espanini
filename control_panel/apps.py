from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ControlPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'control_panel'

    def ready(self):
        """
        Safe AppConfig ready:

        - Does NOT query Tenant objects at import time.
        - All tenant DB registration should happen via `register_tenant_db()` at runtime.
        - Logs a reminder for developers to register tenants properly.
        """
        logger.info(
            "ControlPanel ready: tenant DBs will be registered dynamically at runtime "
            "via `register_tenant_db()`. Do NOT query Tenant objects here."
        )
