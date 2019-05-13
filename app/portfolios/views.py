from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from guardian.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from users.forms import LoginForm, RegisterForm

from guardian.shortcuts import assign_perm

import logging
import re
from datetime import date, datetime

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
        if request.user.is_authenticated:
            if request.user.has_perm('crud portfolio', portfolio):
                creator = GraphCreator()

                data = portfolio.get_portolio_prices()

                # price change day to day
                volatile = portfolio.get_portfolio_returns(data)
                returns_div = creator.get_returns_chart(volatile)

                stocks_data = portfolio.get_stocks_data()
                stocks_div = creator.get_stocks_graph(stocks_data)

                beta = portfolio.get_beta(volatile)
                sharpe = portfolio.get_sharp(volatile)

                stocks_volatile = portfolio.get_stocks_returns(stocks_data)
                stocks_volatile_div = creator.get_stocks_change_graph(stocks_volatile)

                stocks_volatile *= 100

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
                               'alt_weights': alt_weights_string})
            else:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                messages.add_message(request, messages.ERROR, 'You do not have access to this portfolio')
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
        else:
            messages.add_message(request, messages.ERROR, 'You are not authentificated')
            return render(request, 'index.html')


class CreateOptimised(View):

    def get(self, request, pk):
        request_logger.debug(request)
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if request.user.is_authenticated:
            if request.user.has_perm('crud portfolio', portfolio):
                data = portfolio.get_portolio_prices()
                stocks_data = portfolio.get_stocks_data()
                stocks_volatile = portfolio.get_stocks_returns(stocks_data)
                stocks_volatile *= 100
                weights, returns, risks = portfolio.get_efficient_frontier(stocks_volatile)
                portfolio_opt = Portfolio(name=portfolio.name + " Optimized", user=request.user.profile,
                                          creation_date=portfolio.creation_date)
                portfolio_opt.save()
                money = portfolio.get_alt_prices(stocks_data, weights, data['price'].iloc[0])[0]
                amounts = [(weights[i][0] * money) / stocks_data.iloc[0][i] for i in range(len(weights))]
                balances_list = []
                for balance, amount in list(zip(portfolio.balance_set.all(), amounts)):
                    balance = Balance(portfolio=portfolio_opt, security=balance.security, amount=amount)
                    balances_list.append(balance)
                Balance.objects.bulk_create(balances_list)
                assign_perm('crud portfolio', request.user, portfolio_opt)
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
            else:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                messages.add_message(request, messages.ERROR, 'You do not have access to this portfolio')
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
        else:
            form = LoginForm()
            register = RegisterForm()
            messages.add_message(request, messages.ERROR, 'You are not authentificated')
            return render(request, 'index.html', {'form': form, 'form_register': register})


class Portfolios(View):

    def get(self, request):
        request_logger.debug(request)
        if request.user.is_authenticated:
            portfolios = Portfolio.objects.filter(user=request.user.profile).all()
            portfolio_list = get_portfolios_list(portfolios=portfolios)
            return render(request, 'portfolios_list.html', {'list': portfolio_list})
        else:
            messages.add_message(request, messages.ERROR, 'You are not authentificated')
            return render(request, 'index.html')

    def post(self, request):
        security_list = []
        if request.user.is_authenticated:
            tikers = request.POST.getlist('tiker')
            amounts = request.POST.getlist('amount')
            date = request.POST['date']
            x = re.search("^(0[1-9]|1[0-9]|2[0-9]|3[0-1])(-)(0[1-9]|1[0-2])(-)20[0-9][0-9]$", date)
            if x is not None:
                date = datetime.strptime(x.group(), "%d-%m-%Y")
                portfolio = Portfolio(name=request.POST['name'], user=request.user.profile,
                                      creation_date=date)
                if len(tikers) == len(amounts) and len(tikers) >= 2:
                    for tiker in tikers:
                        if tiker != "":
                            security_list.append(get_object_or_404(Security, tiker=tiker.upper()))
                    data = list(zip(security_list, amounts))
                    portfolio.save()
                    balances_list = []
                    for security, amount in data:
                        balance = Balance(portfolio=portfolio, security=security, amount=amount)
                        balances_list.append(balance)
                    Balance.objects.bulk_create(balances_list)
                    assign_perm('crud portfolio', request.user, portfolio)
                    portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                    portfolio_list = get_portfolios_list(portfolios=portfolios)
                    return render(request, 'portfolios_list.html', {'list': portfolio_list})
                else:
                    portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                    portfolio_list = get_portfolios_list(portfolios=portfolios)
                    messages.add_message(request, messages.ERROR, 'Each tiker do not have amount')
                    return render(request, 'portfolios_list.html', {'list': portfolio_list})
            else:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                messages.add_message(request, messages.ERROR, 'Date format is wrong')
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
        else:
            form = LoginForm()
            register = RegisterForm()
            messages.add_message(request, messages.ERROR, 'You are not authentificated')
            return render(request, 'index.html', {'form': form, 'form_register': register})


class DeletePortfolio(View):

    def get(self, request, pk):
        if request.user.is_authenticated:
            portfolio = get_object_or_404(Portfolio, pk=pk)
            if request.user.has_perm('crud portfolio', portfolio):
                portfolio.delete()
                return redirect('/portfolios/')
            else:
                portfolios = Portfolio.objects.filter(user=request.user.profile).all()
                portfolio_list = get_portfolios_list(portfolios=portfolios)
                messages.add_message(request, messages.ERROR, 'You do not have access to this portfolio')
                return render(request, 'portfolios_list.html', {'list': portfolio_list})
        else:
            form = LoginForm()
            register = RegisterForm()
            messages.add_message(request, messages.ERROR, 'You are not authentificated')
            return render(request, 'index.html', {'form': form, 'form_register': register})