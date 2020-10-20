import numpy as np
import pandas as pd

import dash
import dash_html_components as html
import dash_table
import dash_table.FormatTemplate as FormatTemplate

from data_input import get_dashboard_data

# load data
df_dashboard = get_dashboard_data()

# dash app
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Your dashboard'),
    
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
])

if __name__ == '__main__':
    app.run_server(debug=True)
