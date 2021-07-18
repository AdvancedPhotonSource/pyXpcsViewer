# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from numpy.core.defchararray import title
from xpcs_viewer_app import app
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components.Label import Label
import plotly.express as px
from dash.dependencies import Input, Output
import os
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from xpcs_viewer import XpcsFile as xf
import pandas as pd

colors = px.colors.qualitative.Plotly


xf_dict = {}


def create_slice(arr, x_range):
    start, end = 0, arr.size - 1
    
    # switch order if lower > upper
    if x_range is not None and x_range[0] > x_range[1]:
        temp = list(x_range)
        x_range = [temp[1], temp[0]]

    # return all range for None and invalid inputs
    if x_range is None or x_range[0] > np.max(arr) or x_range[1] < np.min(arr):
        return slice(start, end + 1)

    while arr[start] < x_range[0]:
        start += 1
        if start == arr.size:
            break

    while arr[end] >= x_range[1]:
        end -= 1
        if end <= 0:
            break
    
    return slice(start, end + 1)


def get_data(xf_list, q_range=None, t_range=None):
    tslice = create_slice(xf_list[0].t_el, t_range)
    qslice = create_slice(xf_list[0].ql_dyn, q_range)

    flag = True
    tel, qd, g2, g2_err = [], [], [], []
    for fc in xf_list:
        tel.append(fc.t_el[tslice])
        qd.append(fc.ql_dyn[qslice])
        g2.append(fc.g2[tslice, qslice])
        g2_err.append(fc.g2_err[tslice, qslice])

    # t_shape = set([t.shape for t in tel])
    # q_shape = set([q.shape for q in qd])
    # if len(t_shape) != 1 or len(q_shape) != 1:
    #     logger.error('the data files are not consistent in tau or q')
    #     flag = False

    return flag, tel, qd, g2, g2_err



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


def gen_file_list(path=None):
    path = "/Users/mqichu/local_dev/xpcs_data/test_data"
    fname = os.listdir(path)
    flist = list_to_dash(fname)
    xf_dict.clear()

    for x in fname:
        xf_dict[x] = xf(x, cwd=path)

    return fname, flist


def generate_sax1d_df():
    df_list = []
    for key in xf_dict.keys():
        df = pd.DataFrame({'saxs1d': xf_dict[key].saxs_1d,
                            'q': xf_dict[key].ql_sta})
        df['label'] = key 
        df_list.append(df)
    saxs1d_df = pd.concat(df_list, ignore_index=True)

    return saxs1d_df


def generate_saxs2d_array():
    saxs2d = []
    for key in xf_dict.keys():
        saxs2d.append(xf_dict[key].saxs_2d)
    saxs2d = np.array(saxs2d)
    non_zero_min = np.min(saxs2d[saxs2d > 0])
    saxs2d = np.log10(saxs2d + non_zero_min)
    return saxs2d


def create_color_maps():
    clist = ['Plotly3', 'Viridis', 'Plasma', 'Magma', 'Turbo', 'Blackbody',
             'Bluered', 'Hot', 'Jet', 'Rainbow']
    cmap_options = list_to_dash(clist, label_prefix='cmap: ')
    return cmap_options

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


fname, flist = gen_file_list()
xf_list = [xf_dict[x] for x in fname]
saxs1d_df = generate_sax1d_df()
saxs2d_ar = generate_saxs2d_array()
cmap_options = create_color_maps()



app.layout = html.Div([
    html.Div([
        html.H2('Saxs2D'),
        dcc.Graph(id='graph-saxs2d', style={'height':800}),
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
            id='saxs2d_cmap',
            options=cmap_options,
            value='Plotly3',
           clearable=False),
        ],
            style=dict(width='25%', display = 'inline-block'),
        ),

        html.Div([ 
        dcc.Dropdown(
            id='saxs2d_style',
            options=list_to_dash(['log', 'linear'], label_prefix='style: '),
            value='log',
            clearable=False),
            ],
            style=dict(width='25%', display = 'inline-block')
        ),
        html.Div([ 
        dcc.Dropdown(
            id='saxs2d_rot',
            options=list_to_dash(['0', '90'], label_prefix='rot: '),
            value='90',
            clearable=False)
            ],
            style=dict(width='25%', display = 'inline-block')
        )
    ]),
    html.Div([ 
        html.H2('Saxs1D'),
        dcc.Graph(id='graph-saxs1d'),
        html.Div([ 
            dcc.Dropdown(
                id='saxs1d_xstyle',
                options=list_to_dash(['log', 'linear'], label_prefix='x: '),
                value='log',
                clearable=False)
                ],
                style=dict(width='25%', display = 'inline-block')
        ),

        html.Div([ 
            dcc.Dropdown(
                id='saxs1d_ystyle',
                options=list_to_dash(['log', 'linear'], label_prefix='y: '),
                value='log',
                clearable=False)
                ],
                style=dict(width='25%', display = 'inline-block')
        ),
    ]),
    html.Div([ 
        html.H2('Intensity - t'),
        dcc.Graph(id='graph-intt', style={'height': 800}),
        html.Div([
            dcc.Dropdown(
                id='intt-idx',
                options=list_to_dash(fname, val=range(len(fname))),
                value=0,
               clearable=False),
            ],
            style=dict(width='25%', display = 'inline-block'),
        ), 
        html.Div([
            'sampling:',
            dcc.Slider(
                id='intt-sampling', min=1, max=10, step=1, value=1,
                marks={x: str(x) for x in range(1, 11, 1)}),
            ],
            style=dict(width='25%', display = 'inline-block'),
        ),
    ]),
    html.Div([ 
        html.H2('g2 correlation'),
        dcc.Graph(id='graph-g2', style={'height': 800}),
        html.Div([
            'g2_idx:',
            dcc.Dropdown(
                id='g2-idx',
                options=list_to_dash(fname, val=range(len(fname))),
                value=0,
               clearable=False),
            ],
            style=dict(width='25%', display = 'inline-block'),
        ), 
        html.Div([
            'g2-qmin:',
            dcc.Input(
                id="g2-qmin",
                type="number",
                placeholder="g2-qmin",
                value=0.0),
            'g2-qmax:',
            dcc.Input(
                id="g2-qmax",
                type="number",
                value=0.0092,
                placeholder="g2-qmax")
            ]
        ),
        html.Div([
            'g2-tmin:',
            dcc.Input(
                id="g2-tmin",
                type="number",
                value=0.000001,
                placeholder="t-min"),
            'g2-tmax:',
            dcc.Input(
                id="g2-tmax",
                type="number",
                value=0.1,
                placeholder="t-max")
            ]
        ),

        html.Div([
            'num_col:',
            dcc.Input(
                id="g2-num_col",
                type="number",
                value=4,
                placeholder="number of col")
            ]
        ),
    ]),
    html.Div([], style=dict(height=300))
])


