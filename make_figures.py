import numpy as np
import pandas as pd

import dash_table
import dash_table.FormatTemplate as FormatTemplate
import plotly.graph_objects as go

# revenue barchart
def make_revenue_chart(df):
    # sum up revenues
    min_revenue_sum = df['min_revenue'].sum()
    potential_revenue_sum = df['potential_revenue'].sum()
    max_approved_revenue_sum = df['max_monthly_payment'].sum()

    min_potential_delta = potential_revenue_sum - min_revenue_sum
    potential_max_delta = max_approved_revenue_sum - potential_revenue_sum

    trace_min = go.Bar(
                    name='Minimum revenue',
                    y=['revenue'],
                    x=[min_revenue_sum],
                    width=[0.1],
                    orientation='h',
                    marker_color='rgb(0,110,160)')
    trace_potential = go.Bar(
                        name='Potential revenue',
                        y=['revenue'],
                        x=[min_potential_delta],
                        width=[0.1],
                        orientation='h',
                        marker_color='rgb(56,178,234)')
    trace_max = go.Bar(
                    name='Max. revenue approved',
                    y=['revenue'],
                    x=[potential_max_delta],
                    width=[0.1],
                    orientation='h',
                    marker_color='rgb(204,239,255)')

    data = [trace_min, trace_potential, trace_max]
    layout = go.Layout(
                barmode='stack',
                yaxis={'visible':False,
                       'showticklabels':False,
                       'fixedrange':True},
                xaxis={'showgrid':False,
                       'visible':False,
                       'showticklabels':False,
                       'fixedrange':True},

                plot_bgcolor='rgb(0,255,255)',
                title={'text': 'Total Revenue'},
                legend={'orientation':'h',
                        'traceorder':'normal'},
                hovermode=False
                )
    fig = go.Figure(data=data, layout=layout)
    return fig

# child level table
def make_table(df):
    table = dash_table.DataTable(
                    id='child_level',
                    data=df.to_dict('records'),
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
    return table

if __name__ == '__main__':
    from data_input import get_dashboard_data
    df_dashboard, latest_date, is_data_insufficient, days_req_for_warnings = get_dashboard_data()

    fig = make_revenue_chart(df_dashboard)
    fig.show()



