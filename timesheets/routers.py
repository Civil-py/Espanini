from .models import UserDatabase
from threading import local

_user_db_ctx = local()

def set_current_user(user):
    _user_db_ctx.user = user

def get_current_db_alias():
    try:
        user = _user_db_ctx.user
        db_obj = UserDatabase.objects.get(user=user)
        return db_obj.db_alias or 'default'
    except:
        return 'default'

class TenantRouter:
    def db_for_read(self, model, **hints):
        return get_current_db_alias()

    def db_for_write(self, model, **hints):
        return get_current_db_alias()
