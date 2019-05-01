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
        if request.user is not None:
            if request.user.is_authenticated:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = []
                first = 0
                counter = 0
                row = 0
                portfolio_list.append([])
                for portfolio in portfolios:
                    if first < 2:
                        portfolio_list[0].append(portfolio)
                        first += 1
                    if first == 2:
                        counter = 3
                        first += 1
                        continue
                    if first > 2:
                        if counter == 3:
                            portfolio_list.append([])
                            row += 1
                            counter = 0
                        portfolio_list[row].append(portfolio)
                        counter += 1

                return render(request, 'portfolio.html', {'portfolios': portfolios, 'list': portfolio_list})
