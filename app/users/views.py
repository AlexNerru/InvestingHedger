from django.shortcuts import render
from django.contrib.auth.models import User
from users.models import Profile

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from users.serializers import RegisterSerializer, UserSerializer

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
                serializer.save()
                user = User.objects.get(
                    email = serializer.validated_data.get('email'))
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
        user = Profile.objects.filter(pub_key = pk).first()
        if user is not None:
            serializer = UserSerializer(user.user)
            user_dict = serializer.data
            return Response(user_dict, status=status.HTTP_200_OK)
        return Response("No such user", status=status.HTTP_404_NOT_FOUND)
