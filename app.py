from dotenv import load_dotenv
import os
from pathlib import Path

import numpy as np
import pandas as pd

import dash
import dash_auth
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash_table.FormatTemplate as FormatTemplate

from data_input import get_dashboard_data

# load environment variables
username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')
ga_tracking_id = os.environ.get('GA_TRACKING_ID')

# load data
df_dashboard, latest_date, is_data_insufficient, days_req_for_warnings = get_dashboard_data()
min_revenue_sum = df_dashboard['min_revenue'].sum()
potential_revenue_sum = df_dashboard['potential_revenue'].sum()
max_approved_revenue_sum = df_dashboard['max_monthly_payment'].sum()

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

# child level table
child_table = dash_table.DataTable(
                id='child_level',
                data=df_dashboard.to_dict('records'),
                columns=[{
                    'id': 'name',
                    'name': 'Child name',
                    'type': 'text'
                }, {
                    'id': 'case_number',
                    'name': 'Case number',
                    'type': 'text'
                }, {
                    'id': 'biz_name',
                    'name': 'Business',
                    'type': 'text'
                }, {
                    'id': 'attendance_category',
                    'name': 'Attendance category',
                    'type': 'text'
                }, {
                    'id': 'attendance_rate',
                    'name': 'Attendance rate',
                    'type': 'numeric',
                    'format': FormatTemplate.percentage(0)
                }, {
                    'id': 'min_revenue',
                    'name': 'Guaranteed revenue',
                    'type': 'numeric',
                    'format': FormatTemplate.money(2)
                },  {
                    'id': 'potential_revenue',
                    'name': 'Potential revenue',
                    'type': 'numeric',
                    'format': FormatTemplate.money(2)
                }, {
                    'id': 'max_monthly_payment',
                    'name': 'Max. revenue approved',
                    'type': 'numeric',
                    'format': FormatTemplate.money(2)
                }],
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{attendance_category} = "Not enough information"',
                            'column_id': 'attendance_category'
                        },
                        'backgroundColor': 'rgb(248, 248, 248)',
                        'color': 'rgb(128,128,128)'
                    },
                    {
                        'if': {
                            'filter_query': '{attendance_category} = "Sure bet"',
                            'column_id': 'attendance_category' 
                        },
                        'color': 'darkgreen'
                    },
                    {
                        'if': {
                            'filter_query': '{attendance_category} = "Not met"',
                            'column_id': 'attendance_category' 
                        },
                        'color': '#FF4136'
                    },
                    {
                        'if': {
                            'filter_query': '{attendance_category} = "At risk"',
                            'column_id': 'attendance_category' 
                        },
                        'color': '#FF851B'
                    },
                    {
                        'if': {
                            'filter_query': '{attendance_category} = "On track"',
                            'column_id': 'attendance_category' 
                        },
                        'color': '#2ECC40'
                    }
                ],
                style_table=
                    {
                        'padding': '20px'
                    },
                sort_action='native',
                sort_mode='single',
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
                        dbc.CardGroup(
                            [
                                guaranteed_revenue_card,
                                potential_revenue_card,
                                max_approved_revenue_card
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

app.index_string=f"""<!DOCTYPE html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_tracking_id}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());

            gtag('config', 'G-04E4MPCQYQ');
        </script>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>"""


if __name__ == '__main__':
    app.run_server(debug=True)
