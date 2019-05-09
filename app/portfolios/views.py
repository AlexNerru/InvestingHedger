from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied

import logging
from datetime import date

from portfolios.models import Portfolio, Security, Balance
from portfolios.graphs import GraphCreator

logger = logging.getLogger('django')
request_logger = logging.getLogger('django.request')


def get_portfolios_list(portfolios):
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
    return portfolio_list

class PortfolioView(View):

    def get(self, request, pk):
        request_logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.has_perm('crud portfolio', portfolio):
            creator = GraphCreator()

            data = portfolio.get_prices()

            volatile = portfolio.get_portfolio_returns(data)
            returns_div = creator.get_change_chart(volatile)

            stocks_data = portfolio.get_stocks_data()
            stocks_div = creator.get_stocks_graph(stocks_data)

            beta = portfolio.get_beta(volatile)
            sharpe = portfolio.get_sharp(volatile)

            stocks_volatile = portfolio.get_stocks_returns(stocks_data)
            stocks_volatile_div = creator.get_stocks_change_graph(stocks_volatile)

            stocks_volatile*=100

            weights, returns, risks = portfolio.get_efficient_frontier(stocks_volatile)

            alt_price = portfolio.get_alt_prices(stocks_data, weights, data['price'].iloc[0])
            div = creator.get_price_chart(data, alt_price)

            returns_trans = stocks_volatile.to_numpy().T
            means, stds = portfolio.get_random_portfolios(returns_trans)

            frontier = creator.get_frontier_graph(stds, means, risks, returns)

            weights_string = portfolio.get_shares()
            alt_weights_string = portfolio.get_alt_shares_string(weights, stocks_data)

            return render(request, 'portfolio.html',
                          {'graph': div, 'change': returns_div,
                           'portfolio': portfolio, 'beta': beta,
                           'sharpe': sharpe, 'stocks': stocks_div,
                           'stock_change': stocks_volatile_div,
                           'frontier': frontier,
                           'weights': weights_string,
                           'alt_weights':alt_weights_string})
        else:
            raise PermissionDenied


class Portfolios(View):

    def get(self, request):
        request_logger.debug(request)
        if request.user is not None:
            if request.user.is_authenticated:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios = portfolios)
                return render(request, 'portfolios_list.html', {'list': portfolio_list})

    def post(self, request):
        security_list = []
        if request.user.is_authenticated:
            portfolio = Portfolio(name=request.POST['name'], user=request.user.profile, creation_date=date(2018,1,1))
            tikers = request.POST.getlist('tiker')
            amounts = request.POST.getlist('amount')
            if len(tikers) == len(amounts) and len(tikers) >= 2:
                for tiker in tikers:
                    security_list.append(get_object_or_404(Security, tiker = tiker))
                data = list(zip(security_list, amounts))
                portfolio.save()
                balances_list = []
                for security, amount in data:
                    balance = Balance(portfolio = portfolio, security = security, amount=amount)
                    balances_list.append(balance)
                Balance.objects.bulk_create(balances_list)
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
            else:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
        else:
            return PermissionDenied

class DeletePortfolio(View):

    def get(self, request, pk):
        if request.user.is_authenticated:
            portfolio = get_object_or_404(Portfolio, pk = pk)
            if request.user.has_perm('crud portfolio', portfolio):
                portfolio.delete()
                return redirect('/portfolios/')
            else:
                return PermissionDenied
        else:
            return PermissionDenied


