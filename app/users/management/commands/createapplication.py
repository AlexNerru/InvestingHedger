from django.conf import settings
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application, ApplicationManager

from django.contrib.auth.management.commands.createsuperuser import get_user_model

import os

class Command(BaseCommand):

    def handle(self, *args, **options):

        app = Application()
        app.client_id = os.getenv('CLIENT_ID')
        app.client_secret = os.getenv('CLIENT_SECRET')
        app.client_type = 'confidential'
        app.authorization_grant_type = 'password'
        app.name = 'main'
        app.user_id = 1
        app.save()

        self.stdout.write("New application created", ending='')