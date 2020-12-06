import math
import os
from pathlib import Path

from dotenv import load_dotenv
import numpy as np
import pandas as pd

from utilities import (
    pad_hour,
    remove_non_alpha
)

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

def get_attendance_data(filepath):
    '''Reads in attendance data and returns a dataframe'''
    attendance = pd.read_csv(
        filepath,
        usecols=[
            'First name',
            'Last name',
            'Check in time',
            'Check in date',
            'Check out time',
            'Check out date',
            'Hours in care',
            'Minutes in care',
        ],
        dtype={
            'First name': str,
            'Last name': str,
            'Check in time': str,
            'Check in date': str,
            'Check out time': str,
            'Check out date': str,
            'Hours in care': np.float_,
            'Minutes in care': np.float_,
        }
    )
    # rename columns to standardize column names
    attendance.rename(
        columns={
            'First name': 'first_name',
            'Last name': 'last_name',
            'Check in time': 'check_in_time',
            'Check in date': 'check_in_date',
            'Check out time': 'check_out_time',
            'Check out date': 'check_out_date',
            'Hours in care': 'hours_in_care',
            'Minutes in care': 'mins_in_care',
        },
        inplace=True
    )
    return attendance

def get_payment_data(filepath):
    ''' Reads in payment data and returns a dataframe'''
    payment = pd.read_csv(
        filepath,
        skiprows=1,
        usecols=[
            'Business Name',
            'First name',
            'Last name',
            'School age',
            'Case number',
            'Full days approved',
            'Part days (or school days) approved',
            'Co-pay (monthly)',
            'Eligibility',
            'Full day rate',
            'Full day rate quality add-on',
            'Part day rate',
            'Part day rate quality add-on',
            'Co-pay per child',
        ],
        dtype={
            'Business Name': str,
            'First name': str,
            'Last name': str,
            'School age': str,
            'Case number': str,
            'Full days approved': np.float_,
            'Part days (or school days) approved': np.float_,
            'Co-pay (monthly)': np.float_,
            'Eligibility': str,
            'Full day rate': np.float_,
            'Full day rate quality add-on': np.float_,
            'Part day rate': np.float_,
            'Part day rate quality add-on': np.float_,
            'Co-pay per child': np.float_,
        }
    )
    # rename columns to standardize column names
    payment.rename(
        columns={
            'Business Name': 'biz_name',
            'First name': 'first_name',
            'Last name': 'last_name',
            'School age': 'school_age',
            'Case number': 'case_number',
            'Full days approved': 'full_days_approved',
            'Part days (or school days) approved': 'part_days_approved',
            'Co-pay (monthly)': 'family_copay',
            'Eligibility': 'eligibility',
            'Full day rate': 'full_day_rate',
            'Full day rate quality add-on': 'full_day_quality_add_on',
            'Part day rate': 'part_day_rate',
            'Part day rate quality add-on': 'part_day_quality_add_on',
            'Co-pay per child': 'copay_per_child',
        },
        inplace=True
    )
    # fill in nans for approved days as zeros
    payment['full_days_approved'] =  payment['full_days_approved'].fillna(0)
    payment['part_days_approved'] =  payment['part_days_approved'].fillna(0)
    return payment

def clean_attendance_data(attendance_df):
    '''Cleans and prepares attendance data for subsequent calculations'''
    # trim whitespace
    attendance_df['first_name'] = attendance_df['first_name'].map(
        lambda s: s.strip()
    )
    attendance_df['last_name'] = attendance_df['last_name'].map(
        lambda s: s.strip()
    )

    # generate check in and out timestamps
    check_in_str = (
        attendance_df['check_in_time'].map(pad_hour) + ' ' + attendance_df['check_in_date']
    )
    check_in_ts = pd.to_datetime(check_in_str, format='%I:%M %p %m/%d/%Y')

    check_out_str = (
        attendance_df['check_out_time'].map(pad_hour) + ' ' + attendance_df['check_out_date']
    )
    check_out_ts = pd.to_datetime(check_out_str, format='%I:%M %p %m/%d/%Y')

    # calculate time in care
    time_delta = check_out_ts - check_in_ts

    # fill in checked in hours and mins for those not filled in
    attendance_df['hours_in_care'] = attendance_df['hours_in_care'].fillna(
        time_delta.dt.components['hours']
    )
    attendance_df['mins_in_care'] = attendance_df['mins_in_care'].fillna(
        time_delta.dt.components['minutes']
    )

    # convert dates to datetime
    attendance_df['check_in_date'] = pd.to_datetime(attendance_df['check_in_date'])
    attendance_df['check_out_date'] = pd.to_datetime(attendance_df['check_out_date'])

    return attendance_df

