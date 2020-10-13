from pathlib import Path
 
import numpy as np
import pandas as pd

import dash
import dash_table
import dash_table.FormatTemplate as FormatTemplate

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

def process_merged_data(merged_df, days_left):
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
        # at risk (using percentage rule at 50% of month)
        elif row['family_part_days_attended'] / (0.5 * row['family_part_days_approved']) < 0.795:
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
        elif row['family_full_days_attended'] / (0.5 * row['family_full_days_approved']) < 0.795:
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
    cols_to_keep = ['child_id',
                    'case_number',
                    'part_day_category',
                    'part_day_attendance_rate',
                    'full_day_category',
                    'full_day_attendance_rate',
                    'min_revenue',
                    'max_achievable_revenue',
                    'max_monthly_payment']
    df_sub = df.loc[:, cols_to_keep].copy()

    return df_sub

# define month variables needed for categorization 
month_days = 30
days_left = 15

data_dir = Path(__file__).parent.parent.absolute().joinpath('data')

# load data
attendance = pd.read_csv(data_dir.joinpath('Attendance_Data.csv'))
payment = pd.read_csv(data_dir.joinpath('Visualization_Data.csv'))

attendance['date'] = pd.to_datetime(attendance['date'])

# subset attendance to half month
attendance_half = attendance.loc[attendance['date'] <= pd.to_datetime('2020-02-15'), :].copy()
attendance_processed = process_attendance_data(attendance_half)

# join attendance data to payment data
payment_attendance = pd.merge(payment, attendance_processed, on='child_id')

payment_attendance_processed = process_merged_data(payment_attendance, days_left)

revenues_per_child_df = calculate_revenues_per_child(payment_attendance_processed,
                                                     days_left)

all_vars_per_child = calculate_attendance_rate(revenues_per_child_df)

df_dashboard = produce_dashboard_df(all_vars_per_child)

# dash app
app = dash.Dash(__name__)

app.layout = dash_table.DataTable(
    id='child_level',
    data=df_dashboard.to_dict('records'),
    columns=[{
        'id': 'child_id',
        'name': 'Child ID',
        'type': 'text'
    }, {
        'id': 'case_number',
        'name': 'Case number',
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
    }]
    )

if __name__ == '__main__':
    app.run_server(debug=True)
