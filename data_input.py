from pathlib import Path

import math

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).parent.joinpath('data').resolve()

def get_attendance_data():
    attendance = pd.read_csv(DATA_PATH.joinpath('Attendance-Calculation-Sep-2020.csv'),
                            usecols=['Child ID',
                                    'Date',
                                    'School account',
                                    'Hours checked in',
                                    'Minutes checked in'])
    # rename columns to standardize column names
    attendance.rename(columns={'Child ID': 'child_id',
                            'Date': 'date',
                            'School account': 'biz_name',
                            'Hours checked in': 'hours_checked_in',
                            'Minutes checked in': 'mins_checked_in'},
                  inplace=True)
    attendance['date'] = pd.to_datetime(attendance['date'])
    return attendance

def get_payment_data():
    payment = pd.read_csv(DATA_PATH.joinpath('Sample-Billing-Reconciliation-Sep-2020.csv'),
                            skiprows=1,
                            usecols=['Business Name',
                                    'First name**',
                                    'Last name**',
                                    'School age**',
                                    'Case number**',
                                    'Full days approved**',
                                    'Part days (or school days) approved**',
                                    'Maximum monthly payment',
                                    'Total full day rate',
                                    'Total part day rate',
                                    'Co-pay per child',
                                    'Child ID'
                                    ])
    # rename columns to standardize column names
    payment.rename(columns={'Business Name': 'biz_name',
                            'First name**': 'first_name',
                            'Last name**': 'last_name',
                            'School age**': 'school_age',
                            'Case number**': 'case_number',
                            'Full days approved**': 'full_days_approved',
                            'Part days (or school days) approved**': 'part_days_approved',
                            'Maximum monthly payment': 'max_monthly_payment',
                            'Total full day rate': 'full_day_rate',
                            'Total part day rate': 'part_day_rate',
                            'Co-pay per child': 'copay',
                            'Child ID': 'child_id'},
                    inplace=True)
    payment['name'] = payment['first_name'] + ' ' + payment['last_name']
    return payment


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
        # not enough information
        if (month_days - days_left)/month_days < 0.5:
            return 'Not enough information' 
        # sure bet
        elif row['family_part_days_attended'] >= (0.795 * row['family_part_days_approved']):
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
        # not enough informaton
        if (month_days - days_left)/month_days < 0.5:
            return 'Not enough information' 
        # sure bet
        elif row['family_full_days_attended'] >= (0.795 * row['family_full_days_approved']):
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
            full_day_max_revenue = (row['full_days_attended'] + days_left) * row['full_day_rate']  
        else:
            full_day_max_revenue = row['full_days_approved'] * row['full_day_rate']
        # part day
        if row['part_day_category'] == 'Not met':
            part_day_max_revenue = (row['part_days_attended'] + days_left) * row['part_day_rate']  
        else:
            part_day_max_revenue = row['part_days_approved'] * row['part_day_rate']
        return full_day_max_revenue + part_day_max_revenue - row['copay']

    def calculate_min_revenue(row):
        # min revenue is attended days * rate, unless sure bet
        # full day
        if row['full_day_category'] == 'Sure bet':
            full_day_min_revenue = row['full_days_approved'] * row['full_day_rate']
        else:
            full_day_min_revenue = row['full_days_attended'] * row['full_day_rate']
        # part day
        if row['part_day_category'] == 'Sure bet':
            part_day_min_revenue = row['part_days_approved'] * row['part_day_rate']
        else:
            part_day_min_revenue = row['part_days_attended'] * row['part_day_rate'] 
        return full_day_min_revenue + part_day_min_revenue - row['copay']

    # leave out in danger revenues for now
    # def calculate_in_danger_revenue(row):
    #   if row['full_day_category'] == 'At risk':
    #     full_in_danger_revenue = ((row['full_days_approved'] - row['full_days_attended'])
    #                             * row['full_day_rate'])
    #   else:
    #     full_in_danger_revenue = 0
    #   if row['part_day_category'] == 'At risk':
    #     part_in_danger_revenue = ((row['part_days_approved'] - row['part_days_attended'])
    #                             * row['part_day_rate'])
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

def get_dashboard_data():
    attendance = get_attendance_data()
    payment = get_payment_data()

    # subset attendance to half month to simulate having onlf half month data
    attendance_half = attendance.loc[attendance['date'] <= pd.to_datetime('2020-09-15'), :].copy()

    # get latest date in attendance data
    latest_date = attendance_half['date'].max().strftime('%b %d %Y')

    # calculate days in month and days left in month
    month_days, days_left = calculate_month_days(attendance_half)

    # check if data is insufficient
    is_data_insufficient = (month_days - days_left)/month_days < 0.5

    # calculate number of days required for at-risk warnings to be shown
    days_req_for_warnings = math.ceil(month_days/2)

    # process data for dashboard
    attendance_processed = process_attendance_data(attendance_half)
    payment_attendance = pd.merge(payment, attendance_processed, on='child_id')
    payment_attendance_processed = process_merged_data(payment_attendance, month_days, days_left)
    revenues_per_child_df = calculate_revenues_per_child(payment_attendance_processed,
                                                        days_left)
    all_vars_per_child = calculate_attendance_rate(revenues_per_child_df)
    df_dashboard = produce_dashboard_df(all_vars_per_child)
    return df_dashboard, latest_date, is_data_insufficient, days_req_for_warnings

if __name__ == '__main__':
    attendance = get_attendance_data()
    payment = get_payment_data()

