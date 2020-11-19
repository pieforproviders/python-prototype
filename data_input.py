import math
import os
from pathlib import Path

from dotenv import load_dotenv
import numpy as np
import pandas as pd

# constants
BASE_PATH = Path(__file__).parent.resolve()
DATA_PATH = Path(__file__).parent.joinpath('data').resolve()
ATTENDANCE_THRESHOLD = 0.495

# load env var from .env file if in local environment
if BASE_PATH.joinpath('.env').exists():
    load_dotenv()
user_dir = os.environ.get('USER_DIR')
attendance_file = os.environ.get('ATTENDANCE_FILE')
payment_file = os.environ.get('PAYMENT_FILE')

def get_attendance_data():
    '''Reads in and processes attendance data'''
    attendance = pd.read_csv(
        DATA_PATH.joinpath(user_dir, attendance_file),
        usecols=[
            'Child ID',
            'Date',
            'School account',
            'Hours checked in',
            'Minutes checked in'
        ]
    )
    # rename columns to standardize column names
    attendance.rename(
        columns={
            'Child ID': 'child_id',
            'Date': 'date',
            'School account': 'biz_name',
            'Hours checked in': 'hours_checked_in',
            'Minutes checked in': 'mins_checked_in'},
        inplace=True
    )
    attendance['date'] = pd.to_datetime(attendance['date'])
    return attendance

def get_payment_data():
    ''' Reads in and processes payment data'''
    payment = pd.read_csv(
        DATA_PATH.joinpath(user_dir, payment_file),
        skiprows=1,
        usecols=[
            'Business Name',
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
        ]
    )
    # rename columns to standardize column names
    payment.rename(
        columns={
            'Business Name': 'biz_name',
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
            'Child ID': 'child_id'
        },
        inplace=True
    )
    payment['name'] = payment['first_name'] + ' ' + payment['last_name']
    return payment

def calculate_month_days(attendance_df):
    ''' Calculate days in month and days left from max attendance date'''
    max_attended_date = attendance_df['date'].max()
    month_days = max_attended_date.daysinmonth
    days_left = month_days - max_attended_date.day
    return month_days, days_left

def count_days_attended(attendance_df):
    '''
    Counts the number of part and full days attended.

    (0,5) hrs: 1 part day
    [5,12] hrs: 1 full day
    (12, 17) hrs: 1 full day and 1 part day
    [17, 24] hrs: 2 full days

    Returns a dataframe with additional columns of full and part days attended.
    '''
    time_checked_in = (
        attendance_df['hours_checked_in'] + (attendance_df['mins_checked_in'] / 60)
    )
    # count number of part and full days attended
    def count_part_days(time_checked_in_):
        if (
            time_checked_in_ < 5
            or  12 < time_checked_in_ < 17
        ):
            return 1
        else:
            return 0

    def count_full_days(time_checked_in_):
        if time_checked_in_ < 5:
            return 0
        if time_checked_in_ < 17:
            return 1
        if time_checked_in_ <= 24:
            return 2
        else:
            # TODO add separate data validation functions
            raise ValueError('Value should not be more than 24')

    attendance_df['part_days_attended'] = time_checked_in.map(count_part_days)
    attendance_df['full_days_attended'] = time_checked_in.map(count_full_days)

    # aggregate to each child_id
    return (
        attendance_df.groupby('child_id')[['full_days_attended', 'part_days_attended']]
                     .sum()
    )

def adjust_school_age_days(merged_df):
    '''
    Adjust approved days for school-aged children based on attendance.

    Returns a dataframe with adjusted full and part day approved
    '''
    # helper function for new extra_full_days field
    def calculate_extra_full_days(row):
        # If school age and attended_full > approved_full,
        # count extra_full_days.
        # Then add to approved_full and subtract approved_part accordingly
        if (
            row['school_age'] == 'Yes'
            and row['full_days_attended'] > row['full_days_approved']
        ):
            extra_full_days = (
                row['full_days_attended'] - row['full_days_approved']
            )
        else:
            extra_full_days = 0
        return extra_full_days

    # calculate "extra" full days used
    merged_df['extra_full_days'] = merged_df.apply(
        calculate_extra_full_days, axis = 1
    )

    # add extra full days to full days approved
    merged_df['adj_full_days_approved'] = merged_df.apply(
        lambda row: row['full_days_approved'] + row['extra_full_days']
        if row['extra_full_days'] > 0 else row['full_days_approved'],
        axis=1
    )

    # subtract extra full days from part days approved
    merged_df['adj_part_days_approved'] = merged_df.apply(
        lambda row: row['part_days_approved'] - row['extra_full_days']
        if row['extra_full_days'] > 0 else row['part_days_approved'],
        axis=1
    )

    merged_df = merged_df.drop('extra_full_days', axis=1)
    return merged_df

