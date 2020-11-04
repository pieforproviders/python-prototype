import dash_table
import dash_table.FormatTemplate as FormatTemplate
import plotly.graph_objects as go

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