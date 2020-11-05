import numpy as np
import pandas as pd

import dash_table
from dash_table.Format import Format
import dash_table.FormatTemplate as FormatTemplate
import plotly.graph_objects as go

# attendance summary
def make_attendance_table(df):
    # check if not enough info
    if df.loc[0, 'attendance_category'] == 'Not enough information':
        sure_bet_count, at_risk_count, not_met_count, on_track_count = [None] * 4
        sure_bet_pct, at_risk_pct, not_met_pct, on_track_pct = [None] * 4
    else:
        # count children in attendance category
        # using shape[0] to count rows and return an int
        sure_bet_count = df[df['attendance_category'] == 'Sure bet'].shape[0]
        at_risk_count = df[df['attendance_category'] == 'At risk'].shape[0]
        not_met_count = df[df['attendance_category'] == 'Not met'].shape[0]
        on_track_count = df[df['attendance_category'] == 'On track'].shape[0]
        total_count = df['attendance_category'].shape[0]

        # calculate percentage of children in each category
        sure_bet_pct = sure_bet_count / total_count
        at_risk_pct = at_risk_count / total_count
        not_met_pct = not_met_count / total_count
        on_track_pct = on_track_count / total_count

    # make table
    label_col = ['Sure bet',
                 'On track',
                 'At risk',
                 'Not met']
    pct_col = [sure_bet_pct,
               on_track_pct,
               at_risk_pct,
               not_met_pct]
    count_col = [sure_bet_count,
                 on_track_count,
                 at_risk_count,
                 not_met_count]
    df_table = pd.DataFrame({
        'attendance_category': label_col,
        'percentage': pct_col,
        'count': count_col}) 

    table = dash_table.DataTable(
        id='summary',
        columns=[{
                'id': 'attendance_category',
                'name': 'Attendance risk',
                'type': 'text'
            }, {
                'id': 'percentage',
                'name': 'Percentage',
                'type': 'numeric',
                'format': {'nully':'-%',
                        'prefix': None,
                        'specifier': '.0%'}
            }, {
                'id': 'count',
                'name': 'Count',
                'type': 'numeric',
                'format': Format(
                    precision=0,
                    nully='-'
                )
            }
        ],
        data=df_table.to_dict('records'),
        style_as_list_view=True
    )
    return table

# revenue barchart
def make_revenue_chart(df):
    # sum up revenues
    min_revenue_sum = df['min_revenue'].sum()
    potential_revenue_sum = df['potential_revenue'].sum()
    max_approved_revenue_sum = df['max_monthly_payment'].sum()

    min_potential_delta = potential_revenue_sum - min_revenue_sum
    potential_max_delta = max_approved_revenue_sum - potential_revenue_sum

    trace_min = go.Bar(
                    name=('Guaranteed revenue <br>'
                        + '$' + str(round(min_revenue_sum))
                    ),
                    y=['revenue'],
                    x=[min_revenue_sum],
                    width=[0.3],
                    orientation='h',
                    marker_color='rgb(0,110,160)')
    trace_potential = go.Bar(
                        name=('Potential revenue <br>' 
                            + '$' + str(round(potential_revenue_sum))
                        ),
                        y=['revenue'],
                        x=[min_potential_delta],
                        width=[0.3],
                        orientation='h',
                        marker_color='rgb(56,178,234)')
    trace_max = go.Bar(
                    name=('Max. revenue approved <br>'
                        + '$' + str(round(max_approved_revenue_sum))
                    ),
                    y=['revenue'],
                    x=[potential_max_delta],
                    width=[0.3],
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
                       'fixedrange':True,},
                plot_bgcolor='rgb(255,255,255)',
                margin={
                    'l':0,
                    'r':0,
                    't':0,
                    'b':0},
                legend={'orientation':'h',
                        'traceorder':'normal'},
                hovermode=False,
                font={'size':17},
                autosize=False,
                height=150
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
                        'name': 'Attendance risk',
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

    # fig = make_revenue_chart(df_dashboard)
    # fig.show()
    
    make_attendance_table(df_dashboard)


