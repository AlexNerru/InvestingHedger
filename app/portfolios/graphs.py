import plotly.offline as opy
import plotly.graph_objs as go
from sqlalchemy import create_engine
import pandas as pd


class GraphCreator():

    def get_price_chart(self, data, second_data):
        x = data.index
        y = data['price']
        trace = go.Scatter(x=x, y=y, marker={'color': 'green', 'symbol': 104},
                           mode="lines", name='You portfolio')
        trace1 = go.Scatter(x=x, y=second_data, marker={'color': 'blue', 'symbol': 104},
                           mode="lines", name='Optimised portfolio')
        layout = go.Layout(xaxis={'title': 'date'}, yaxis={'title': 'price'})
        figure = go.Figure(data=[trace, trace1], layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div', include_plotlyjs=False)
        return div

    def get_returns_chart(self, data):
        x = data.index
        y = data['change']
        trace = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104},
                           mode="lines", name='1st Trace')
        layout = go.Layout(xaxis={'title': 'date'}, yaxis={'title': 'change'})
        figure = go.Figure(data=[trace], layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div', include_plotlyjs=False)
        return div


    def get_stocks_graph(self, data):
        lines = []

        for column in data:
            x = data.index
            y = data[column]
            trace = go.Scatter(x=x, y=y, marker={ 'symbol': 104},
                               mode="lines", name=column)
            lines.append(trace)
        layout = go.Layout(xaxis={'title': 'date'}, yaxis={'title': 'change'})
        figure = go.Figure(data=lines, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div', include_plotlyjs=False)
        return div

    def get_stocks_change_graph(self, data):
        lines = []

        for column in data:
            x = data.index
            y = data[column]
            trace = go.Scatter(x=x, y=y, marker={'symbol': 104},
                               mode="lines", name=column)
            lines.append(trace)
        layout = go.Layout(xaxis={'title': 'date'}, yaxis={'title': 'change'})
        figure = go.Figure(data=lines, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div', include_plotlyjs=False)
        return div


    def get_frontier_graph(self, stds, means, risks, returns):
        stds = stds.T[0]
        means = means.T[0]
        trace = go.Scatter(x=stds, y=means,
                           mode="markers", name='Portfolios')
        trace1 = go.Scatter(x=risks, y=returns, mode='markers', name = 'Frontier')
        layout = go.Layout(xaxis={'title': 'Volatility'}, yaxis={'title': 'Expected return'})
        figure = go.Figure(data=[trace, trace1], layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')
        return div


