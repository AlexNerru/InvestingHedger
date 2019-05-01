from django.contrib import admin

from portfolios.models import Portfolio, Security, Balance

admin.site.register(Portfolio)
admin.site.register(Security)
admin.site.register(Balance)
# Register your models here.
