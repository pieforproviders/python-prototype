from pathlib import Path
 
import numpy as np
import pandas as pd

import dash
import dash_html_components as html
import dash_table
import dash_table.FormatTemplate as FormatTemplate


def calculate_month_days(attendance_df):
    # calculate days left and month
    max_attended_date = attendance_df['date'].max()
    month_days = max_attended_date.daysinmonth
    days_left = month_days - max_attended_date.day
    return month_days, days_left

def process_attendance_data(attendance_df):
    # count number of part and full days attended
    def count_part_days(row):
        time_checked_in = row['hours_checked_in'] + (row['mins_checked_in'] / 60)
        if time_checked_in < 5:
            return 1
        elif (time_checked_in > 12) and (time_checked_in < 17):
            return 1
        else:
            return 0

    def count_full_days(row):
        time_checked_in = row['hours_checked_in'] + (row['mins_checked_in'] / 60)
        if time_checked_in < 5:
            return 0
        elif time_checked_in <= 12:
            return 1
        elif time_checked_in < 17:
            return 1
        elif time_checked_in <= 24:
            return 2
        else:
            raise ValueError('Value should not be more than 24')

    attendance_df['part_days_attended'] = attendance_df.apply(count_part_days, axis=1)
    attendance_df['full_days_attended'] = attendance_df.apply(count_full_days, axis=1)

    # aggregate to each child_id
    attendance_per_child = (attendance_df.groupby('child_id')[['full_days_attended', 'part_days_attended']]
                                        .sum())

    return attendance_per_child

def process_merged_data(merged_df, month_days, days_left):
    # helper function to categorize 
    def categorize_families_part_day(row, days_left):
        # part day
        # sure bet
        if row['family_part_days_attended'] >= (0.795 * row['family_part_days_approved']):
            return 'Sure bet'
        # not met
        elif ((0.795 * row['family_part_days_approved'] - row['family_part_days_attended'])
                > days_left):
            return 'Not met'
        # at risk (using percentage rule based on adjusted attendance rate)
        elif (row['family_part_days_attended'] 
                / (((month_days - days_left) / month_days) * row['family_part_days_approved']) < 0.795):
            return 'At risk'
        # on track (all others not falling in above categories)
        else:
            return 'On track'

    def categorize_families_full_day(row, days_left):
        # sure bet
        if row['family_full_days_attended'] >= (0.795 * row['family_full_days_approved']):
            return 'Sure bet'
        # not met
        elif ((0.795 * row['family_full_days_approved'] - row['family_full_days_attended'])
            > days_left):
            return 'Not met'
        # at risk (using percentage rule at 50% of month)
        elif (row['family_full_days_attended'] 
                / (((month_days - days_left) / month_days) * row['family_full_days_approved']) < 0.795):
            return 'At risk'
        # on track (all others not falling in above categories)
        else:
            return 'On track' 
        # todo: check that categories are mutually exclusive

    # calculate family level days approved and attended
    merged_df['family_full_days_approved'] = (merged_df.groupby('case_number')['full_days_approved']
                                                        .transform(lambda x: np.sum(x)))
    merged_df['family_full_days_attended'] = (merged_df.groupby('case_number')['full_days_attended']
                                                        .transform(lambda x: np.sum(x)))               
    merged_df['family_part_days_approved'] = (merged_df.groupby('case_number')['part_days_approved']
                                                        .transform(lambda x: np.sum(x)))
    merged_df['family_part_days_attended'] = (merged_df.groupby('case_number')['part_days_attended']
                                                        .transform(lambda x: np.sum(x)))  

    # categorize families
    merged_df['part_day_category'] = merged_df.apply(categorize_families_part_day,
                                                    args=[days_left],
                                                    axis=1)
    merged_df['full_day_category'] = merged_df.apply(categorize_families_full_day,
                                                    args=[days_left],
                                                    axis=1)
                        
    return merged_df

