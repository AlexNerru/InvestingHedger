from django.contrib.auth.models import User
from portfolios.serializers import PortfolioSerializer
from guardian.shortcuts import assign_perm
from rest_framework.views import APIView
from rest_framework.response import Response
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404

from rest_framework import status, permissions

import logging

from portfolios.serializers import PortfolioSerializer, PortfolioDataSerializer, AddStockSerializer
from portfolios.models import Portfolio, Security, Balance

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')

class PortfolioList(APIView):

    def post(self, request):
        request_logger.debug(request.data)
        logger.debug(request)
        serializer = PortfolioSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user is not None:
                portfolio = serializer.save(user = user.profile)
                assign_perm('crud portfolio', user, portfolio)
                created_data = PortfolioDataSerializer(portfolio)
                return Response(created_data.data,  status = status.HTTP_200_OK)
            return Response('User not found', status=status.HTTP_404_NOT_FOUND)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

class PortfolioDetails(APIView):

    def get(self, request, pk):
        request_logger.debug(request.data)
        logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.has_perm('crud portfolio', portfolio):
            serializer = PortfolioDataSerializer(portfolio)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response('You have no access to this portfolio', status = status.HTTP_403_FORBIDDEN)

    def put(self, request, pk):
        request_logger.debug(request.data)
        logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.has_perm('crud portfolio', portfolio):
            serializer = PortfolioSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(portfolio, serializer.validated_data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(status = status.HTTP_400_BAD_REQUEST)
        return Response('You have no access to this portfolio', status=status.HTTP_403_FORBIDDEN)


    def delete(self, request, pk):
        request_logger.debug(request.data)
        logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.has_perm('crud portfolio', portfolio):
            portfolio.delete()
            return Response(status=status.HTTP_200_OK)
        return Response('You have no access to this portfolio', status = status.HTTP_403_FORBIDDEN)

class PortfolioSecurities(APIView):

    def post(self, request, pk):
        request_logger.debug(request.data)
        logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        serializer = AddStockSerializer(request.data)
        if serializer.is_valid():
            if request.user.has_perm('crud portfolio', portfolio):
                security = get_object_or_404(Security, tiker = serializer.validated_data['tiker'])
                balance = Balance(security=security, portfolio=portfolio,
                                  amount = serializer.validated_data['amount'])
                balance.save()
            return Response(status = status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)