def clean_payment_data(payment_df):
    '''Cleans and prepares payment data for subsequent calculations'''
    # trim whitespace for user input text columns
    payment_df['biz_name'] = payment_df['biz_name'].map(
        lambda s: s.strip()
    )
    payment_df['first_name'] = payment_df['first_name'].map(
        lambda s: s.strip()
    )
    payment_df['last_name'] = payment_df['last_name'].map(
        lambda s: s.strip()
    )
    payment_df['case_number'] = payment_df['case_number'].map(
        lambda s: s.strip()
    )
    # generate full name column
    payment_df['name'] = payment_df['first_name'] + ' ' + payment_df['last_name']
    return payment_df

def generate_child_id(df):
    '''Generates a child id column based on first name and last name'''
    first_name = df['first_name'].map(remove_non_alpha)
    last_name = df['last_name'].map(remove_non_alpha)
    df['child_id'] = first_name + last_name
    return df

def calculate_days_in_month(attendance_df):
    ''' Calculate days in month and days left from max attendance date'''
    max_attended_date = attendance_df['check_out_date'].max()
    days_in_month = max_attended_date.daysinmonth
    days_left = days_in_month - max_attended_date.day
    return days_in_month, days_left

def count_days_attended(attendance_df):
    '''
    Counts the number of part and full days attended.

    (0,5) hrs: 1 part day
    [5,12] hrs: 1 full day
    (12, 17) hrs: 1 full day and 1 part day
    [17, 24] hrs: 2 full days

    Returns a dataframe with additional columns of full and part days attended.
    '''
    time_in_care = (
        attendance_df['hours_in_care'] + (attendance_df['mins_in_care'] / 60)
    )
    # count number of part and full days attended
    def count_part_days(time_in_care_):
        if (
            time_in_care_ < 5
            or  12 < time_in_care_ < 17
        ):
            return 1
        else:
            return 0

    def count_full_days(time_in_care_):
        if time_in_care_ < 5:
            return 0
        if time_in_care_ < 17:
            return 1
        if time_in_care_ <= 24:
            return 2
        else:
            # TODO add separate data validation functions
            raise ValueError('Value should not be more than 24')

    attendance_df['part_days_attended'] = time_in_care.map(count_part_days)
    attendance_df['full_days_attended'] = time_in_care.map(count_full_days)

    # aggregate to each child_id
    return (
        attendance_df.groupby('child_id')[['full_days_attended', 'part_days_attended']]
                     .sum()
    )

def combine_payment_and_attendance(payment_df, attendance_df):
    ''' Combines payment and attendance data and returns a merged dataframe.'''
    # left join between payment and attendance data
    merged_df = pd.merge(
        payment_df, attendance_df,
        how='left',
        on='child_id'
    )

    # kids without attendance data have no attendance so set attended days as 0
    merged_df['full_days_attended'] = merged_df['full_days_attended'].fillna(0)
    merged_df['part_days_attended'] = merged_df['part_days_attended'].fillna(0)

    return merged_df

def extract_ineligible_children(merged_df):
    '''Keeps the ineligible children'''
    return merged_df.loc[merged_df['eligibility'] == 'Ineligible', :].copy()

def drop_ineligible_children(merged_df):
    '''Drops ineligible children'''
    return merged_df.loc[merged_df['eligibility'] == 'Eligible', :].copy()

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

