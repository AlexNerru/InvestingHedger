from django.conf import settings
from django.core.management.base import BaseCommand

from django.contrib.auth.management.commands.createsuperuser import get_user_model

import os

class Command(BaseCommand):

    def handle(self, *args, **options):

        username = os.getenv('DJANGO_SU_NAME', 'admin')
        email = os.getenv('DJANGO_SU_EMAIL', 'admin@mysite.com')
        password = os.getenv('DJANGO_SU_PASSWORD', 'mypass')

        get_user_model()._default_manager.db_manager('default')\
            .create_superuser(username=username, email=email, password=password)

        self.stdout.write("SuperUser Created", ending='')