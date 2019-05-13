from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from users.forms import LoginForm, RegisterForm
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from django.contrib import messages

import logging

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')


class MainView(View):
    template_name = 'index.html'

    def get(self, request):
        form = LoginForm()
        register = RegisterForm()
        return render(request, self.template_name, {'form': form, 'form_register': register})


class LoginView(View):

    def post(self, request):
        request_logger.debug(request)
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.data['username'], password=form.data['password'])
            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('/portfolios/')
            else:
                form = LoginForm()
                register = RegisterForm()
                messages.add_message(request, messages.ERROR, 'Check your login and password')
                return render(request, 'index.html', {'form': form, 'form_register': register})
        else:
            form = LoginForm()
            register = RegisterForm()
            messages.add_message(request, messages.ERROR, 'Check your form data')
            return render(request, 'index.html', {'form': form, 'form_register': register})


class RegisterView(View):

    def post(self, request):
        request_logger.debug(request)
        form = RegisterForm(request.POST)
        if form.is_valid():
            if form.data['password'] == form.data['password2']:
                us = User.objects.filter(username=form.data['username']).first()
                if us is None:
                    user = User.objects.create_user(username=form.data['username'], password=form.data['password'])
                    user.save()
                    if user is not None:
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                        return redirect('/portfolios/')
                else:
                    register = RegisterForm()
                    form = LoginForm()
                    messages.add_message(request, messages.ERROR, 'User with this username already exists')
                    return render(request, 'index.html', {'form': form, 'form_register': register})
            else:
                register = RegisterForm()
                form = LoginForm()
                messages.add_message(request, messages.ERROR, 'Passwords does not match')
                return render(request, 'index.html', {'form': form, 'form_register': register})
        else:
            register = RegisterForm()
            form = LoginForm()
            messages.add_message(request, messages.ERROR, 'Check your form data')
            return render(request, 'index.html', {'form': form, 'form_register': register})


class LogoutView(View):

    def get(self, request):
        request_logger.debug(request)
        logout(request)
        form = LoginForm()
        register = RegisterForm()
        return redirect('/', {'form': form, 'form_register': register})
