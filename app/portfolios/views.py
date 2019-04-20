from django.contrib.auth.models import User
from portfolios.serializers import PortfolioSerializer
from guardian.shortcuts import assign_perm
from rest_framework.views import APIView
from rest_framework.response import Response
from guardian.mixins import PermissionRequiredMixin

from rest_framework import status, permissions

import logging

from portfolios.serializers import PortfolioSerializer

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
                portfolio = serializer.save(user = user)
                assign_perm('crud portfolio', user, portfolio)
                return Response(serializer.data,  status = status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)
