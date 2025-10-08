from django.core.management.base import BaseCommand, CommandError
from control_panel.models import Tenant
from control_panel.db_manager import register_tenant_db

class Command(BaseCommand):
    help = "Run migrations for a specific tenant"

    def add_arguments(self, parser):
        parser.add_argument(
            'alias',
            type=str,
            help='The DB alias of the tenant to migrate'
        )

    def handle(self, *args, **options):
        alias = options['alias']
        try:
            tenant = Tenant.objects.get(db_alias=alias)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant with alias '{alias}' does not exist.")

        self.stdout.write(f"Running migrations for tenant '{alias}'...")
        register_tenant_db(tenant, migrate=True)
        self.stdout.write(self.style.SUCCESS(f"✅ Migrations completed for tenant '{alias}'"))
