from django.db import models
from users.models import Profile
from securities.models import Security
from django.core.exceptions import ValidationError

# Create your models here.
class Portfolio(models.Model):
    name = models.CharField(max_length=250)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    securities = models.ManyToManyField(
        Security,
        through='Balance',
        through_fields=('portfolio', 'security'),
    )

    class Meta:
        permissions = (
            ('crud portfolio', 'CRUD portfolio'),
        )


class Balance(models.Model):
    security = models.ForeignKey(Security, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    anount = models.DecimalField(decimal_places=5, max_digits=20)