def calculate_family_days(merged_df):
    '''
    Aggregates child level days on a family level.

    Returns a dataframe with part and full family days attended and approved.
    '''

    # calculate family level days approved and attended
    merged_df['family_full_days_approved'] = (
        merged_df.groupby('case_number')['adj_full_days_approved']
                 .transform(lambda x: np.sum(x))
    )
    merged_df['family_full_days_attended'] = (
        merged_df.groupby('case_number')['full_days_attended']
                 .transform(lambda x: np.sum(x))
    )
    merged_df['family_part_days_approved'] = (
        merged_df.groupby('case_number')['adj_part_days_approved']
                 .transform(lambda x: np.sum(x))
    )
    merged_df['family_part_days_attended'] = (
        merged_df.groupby('case_number')['part_days_attended']
                 .transform(lambda x: np.sum(x))
    )

    # calculate total family days
    merged_df['family_total_days_approved'] = (
        merged_df['family_full_days_approved']
        + merged_df['family_part_days_approved']
    )
    merged_df['family_total_days_attended'] = (
        merged_df['family_full_days_attended']
        + merged_df['family_part_days_attended']
    )

    return merged_df

def categorize_family_attendance_risk(merged_df, month_days_, days_left_):
    '''
    Categorizes the attendance risk of a family

    Returns a dataframe with an additional attendance risk column
    '''
    days_elapsed = month_days_ - days_left_

    # calculate number of children in the family
    merged_df['num_children_in_family'] = (
        merged_df.groupby('case_number')['child_id']
                 .transform('count')
    )

    def categorize_families(row):
        # helper function to categorize families
        # not enough information
        if days_elapsed / month_days_ < 0.5:
            return 'Not enough info'
        # sure bet
        if (
            # condition 1: attendance rate >= threshold
            row['family_total_days_attended'] / row['family_total_days_approved']
            >= ATTENDANCE_THRESHOLD
            # condition 2: child is one of 3 types below
            and (
                # child is approved for only full days and attended at least 1 full day
                (
                    row['adj_full_days_approved'] > 0
                    and row['full_days_attended'] > 0
                    and row['adj_part_days_approved'] == 0
                )
                # child is approved for only part days and attended at least 1 part day
                or (
                    row['adj_part_days_approved'] > 0
                    and row['part_days_attended'] > 0
                    and row['adj_full_days_approved'] == 0
                )
                # child is approved for both full and part days and
                # attended at least 1 full day and 1 part day
                or (
                    row['adj_full_days_approved'] > 0
                    and row['adj_part_days_approved'] > 0
                    and row['full_days_attended'] > 0
                    and row['part_days_attended'] > 0
                )
            )
        ):
            return 'Sure bet'
        # not met
        if (
            ATTENDANCE_THRESHOLD * row['family_total_days_approved']
            - row['family_total_days_attended']
            > row['num_children_in_family'] * days_left_
        ):
            return 'Not met'
        # at risk (using percentage rule based on adjusted attendance rate)
        if (
            row['family_total_days_attended']
            / ((days_elapsed / month_days_) * row['family_total_days_approved'])
            < ATTENDANCE_THRESHOLD
        ):
            return 'At risk'
        # on track (all others not falling in above categories)
        return 'On track'

    # categorize families
    merged_df['attendance_category'] = merged_df.apply(categorize_families, axis=1)
    # drop col not used in future calculations
    merged_df = merged_df.drop('num_children_in_family', axis=1)
    return merged_df

def calculate_min_revenue_per_child(merged_df):
    '''
    Calculates the minimum (guaranteed revenue) per child.

    Returns a dataframe with an additional min revenue column.
    '''
    def calculate_min_revenue(row):
        # min revenue is attended days * rate, unless sure bet
        # full day
        if row['attendance_category'] == 'Sure bet':
            full_day_min_revenue = row['full_days_approved'] * row['full_day_rate']
            part_day_min_revenue = row['part_days_approved'] * row['part_day_rate']
        else:
            full_day_min_revenue = row['full_days_attended'] * row['full_day_rate']
            part_day_min_revenue = row['part_days_attended'] * row['part_day_rate']
        return full_day_min_revenue + part_day_min_revenue - row['copay']

    merged_df['min_revenue'] = merged_df.apply(calculate_min_revenue, axis=1)
    return merged_df

