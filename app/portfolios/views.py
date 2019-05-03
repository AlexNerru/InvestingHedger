from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

import logging
from datetime import date

from portfolios.models import Portfolio, Security, Balance
from portfolios.graphs import GraphCreator

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')


class PortfolioView(View):

    def get(self, request, pk):
        request_logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.has_perm('crud portfolio', portfolio):
            creator = GraphCreator()

            data = portfolio.get_prices()
            div = creator.get_price_chart(data)

            volatile = portfolio.get_portfolio_returns(data)
            returns_div = creator.get_change_chart(volatile)

            stocks_data = portfolio.get_stocks_data()
            stocks_div = creator.get_stocks_graph(stocks_data)

            beta = portfolio.get_beta(volatile)
            sharpe = portfolio.get_sharp(volatile)

            stocks_volatile = portfolio.get_stocks_returns(stocks_data)
            stocks_volatile_div = creator.get_stocks_change_graph(stocks_volatile)

            return render(request, 'portfolio.html',
                          {'graph': div, 'change':returns_div,
                           'portfolio': portfolio, 'beta':beta,
                           'sharpe': sharpe, 'stocks': stocks_div,
                           'stock_change': stocks_volatile_div})
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

                return render(request, 'portfolios_list.html', {'portfolios': portfolios, 'list': portfolio_list})
