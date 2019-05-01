from django.contrib.auth.models import User
from users.models import Profile
from users.serializers import RegisterSerializer, UserSerializer
from django.shortcuts import get_object_or_404

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')

class UserRegister(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        request_logger.debug(request.data)
        logger.debug(request)
        if request.auth is None:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                user.profile.save()
                serialized_user = UserSerializer(user)
                return Response(serialized_user.data,  status = status.HTTP_200_OK)
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_403_FORBIDDEN)

class UserDetails(APIView):

    def get(self, request, pk):
        request_logger.debug(request.data)
        logger.debug(request)
        user = get_object_or_404(User,pk = pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
