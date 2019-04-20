from django.db import models
from issuers.models import Issuer

# Create your models here.
class Security(models.Model):
    issuer = models.ForeignKey(Issuer, on_delete=models.CASCADE)
    tiker = models.CharField(unique=True, max_length=10)


class Price(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    #date = models.DateField()
    #low = models.DecimalField()
    #high = models.DecimalField()
    #avg = models.DecimalField()
    #currency = models.CharField()
    #exchange = models.CharField()
