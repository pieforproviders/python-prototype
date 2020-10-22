import numpy as np
import pandas as pd

import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash_table.FormatTemplate as FormatTemplate

from data_input import get_dashboard_data

# load data
df_dashboard = get_dashboard_data()
min_revenue_sum = df_dashboard['min_revenue'].sum()
max_achievable_revenue_sum = df_dashboard['max_achievable_revenue'].sum()
max_approved_revenue_sum = df_dashboard['max_monthly_payment'].sum()

# dash app
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])

# summary cards
guaranteed_revenue_card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Guaranteed revenue", className="card-title"),
                            html.P(
                                '$' + str(round(min_revenue_sum, 2)), className="card-title"
                            )
                        ]
                    )
                )

potential_revenue_card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Potential revenue", className="card-title"),
                            html.P(
                                '$' + str(round(max_achievable_revenue_sum, 2)), className="card-title"
                            )
                        ]
                    )
                )

max_approved_revenue_card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Max. approved revenue", className="card-title"),
                            html.P(
                                '$' + str(round(max_approved_revenue_sum, 2)), className="card-title"
                            )
                        ]
                    )
                )

app.layout = dbc.Container(
    [
        html.H1(children='Your dashboard'),
        
        # Summary statistics
        dbc.CardGroup(
            [
                guaranteed_revenue_card,
                potential_revenue_card,
                max_approved_revenue_card
            ]
        ),

        dash_table.DataTable(
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
                'id': 'part_day_category',
                'name': 'Part day category',
                'type': 'text'
            }, {
                'id': 'part_day_attendance_rate',
                'name': 'Part day attendance rate',
                'type': 'numeric',
                'format': FormatTemplate.percentage(2)
            }, {
                'id': 'full_day_category',
                'name': 'Full day category',
                'type': 'text'
            }, {
                'id': 'full_day_attendance_rate',
                'name': 'Full day attendance rate',
                'type': 'numeric',
                'format': FormatTemplate.percentage(2)
            }, {
                'id': 'min_revenue',
                'name': 'Guaranteed revenue',
                'type': 'numeric',
                'format': FormatTemplate.money(2)
            },  {
                'id': 'max_achievable_revenue',
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
                        'filter_query': '{part_day_category} = "Not enough information"',
                        'column_id': 'part_day_category'
                    },
                    'backgroundColor': 'rgb(248, 248, 248)',
                    'color': 'rgb(128,128,128)'
                },
                {
                    'if': {
                        'filter_query': '{part_day_category} = "Sure bet"',
                        'column_id': 'part_day_category' 
                    },
                    'color': 'darkgreen'
                },
                {
                    'if': {
                        'filter_query': '{part_day_category} = "Not met"',
                        'column_id': 'part_day_category' 
                    },
                    'color': '#FF4136'
                },
                {
                    'if': {
                        'filter_query': '{part_day_category} = "At risk"',
                        'column_id': 'part_day_category' 
                    },
                    'color': '#FF851B'
                },
                {
                    'if': {
                        'filter_query': '{part_day_category} = "On track"',
                        'column_id': 'part_day_category' 
                    },
                    'color': '#2ECC40'
                },
                {
                    'if': {
                        'filter_query': '{full_day_category} = "Not enough information"',
                        'column_id': 'full_day_category'
                    },
                    'backgroundColor': 'rgb(248, 248, 248)',
                    'color': 'rgb(128,128,128)'
                },
                            {
                    'if': {
                        'filter_query': '{full_day_category} = "Sure bet"',
                        'column_id': 'full_day_category' 
                    },
                    'color': 'darkgreen'
                },
                {
                    'if': {
                        'filter_query': '{full_day_category} = "Not met"',
                        'column_id': 'full_day_category' 
                    },
                    'color': '#FF4136'
                },
                {
                    'if': {
                        'filter_query': '{full_day_category} = "At risk"',
                        'column_id': 'full_day_category' 
                    },
                    'color': '#FF851B'
                },
                {
                    'if': {
                        'filter_query': '{full_day_category} = "On track"',
                        'column_id': 'full_day_category' 
                    },
                    'color': '#2ECC40'
                }
            ],
            sort_action='native',
            sort_mode='single',
        )    
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)