@app.callback(
    Output('graph-saxs2d', 'figure'),
    Input('saxs2d_idx', 'value'),
    Input('saxs2d_cmap', 'value'),
    Input('saxs2d_style', 'value'),
    Input('saxs2d_rot', 'value')
)
def create_saxs2d_figure(idx, cmap, style, rot):
    if style == 'linear':
        data = 10 ** saxs2d_ar[idx]
    elif style == 'log':
        data = saxs2d_ar[idx]
    
    if rot == '90':
        data = data.T

    fig_saxs2d = px.imshow(data, color_continuous_scale=cmap)
    return fig_saxs2d


@app.callback(
    Output('graph-saxs1d', 'figure'),
    Input('saxs1d_xstyle', 'value'),
    Input('saxs1d_ystyle', 'value'),
)
def create_saxs1d_figure(xstyle, ystyle):
    log_x = xstyle == 'log'
    log_y = ystyle == 'log'
    fig_saxs1d = px.scatter(saxs1d_df, x="q", y="saxs1d",
                     color="label", hover_name="label",
                     log_x=log_x, log_y=log_y)

    fig_saxs1d.update_layout(clickmode='event+select', xaxis_title=r'q (Å⁻¹)')
    return fig_saxs1d


@app.callback(
    Output('graph-intt', 'figure'),
    Input('intt-idx', 'value'),
    Input('intt-sampling', 'value'),
)
def create_intt_figure(idx, sampling):
    plot_fname = fname[idx]
    y = xf_dict[plot_fname].Int_t[1][::int(sampling)]
    delta_t = xf_dict[plot_fname].t0 * sampling

    x = np.arange(len(y)) * delta_t

    y_fft = np.abs(np.fft.fft(y))

    x_fft = np.arange(y.size // 2) / (y.size * delta_t)
    y_fft = y_fft[slice(0, y.size // 2)]
    # get ride of zero frequency;
    y_fft[0] = 0

    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(
        go.Scatter(x=x, y=y, name='Time domain'), row=1, col=1,
    )    
    fig.add_trace(
        go.Scatter(x=x_fft, y=y_fft, name='Frequency domain'), row=2, col=1,
    )    
    fig.update_xaxes(title_text="Time (s)", row=1, col=1)
    fig.update_yaxes(title_text="counts (ct/s)", row=1, col=1)

    fig.update_xaxes(title_text="Frequency (Hz)", row=2, col=1)
    fig.update_yaxes(title_text="FFT Amplitude", row=2, col=1)

    return fig


@app.callback(
    Output('graph-g2', 'figure'),
    Input('g2-qmin', 'value'),
    Input('g2-qmax', 'value'),
    Input('g2-tmin', 'value'),
    Input('g2-tmax', 'value'),
    Input('g2-num_col', 'value')
)
def create_g2_figure(qmin, qmax, tmin, tmax, num_col):
    flag, tel, qd, g2, g2_err = get_data(xf_list, q_range=(qmin, qmax),
                                                  t_range=(tmin, tmax))
    if num_col is None:
        return
    num_dst = len(g2)
    num_fig = g2[0].shape[1]
    num_row = (num_fig + num_col - 1) // num_col
    subplot_titles = ["q=%.4fÅ⁻¹" % qd[0][m] for m in range(num_fig)]

    fig = make_subplots(rows=num_row, cols=num_col, shared_xaxes=False,
                        subplot_titles=subplot_titles)

    for n in range(num_dst):
    # for n in range(1):
        line_color = colors[n % len(colors)]
        for m in range(num_fig):
            loc_r = m // num_col + 1
            loc_c = m % num_col + 1
            if m == 0:
                fig.add_trace(
                    go.Scatter(x=tel[n], y=g2[n][:, m], name=xf_list[n].label,
                               legendgroup='group1', line_color=line_color),
                    row=loc_r, col=loc_c)
            else:
                fig.add_trace(
                    go.Scatter(x=tel[n], y=g2[n][:, m], name=xf_list[n].label,
                               legendgroup='group1', line_color=line_color,
                               showlegend=False),
                    row=loc_r, col=loc_c)
            if n == num_dst - 1:
                fig.update_xaxes(title_text= "t (s)",
                                 type="log", row=loc_r, col=loc_c)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
