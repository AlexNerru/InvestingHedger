import plotly.offline as opy
import plotly.graph_objs as go
from sqlalchemy import create_engine
import pandas as pd


class GraphCreator():

    def get_price_chart(self, data):
        x = data.index
        y = data['price']
        trace = go.Scatter(x=x, y=y, marker={'color': 'green', 'symbol': 104},
                           mode="lines", name='1st Trace')
        layout = go.Layout(xaxis={'title': 'date'}, yaxis={'title': 'price'})
        figure = go.Figure(data=[trace], layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')
        return div

    def get_change_chart(self, data):
        x = data.index
        y = data['change']
        trace = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104},
                           mode="lines", name='1st Trace')
        layout = go.Layout(xaxis={'title': 'date'}, yaxis={'title': 'change'})
        figure = go.Figure(data=[trace], layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')
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
        div = opy.plot(figure, auto_open=False, output_type='div')
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
        div = opy.plot(figure, auto_open=False, output_type='div')
        return div