def calculate_potential_revenue_per_child(merged_df, days_left_):
    '''
    Calculates the potential revenue per child.

    Returns a dataframe with an additional potential revenue column.
    '''
    def calculate_potential_revenue(row, days_left):
        # potential revenue is approved days * rate unless threshold is already not met
        if row['attendance_category'] == 'Not met':
            full_days_difference = (
                row['full_days_approved'] - row['full_days_attended']
            )
            part_days_difference = (
                row['part_days_approved'] - row['part_days_attended']
            )
            potential_revenue_full_days = np.min(
                days_left, full_days_difference
            )
            if full_days_difference < days_left:
                potential_revenue_part_days = np.min(
                    days_left - full_days_difference,
                    part_days_difference
                )
            else:
                potential_revenue_part_days = 0
            full_day_potential_revenue = (
                (row['full_days_attended'] + potential_revenue_full_days)
                * row['full_day_rate']
            )
            part_day_potential_revenue = (
                (row['part_days_attended'] + potential_revenue_part_days)
                * row['part_day_rate']
            )
        else:
            full_day_potential_revenue = (
                row['full_days_approved'] * row['full_day_rate']
            )
            part_day_potential_revenue = (
                row['part_days_approved'] * row['part_day_rate']
            )
        return full_day_potential_revenue + part_day_potential_revenue - row['copay']

    merged_df['potential_revenue'] = merged_df.apply(
        calculate_potential_revenue,
        args=[days_left_],
        axis=1
    )
    return merged_df

def calculate_e_learning_revenue(merged_df):
    '''
    Calculate the additional rev potential if all part days become full

    Returns a dataframe with an additional e learning potential revenue column
    '''
    # Helper function
    def e_learning_helper(row):
        if (row['school_age'] == 'Yes'
            and row['adj_part_days_approved'] > row['part_days_attended']):
            e_learning_revenue = (
                (row['adj_part_days_approved'] - row['part_days_attended'])
                * (row['full_day_rate'] - row['part_day_rate'])
            )
        else:
            e_learning_revenue = 0
        return e_learning_revenue

    merged_df['e_learning_revenue_potential'] = (
        merged_df.apply(e_learning_helper, axis=1)
    )

    return merged_df

def calculate_attendance_rate(df):
    ''' Calculate family attendance rate'''
    df['attendance_rate'] = (
        df['family_total_days_attended'] / df['family_total_days_approved']
    )
    return df

def produce_dashboard_df(df):
    ''' Filter to required columns for dashboard'''
    cols_to_keep = [
        'name',
        'case_number',
        'biz_name',
        'attendance_category',
        'attendance_rate',
        'min_revenue',
        'potential_revenue',
        'max_monthly_payment',
        'e_learning_revenue_potential'
    ]
    df_sub = df.loc[:, cols_to_keep].copy()
    return df_sub

def get_dashboard_data():
    ''' Returns data for dashboard'''
    attendance = get_attendance_data()
    payment = get_payment_data()

    # subset attendance to half month to simulate having onlf half month data
    attendance_half = attendance.loc[attendance['date'] <= pd.to_datetime('2020-09-13'), :].copy()

    # get latest date in attendance data
    latest_date = attendance_half['date'].max().strftime('%b %d %Y')

    # calculate days in month and days left in month
    month_days, days_left = calculate_month_days(attendance_half)

    # check if data is insufficient
    is_data_insufficient = (month_days - days_left)/month_days < 0.5

    # calculate number of days required for at-risk warnings to be shown
    days_req_for_warnings = math.ceil(month_days/2)

    # process data for dashboard
    attendance_processed = count_days_attended(attendance_half)
    payment_attendance = pd.merge(payment, attendance_processed, on='child_id')
    df_dashboard = (
        payment_attendance.pipe(adjust_school_age_days)
                          .pipe(calculate_family_days)
                          .pipe(categorize_family_attendance_risk, month_days, days_left)
                          .pipe(calculate_min_revenue_per_child)
                          .pipe(calculate_potential_revenue_per_child, days_left)
                          .pipe(calculate_e_learning_revenue)
                          .pipe(calculate_attendance_rate)
                          .pipe(produce_dashboard_df)
    )
    return df_dashboard, latest_date, is_data_insufficient, days_req_for_warnings

if __name__ == '__main__':
    get_dashboard_data()
