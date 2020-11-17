import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from io import StringIO

from data_input import(
    calculate_month_days,
    count_days_attended,
    adjust_school_age_days,
    calculate_family_days,
    categorize_family_attendance_risk,
    calculate_e_learning_revenue
    )

@pytest.fixture
def example_attendance_data():
    attendance_data = StringIO(
        '''child_id,date,biz_name,hours_checked_in,mins_checked_in,
        JanSchakowsky,2020-09-01,Lil Baby Ducklings,11,44
        KeithEllison,2020-09-01,Lil Baby Ducklings,3,34
        LaurenUnderwood,2020-09-02,Lil Baby Ducklings,10,26
        JanSchakowsky,2020-09-02,Lil Baby Ducklings,6,35
        KamalaHarris,2020-09-02,Lil Baby Ducklings,5,00
        CoryBooker,2020-09-02,Lil Baby Ducklings,12,00
        DebHaaland,2020-09-02,Lil Baby Ducklings,13,45
        GabrielleGifford,2020-09-02,Lil Baby Ducklings,17,00
        JulianCastro,2020-09-02,Lil Baby Ducklings,20,54
        JohnLewis,2020-09-02,Lil Baby Ducklings,24,00
        '''
    )
    attendance = pd.read_csv(attendance_data)
    attendance['date'] = pd.to_datetime(attendance['date'])
    return attendance

def test_calculate_month_days(example_attendance_data):
    expected = (30, 28) # function returns month days, days left
    assert calculate_month_days(example_attendance_data) == expected

def test_count_days_attended(example_attendance_data):
    expected_data = StringIO(
        '''child_id,full_days_attended,part_days_attended
        JanSchakowsky,2,0
        KeithEllison,0,1
        LaurenUnderwood,1,0
        KamalaHarris,1,0
        CoryBooker,1,0
        DebHaaland,1,1
        GabrielleGifford,2,0
        JulianCastro,2,0
        JohnLewis,2,0
        '''
    )
    expected = pd.read_csv(expected_data, index_col='child_id')
    assert_frame_equal(
        count_days_attended(example_attendance_data), expected,
        check_like=True
    )

def test_adjust_school_age_days():
    example_df = pd.DataFrame(
        {
            'child_id': ['a', 'b', 'c', 'd', 'e', 'f'],
            'school_age': ['Yes', 'Yes', 'Yes', 'No', 'No', 'No'],
            'full_days_approved': [5, 5, 5, 5, 5, 5],
            'full_days_attended': [3, 6, 5, 3, 6, 5],
            'part_days_approved': [3, 3, 3, 3, 3, 3],
            'part_days_attended': [5, 2, 3, 5, 2, 3],
        }
    )
    expected_df = pd.DataFrame(
        {
            'child_id': ['a', 'b', 'c', 'd', 'e', 'f'],
            'school_age': ['Yes', 'Yes', 'Yes', 'No', 'No', 'No'],
            'full_days_approved': [5, 5, 5, 5, 5, 5],
            'full_days_attended': [3, 6, 5, 3, 6, 5],
            'part_days_approved': [3, 3, 3, 3, 3, 3],
            'part_days_attended': [5, 2, 3, 5, 2, 3],
            'adj_full_days_approved': [5, 6, 5, 5, 5, 5],
            'adj_part_days_approved': [3, 2, 3, 3, 3, 3],
        }
    )
    assert_frame_equal(
        adjust_school_age_days(example_df), expected_df
    )

def test_calculate_family_days():
    example_df = pd.DataFrame(
        {
            'child_id': ['a', 'b', 'c'],
            'case_number': ['01', '01', '02'],
            'adj_full_days_approved': [5, 6, 7],
            'full_days_attended': [3, 2, 5],
            'adj_part_days_approved': [3, 4, 5],
            'part_days_attended': [2, 4, 4],
        }
    )

    expected_df = pd.DataFrame(
        {
            'child_id': ['a', 'b', 'c'],
            'case_number': ['01', '01', '02'],
            'adj_full_days_approved': [5, 6, 7],
            'full_days_attended': [3, 2, 5],
            'adj_part_days_approved': [3, 4, 5],
            'part_days_attended': [2, 4, 4],
            'family_full_days_approved': [11, 11, 7],
            'family_full_days_attended': [5, 5, 5],
            'family_part_days_approved': [7, 7, 5],
            'family_part_days_attended': [6, 6, 4],
            'family_total_days_approved': [18, 18, 12],
            'family_total_days_attended': [11, 11, 9],
        }
    )
    assert_frame_equal(calculate_family_days(example_df), expected_df)

class TestCategorizeFamilyAttendanceRisk:
    def test_not_enough_info(self):
        month_days = 30
        days_left = 16
        cols = [
                'child_id',
                'case_number',
                'family_total_days_approved',
                'family_total_days_attended',
        ]
        example_df = pd.DataFrame(
            [
                ['a', '01', 1, 1],
            ],
            columns=cols
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 1, 1, 'Not enough info']
            ],
            columns=cols + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

def test_calculate_e_learning_revenue():
    example_df = pd.DataFrame(
        {
            'child_id': ['a', 'b', 'c', 'd'],
            'school_age': ['Yes', 'Yes', 'No', 'No'],
            'part_days_attended': [3, 5, 3, 5],
            'adj_part_days_approved': [5, 5, 5, 5],
            'full_day_rate': [20, 20, 20, 20],
            'part_day_rate': [10, 10, 10, 10],
        }
    )

    expected_df = pd.DataFrame(
        {
            'child_id': ['a', 'b', 'c', 'd'],
            'school_age': ['Yes', 'Yes', 'No', 'No'],
            'part_days_attended': [3, 5, 3, 5],
            'adj_part_days_approved': [5, 5, 5, 5],
            'full_day_rate': [20, 20, 20, 20],
            'part_day_rate': [10, 10, 10, 10],
            'e_learning_revenue_potential': [20, 0, 0, 0],
        }
    )
    assert_frame_equal(calculate_e_learning_revenue(example_df), expected_df)