def calculate_revenues_per_child(merged_df, days_left):
    # helper functions to calculate revenue
    def calculate_max_achievable_revenue(row, days_left):
        # max achievable revenue is approved days * rate unless threshold is already not met
        # full day
        if row['full_day_category'] == 'Not met':
            full_day_max_revenue = (row['full_days_attended'] + days_left) * row['full_day_rate_no_copay']  
        else:
            full_day_max_revenue = row['full_days_approved'] * row['full_day_rate_no_copay']
        # part day
        if row['part_day_category'] == 'Not met':
            part_day_max_revenue = (row['part_days_attended'] + days_left) * row['part_day_rate_no_copay']  
        else:
            part_day_max_revenue = row['part_days_approved'] * row['part_day_rate_no_copay']
        return full_day_max_revenue + part_day_max_revenue

    def calculate_min_revenue(row):
        # min revenue is attended days * rate, unless sure bet
        # full day
        if row['full_day_category'] == 'Sure bet':
            full_day_min_revenue = row['full_days_approved'] * row['full_day_rate_no_copay']
        else:
            full_day_min_revenue = row['full_days_attended'] * row['full_day_rate_no_copay']
        # part day
        if row['part_day_category'] == 'Sure bet':
            part_day_min_revenue = row['part_days_approved'] * row['part_day_rate_no_copay']
        else:
            part_day_min_revenue = row['part_days_attended'] * row['part_day_rate_no_copay'] 
        return full_day_min_revenue + part_day_min_revenue

    # leave out in danger revenues for now
    # def calculate_in_danger_revenue(row):
    #   if row['full_day_category'] == 'At risk':
    #     full_in_danger_revenue = ((row['full_days_approved'] - row['full_days_attended'])
    #                             * row['full_day_rate_no_copay'])
    #   else:
    #     full_in_danger_revenue = 0
    #   if row['part_day_category'] == 'At risk':
    #     part_in_danger_revenue = ((row['part_days_approved'] - row['part_days_attended'])
    #                             * row['part_day_rate_no_copay'])
    #   else:
    #     part_in_danger_revenue = 0
    #   return full_in_danger_revenue + part_in_danger_revenue

    # calculate revenues at child level
    merged_df['max_achievable_revenue'] = merged_df.apply(calculate_max_achievable_revenue,
                                                            args=[days_left],
                                                            axis=1)
    merged_df['min_revenue'] = merged_df.apply(calculate_min_revenue,
                                                axis=1)
    # merged_df['in_danger_revenue'] = merged_df.apply(calculate_in_danger_revenue, axis=1)

    return merged_df

def calculate_attendance_rate(df):
    # part day
    df['part_day_attendance_rate'] = df['family_part_days_attended'] / df['family_part_days_approved']
    # full day
    df['full_day_attendance_rate'] = df['family_full_days_attended'] / df['family_full_days_approved']
    return df

def produce_dashboard_df(df):
    # filter to required columns
    cols_to_keep = ['name',
                    'case_number',
                    'biz_name',
                    'part_day_category',
                    'part_day_attendance_rate',
                    'full_day_category',
                    'full_day_attendance_rate',
                    'min_revenue',
                    'max_achievable_revenue',
                    'max_monthly_payment']
    df_sub = df.loc[:, cols_to_keep].copy()

    return df_sub

data_dir = Path(__file__).parent.parent.absolute().joinpath('data')

# load data
attendance = pd.read_csv(data_dir.joinpath('Attendance_Calculation_Sep-2020.csv'),
                            usecols=['Child ID',
                                    'Date',
                                    'School account',
                                    'Hours checked in',
                                    'Minutes checked in'])
payment = pd.read_csv(data_dir.joinpath('Sample_Billing_Reconciliation.csv'),
                        skiprows=1,
                        usecols=['First name (required)',
                                'Last name (required)',
                                'Business Name (required)',
                                'Case number',
                                'Maximum monthly payment',
                                'Full day rate minus copay',
                                'Part day rate minus copay',
                                'Full days',
                                'Part days',
                                'Child ID'
                                ])

# rename columns to standardize names
attendance.rename(columns={'Child ID': 'child_id',
                            'Date': 'date',
                            'School account': 'biz_name',
                            'Hours checked in': 'hours_checked_in',
                            'Minutes checked in': 'mins_checked_in'},
                  inplace=True)

payment.rename(columns={'First name (required)': 'first_name',
                        'Last name (required)': 'last_name',
                        'Business Name (required)': 'biz_name',
                        'Case number': 'case_number',
                        'Maximum monthly payment': 'max_monthly_payment',
                        'Full day rate minus copay': 'full_day_rate_no_copay',
                        'Part day rate minus copay': 'part_day_rate_no_copay',
                        'Full days': 'full_days_approved',
                        'Part days': 'part_days_approved',
                        'Child ID': 'child_id'},
                inplace=True)


attendance['date'] = pd.to_datetime(attendance['date'])
payment['name'] = payment['first_name'] + ' ' + payment['last_name']

# subset attendance to half month
attendance_half = attendance.loc[attendance['date'] <= pd.to_datetime('2020-09-15'), :].copy()
attendance_processed = process_attendance_data(attendance_half)

# calculate days left
month_days, days_left = calculate_month_days(attendance_half)

# join attendance data to payment data
payment_attendance = pd.merge(payment, attendance_processed, on='child_id')

payment_attendance_processed = process_merged_data(payment_attendance, month_days, days_left)

revenues_per_child_df = calculate_revenues_per_child(payment_attendance_processed,
                                                    days_left)

all_vars_per_child = calculate_attendance_rate(revenues_per_child_df)

df_dashboard = produce_dashboard_df(all_vars_per_child)

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
        ]
    )    
])

if __name__ == '__main__':
    app.run_server(debug=True)
