from dotenv import load_dotenv
import os
from pathlib import Path

import numpy as np
import pandas as pd

import dash
import dash_auth
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from data_input import get_dashboard_data
from make_figures import make_table, make_revenue_chart, make_attendance_table 

# load environment variables
username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')

# load data
df_dashboard, latest_date, is_data_insufficient, days_req_for_warnings = get_dashboard_data()
min_revenue_sum = df_dashboard['min_revenue'].sum()
potential_revenue_sum = df_dashboard['potential_revenue'].sum()
max_approved_revenue_sum = df_dashboard['max_monthly_payment'].sum()

# figures
child_table = make_table(df_dashboard)
revenue_chart = make_revenue_chart(df_dashboard)
summary_table = make_attendance_table(df_dashboard)

# dash app
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])
auth = dash_auth.BasicAuth(
    app,
    {username: password}
)
server = app.server

# navbar
navbar = dbc.Navbar(
    dbc.Container(
        [
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(
                            html.Img(src='/assets/pie_logo.png', height='50px')
                        ),
                ],
                align='center',
                no_gutters=True,
            )
        ],
        fluid=True
    ),
    color="light"
)

# summary cards
attendance_summary_card = dbc.Card(
    [
        dbc.CardBody(
            [   html.H3('Total Attendance',
                        style={'font-size': '1.5rem'}),
                summary_table
            ]
        )  
    ],
    className='h-100',
)

revenue_summary_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3('Total Revenue',
                        style={'font-size': '1.5rem'}),
                dcc.Graph(
                    figure=revenue_chart,
                    config={'displayModeBar':False})
            ]
        )  
    ],
    className='h-100',
)

# detail cards
attendance_copy_card = dbc.Card(
    [
        dbc.CardHeader(
            html.H2(
                dbc.Button(
                    'More details on attendance risk',
                    color='info',
                    id='toggle-1'
                )
            )
        ),
        dbc.Collapse(
            dbc.CardBody(
                [   
                    html.P(
                        [
                            html.Strong('Sure bet: '),
                            html.Span('attendance rate met - maximum payment expected!')
                        ]
                    ),
                    html.P(
                        [
                            html.Strong('On track: '),
                            html.Span('likely to meet attendance rate for full payment')
                        ]
                    ),
                    html.P(
                        [
                            html.Strong('At risk: '),
                            html.Span('may not meet attendance rate for full payment - encourage family to attend')
                        ]
                    ),
                     html.P(
                        [
                            html.Strong('Not met: '),
                            html.Span("full payment not possible; you'll get paid for days attended only")
                        ]
                    ),  
                     html.P(
                        [
                            html.Strong('Not enough info: '),
                            html.Span('email us ' + str(days_req_for_warnings) 
                                        + '+ days of attendance records to get projections')
                        ]
                    )
                ]
            ),
            id='collapse-1'
        )
    ]
)

revenue_copy_card = dbc.Card(
    [
        dbc.CardHeader(
            html.H2(
                dbc.Button(
                    'More details on revenue',
                    color='info',
                    id='toggle-2'
                )
            )
        ),
        dbc.Collapse(
            dbc.CardBody(
                [
                    html.P(
                        [
                            html.Strong('Guaranteed revenue: '),
                            html.Span('based on days already attended')
                        ]
                    ),
                    html.P(
                        [
                            html.Strong('Potential revenue: '),
                            html.Span('based on attendance expected for rest of the month')
                        ]
                    ),
                    html.P(
                        [
                            html.Strong('Max. approved revenue: '),
                            html.Span('if all children meet 80% attendance rate')
                        ]
                    )
                ]
            ),
            id='collapse-2'
        )
    ]
)

accordion = html.Div(
    [attendance_copy_card, revenue_copy_card], className='accordion'
)


app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [   
                html.H1(children='Your dashboard'),

                html.H2('Estimates as of ' + latest_date,
                        style={'font-size': '1.5rem'}),

                html.Div(
                    dbc.Alert('At-risk case warnings will be available with '
                                + str(days_req_for_warnings) 
                                + ' days of attendance data',
                                color='info',
                                is_open=is_data_insufficient)
                ),

                # Summary statistics
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    attendance_summary_card,
                                    width=4
                                ),
                                dbc.Col(
                                    revenue_summary_card,
                                    width=8
                                )
                            ],
                            no_gutters=True,
                            align='stretch'
                        ),
                    ]
                ),

                accordion,

                html.Br(),

                # Child level table
                html.Div(
                    child_table
                )
            ]
        )   
    ]
)

# callbacks
@app.callback(
    [Output(f"collapse-{i}", "is_open") for i in range(1, 3)],
    [Input(f"toggle-{i}", "n_clicks") for i in range(1, 3)],
    [State(f"collapse-{i}", "is_open") for i in range(1, 3)],
)

def toggle_accordion(n1, n2, is_open1, is_open2):
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, False
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "toggle-1" and n1:
        return not is_open1, False
    elif button_id == "toggle-2" and n2:
        return False, not is_open2
    return False, False

if __name__ == '__main__':
    app.run_server(debug=True)
