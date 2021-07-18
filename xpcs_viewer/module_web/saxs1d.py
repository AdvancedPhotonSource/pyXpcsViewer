import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import os
import numpy as np
import plotly.graph_objects as go

import pandas as pd


def list_to_dash(alist, val=None, label_prefix=None):
    assert type(alist) == list
    if val is not None:
        assert len(alist) == len(val)
    else:
        val = alist
    
    if label_prefix is None:
        label_prefix = ''

    return [{'label': label_prefix + alist[n], 'value': val[n]} 
            for n in range(len(alist))]


module = html.Div([
    html.H2('SAXS - 1D'),
    html.Div([ 
        dcc.Graph(id='graph-saxs1d')
    ]), 
    html.Div([
        html.Div([
        dcc.Dropdown(
            id='saxs2d_idx',
            options=list_to_dash(fname, val=range(len(fname))),
            value=0,
           clearable=False),
        ],
            style=dict(width='25%', display = 'inline-block'),
        ),

        html.Div([ 
        dcc.Dropdown(
            id='saxs1d_style',
            options=list_to_dash(['logx-logy', 'logx-y', 'x-logy', 'x-y'], 
                                 label_prefix='style: '),
            value='logx-logy',
            clearable=False),
            ],
            style=dict(width='25%', display = 'inline-block')
        ),
        html.Div([ 
        dcc.Dropdown(
            id='saxs1d_rot',
            options=list_to_dash(['0', '90'], label_prefix='rot: '),
            value='90',
            clearable=False)
            ],
            style=dict(width='25%', display = 'inline-block')
        )
    ]),
]
)


