import plotly.offline as opy
import plotly.graph_objs as go
from sqlalchemy import create_engine
import pandas as pd

class GraphCreator():

    def get_context_data(self):
        x = [-2,0,4,6,7]
        y = [q**2-q+3 for q in x]
        trace1 = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104},
                            mode="lines",  name='1st Trace')

        data=go.Data([trace1])
        layout=go.Layout(title="Meine Daten", xaxis={'title':'x1'}, yaxis={'title':'x2'})
        figure=go.Figure(data=data,layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')

        return div

    def get_price_chart(self, data):
        x = data['date']
        y = data['price']
        trace = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104},
                            mode="lines", name='1st Trace')
        data = go.Data([trace])
        layout = go.Layout(title="Portfolio Price", xaxis={'title': 'date'}, yaxis={'title': 'price'})
        figure = go.Figure(data=data, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')
        return div

    def get_change_chart(self, data):
        x = data['date']
        y = data['change']
        trace = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104},
                            mode="lines", name='1st Trace')
        data = go.Data([trace])
        layout = go.Layout(title="Portfolio Volatile", xaxis={'title': 'date'}, yaxis={'title': 'change'})
        figure = go.Figure(data=data, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')
        return div