def cap_attended_days(merged_df):
    '''
    Caps the days attended by a child to the days approved by rate type.

    We assume that the provider will not receive payment for days attended over
    the days approved for each rate type.

    Returns a dataframe with days attended capped at days approved for each rate
    type.
    '''
    merged_df['full_days_attended'] = merged_df.apply(
        lambda row: row['adj_full_days_approved']
        if row['full_days_attended'] > row['adj_full_days_approved']
        else row['full_days_attended'],
        axis=1
    )

    merged_df['part_days_attended'] = merged_df.apply(
        lambda row: row['adj_part_days_approved']
        if row['part_days_attended'] > row['adj_part_days_approved']
        else row['part_days_attended'],
        axis=1
    )
    return merged_df

def calculate_family_days(merged_df):
    '''
    Aggregates child level days on a family level.

    Returns a dataframe with part and full family days attended and approved.
    '''

    # calculate family level days approved and attended
    merged_df['family_full_days_approved'] = (
        merged_df.groupby('case_number')['adj_full_days_approved']
                 .transform(np.sum)
    )
    merged_df['family_full_days_attended'] = (
        merged_df.groupby('case_number')['full_days_attended']
                 .transform(np.sum)
    )
    merged_df['family_part_days_approved'] = (
        merged_df.groupby('case_number')['adj_part_days_approved']
                 .transform(np.sum)
    )
    merged_df['family_part_days_attended'] = (
        merged_df.groupby('case_number')['part_days_attended']
                 .transform(np.sum)
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

def categorize_family_attendance_risk(merged_df, days_in_month_, days_left_):
    '''
    Categorizes the attendance risk of a family

    Returns a dataframe with an additional attendance risk column
    '''
    days_elapsed = days_in_month_ - days_left_

    # calculate number of children in the family
    merged_df['num_children_in_family'] = (
        merged_df.groupby('case_number')['child_id']
                 .transform('count')
    )

    def categorize_families(row):
        # helper function to categorize families
        # not enough information
        if days_elapsed / days_in_month_ < 0.5:
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
            / ((days_elapsed / days_in_month_) * row['family_total_days_approved'])
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

def calculate_max_revenue_per_child_before_copay(merged_df):
    '''
    Calculates the maximum approved revenue per child before copay.

    Returns a dataframe with an additional max revenue before copay column.
    '''
    def calculate_max_revenue(row):
        return (
            row['adj_full_days_approved'] * row['full_day_rate']
            + row['adj_part_days_approved'] * row['part_day_rate']
        )

    merged_df['max_revenue_before_copay'] = merged_df.apply(calculate_max_revenue, axis=1)
    return merged_df

def calculate_max_quality_add_on_per_child(merged_df):
    '''
    Calculates the quality add on fee corresponding to maximum approved revenue
    per child.

    Returns a dataframe with an additional max quality add on column.
    '''
    def calculate_max_quality_add_on(row):
        return(
            row['adj_full_days_approved'] * row['full_day_quality_add_on']
            + row['adj_part_days_approved'] * row['part_day_quality_add_on']
        )

    merged_df['max_quality_add_on'] = merged_df.apply(calculate_max_quality_add_on, axis=1)
    return merged_df

def calculate_min_revenue_per_child_before_copay(merged_df):
    '''
    Calculates the minimum (guaranteed revenue) per child before copay.

    Returns a dataframe with an additional min revenue before copay column.
    '''
    def calculate_min_revenue(row):
        # if threshold met and > 0 instances of attendance then approved days * rate type
        if (row['family_total_days_attended'] / row['family_total_days_approved']
            >= ATTENDANCE_THRESHOLD):
            if row['full_days_attended'] > 0:
                full_day_min_revenue = row['adj_full_days_approved'] * row['full_day_rate']
            else:
                full_day_min_revenue = 0
            if row['part_days_attended'] > 0:
                part_day_min_revenue = row['adj_part_days_approved'] * row['part_day_rate']
            else:
                part_day_min_revenue = 0
        else:
            full_day_min_revenue = row['full_days_attended'] * row['full_day_rate']
            part_day_min_revenue = row['part_days_attended'] * row['part_day_rate']
        return full_day_min_revenue + part_day_min_revenue

    merged_df['min_revenue_before_copay'] = merged_df.apply(calculate_min_revenue, axis=1)
    return merged_df

def calculate_potential_revenue_per_child_before_copay(merged_df, days_left_):
    '''
    Calculates the potential revenue per child before copay.

    Returns a dataframe with an additional potential revenue before copay column.
    '''
    def calculate_potential_revenue(row, days_left):
        # potential revenue is approved days * rate unless threshold is already not met
        if row['attendance_category'] == 'Not met':
            full_days_difference = (
                row['adj_full_days_approved'] - row['full_days_attended']
            )
            part_days_difference = (
                row['adj_part_days_approved'] - row['part_days_attended']
            )
            potential_revenue_full_days = np.minimum(
                days_left, full_days_difference
            )
            if full_days_difference < days_left:
                potential_revenue_part_days = np.minimum(
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
                row['adj_full_days_approved'] * row['full_day_rate']
            )
            part_day_potential_revenue = (
                row['adj_part_days_approved'] * row['part_day_rate']
            )
        return full_day_potential_revenue + part_day_potential_revenue

    merged_df['potential_revenue_before_copay'] = merged_df.apply(
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

def filter_dashboard_cols(df):
    ''' Filter to required columns for dashboard'''
    cols_to_keep = [
        'name',
        'case_number',
        'biz_name',
        'attendance_category',
        'attendance_rate',
        'min_revenue',
        'potential_revenue',
        'max_revenue',
        'e_learning_revenue_potential'
    ]
    df_sub = df.loc[:, cols_to_keep].copy()
    return df_sub

def produce_ineligible_df(ineligible_df):
    '''Processes ineligible children observations for dashboard'''
    cols_to_keep = [
        'name',
        'case_number',
        'biz_name',
    ]
    ineligible_df = ineligible_df.loc[:, cols_to_keep].copy()

    # add columns where no value was calculated
    ineligible_df['attendance_category'] = 'Case expired'
    ineligible_df['attendance_rate'] = np.nan
    ineligible_df['min_revenue'] = 0
    ineligible_df['potential_revenue'] = 0
    ineligible_df['max_revenue'] = 0
    ineligible_df['e_learning_revenue_potential'] = 0

    return ineligible_df

def get_dashboard_data():
    ''' Returns data for dashboard'''
    attendance = get_attendance_data(DATA_PATH.joinpath(user_dir, attendance_file))
    payment = get_payment_data(DATA_PATH.joinpath(user_dir, payment_file))

    # clean attendance data
    attendance_clean = (
        attendance.pipe(clean_attendance_data)
                  .pipe(generate_child_id)
    )

    # get latest date in attendance data
    latest_date = attendance_clean['check_out_date'].max().strftime('%b %d %Y')

    # calculate days in month and days left in month
    days_in_month, days_left = calculate_days_in_month(attendance_clean)

    # check if data is insufficient
    is_data_insufficient = (days_in_month - days_left) / days_in_month < 0.5

    # calculate number of days required for at-risk warnings to be shown
    days_req_for_warnings = math.ceil(days_in_month/2)

    # process data for dashboard
    attendance_processed = count_days_attended(attendance_clean)
    payment_processed = (
        payment.pipe(clean_payment_data)
               .pipe(generate_child_id)
    )

    # combine payment and attendance data
    payment_attendance = combine_payment_and_attendance(
        payment_processed, attendance_processed
    )

    ineligible = (
        payment_attendance.pipe(extract_ineligible_children)
                          .pipe(produce_ineligible_df)
    )
    df_dashboard = (
        payment_attendance.pipe(drop_ineligible_children)
                          .pipe(adjust_school_age_days)
                          .pipe(cap_attended_days)
                          .pipe(calculate_family_days)
                          .pipe(categorize_family_attendance_risk, days_in_month, days_left)
                          .pipe(calculate_max_revenue_per_child_before_copay)
                          .pipe(calculate_min_revenue_per_child_before_copay)
                          .pipe(calculate_potential_revenue_per_child_before_copay, days_left)
                          .pipe(calculate_e_learning_revenue)
                          .pipe(calculate_attendance_rate)
                          .pipe(filter_dashboard_cols)
                          .append(ineligible, ignore_index=True)
                          .sort_values(by=['case_number', 'name'])
    )
    return df_dashboard, latest_date, is_data_insufficient, days_req_for_warnings

if __name__ == '__main__':
    get_dashboard_data()
