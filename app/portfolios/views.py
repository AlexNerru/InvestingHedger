from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

import logging

from portfolios.models import Portfolio, Security, Balance

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')

class PortfolioView(View):
    template_name = 'form_template.html'

    def get(self, request, pk):
        request_logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.has_perm('crud portfolio', portfolio):
            return render(request, self.template_name)
        else:
            raise PermissionDenied


    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            return HttpResponseRedirect('/success/')

        return render(request, self.template_name, {'form': form})

class Portfolios(View):

    def get(self, request):
        request_logger.debug(request)
        user = request.user
