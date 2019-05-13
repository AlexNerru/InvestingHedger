from rest_framework import serializers
from django.contrib.auth.models import User
from portfolios.models import Portfolio
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator


class PortfolioSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta():
        model = Portfolio
        fields = ('name',)


class PortfolioDataSerializer(serializers.ModelSerializer):
    class Meta():
        model = Portfolio
        fields = '__all__'


class AddStockSerializer(serializers.Serializer):
    portfolio = serializers.IntegerField()
    security = serializers.CharField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=5)
