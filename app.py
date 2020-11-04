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
            [
                summary_table
            ]
        )  
    ]
)

revenue_summary_card = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Graph(
                    figure=revenue_chart,
                    config={'displayModeBar':False})
            ]
        )  
    ]
)

guaranteed_revenue_card = dbc.Card(
    [
        dbc.CardHeader("Guaranteed revenue"),
        dbc.CardBody(
            [
                html.H4(
                    '$' + str(round(min_revenue_sum, 2)), className="card-title font-weight-bold"
                )
            ]
        )  
    ]
)

potential_revenue_card = dbc.Card(
    [
        dbc.CardHeader("Potential revenue"),
        dbc.CardBody(
            [
                html.H4(
                    '$' + str(round(potential_revenue_sum, 2)), className="card-title font-weight-bold"
                )
            ]
        )  
    ]
)

max_approved_revenue_card = dbc.Card(
    [
        dbc.CardHeader("Max. approved revenue"),
        dbc.CardBody(
            [
                html.H4(
                    '$' + str(round(max_approved_revenue_sum, 2)), className="card-title font-weight-bold"
                )
            ]
        )  
    ]
)


app.layout = html.Div(
    [navbar,
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
                        dbc.CardGroup(
                            [
                                attendance_summary_card,
                                revenue_summary_card,
                            ],
                        ),
                    ]
                ),

                html.Br(),

                # Child level table
                html.Div(
                    child_table
                )
            ]
        )   
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)
