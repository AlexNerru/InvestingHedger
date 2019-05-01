from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from users.forms import LoginForm
from django.contrib.auth import authenticate, logout, login

import logging

from portfolios.models import Portfolio, Security, Balance

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')

class MainView(View):
    template_name = 'index.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form':form})

class LoginView(View):

    def post(self, request):
        request_logger.debug(request)
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username = form.data['username'], password = form.data['password'])
            if user is not None:
                login(request, user)
                return redirect('/portfolios/')
            else:
                form = LoginForm()
                return render(request, 'index.html', {'form': form})

class LogoutView(View):

    def get(self, request):
        request_logger.debug(request)
        logout(request)
        form = LoginForm()
        return redirect('/', {'form': form})

