import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from io import StringIO

from data_input import(
    calculate_month_days,
    count_days_attended,
    adjust_school_age_days,
    cap_attended_days,
    calculate_family_days,
    categorize_family_attendance_risk,
    calculate_max_revenue_per_child,
    calculate_potential_revenue_per_child,
    calculate_e_learning_revenue,
    calculate_attendance_rate,
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

class TestCalculateMonthDays:
    def test_calculate_month_days(self):
        example_df = pd.DataFrame(
            [
                ['2020-09-02'],
                ['2020-09-01'],
            ],
            columns=['check_out_date']
        )
        example_df['check_out_date'] = pd.to_datetime(example_df['check_out_date'])
        expected = (30, 28) # function returns month days, days left
        assert calculate_month_days(example_df) == expected

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

class TestCapAttendedDays:
    def setup_class(self):
        self.columns=[
            'child_id',
            'adj_full_days_approved',
            'full_days_attended',
            'adj_part_days_approved',
            'part_days_attended',
        ]

    def test_cap_attended_days_full_attended_over_approved(self):
        example_df = pd.DataFrame(
            [
                ['a', 5, 6, 4, 2]
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', 5, 5, 4, 2]
            ],
            columns=self.columns
        )

        assert_frame_equal(cap_attended_days(example_df), expected_df)

    def test_cap_attended_days_part_attended_over_approved(self):
        example_df = pd.DataFrame(
            [
                ['a', 5, 3, 4, 6]
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', 5, 3, 4, 4]
            ],
            columns=self.columns
        )

        assert_frame_equal(cap_attended_days(example_df), expected_df)

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
    def setup_class(self):
        self.columns = [
                'child_id',
                'case_number',
                'adj_full_days_approved',
                'adj_part_days_approved',
                'full_days_attended',
                'part_days_attended',
                'family_total_days_approved',
                'family_total_days_attended',
        ]

    def test_not_enough_info(self):
        month_days = 30
        days_left = 16
        example_df = pd.DataFrame(
            [
                ['a', '01', 1, 1, 1, 1, 2, 2],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 1, 1, 1, 1, 2, 2, 'Not enough info']
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_sure_bet_only_full(self):
        month_days = 30
        days_left = 10
        example_df = pd.DataFrame(
            [
                ['a', '01', 1, 0, 1, 0, 1, 1],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 1, 0, 1, 0, 1, 1, 'Sure bet']
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_sure_bet_only_part(self):
        month_days = 30
        days_left = 10
        example_df = pd.DataFrame(
            [
                ['a', '01', 0, 1, 0, 1, 1, 1],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 0, 1, 0, 1, 1, 1, 'Sure bet']
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_sure_bet_part_and_full(self):
        month_days = 30
        days_left = 10
        example_df = pd.DataFrame(
            [
                ['a', '01', 1, 1, 1, 1, 2, 2],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 1, 1, 1, 1, 2, 2, 'Sure bet']
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_not_met(self):
        # test case example from initial_rules_visualization doc
        month_days = 30
        days_left = 5
        example_df = pd.DataFrame(
            [
                ['a', '01', 15, 0, 1, 0, 30, 2],
                ['b', '01', 15, 0, 1, 0, 30, 2],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 15, 0, 1, 0, 30, 2, 'Not met'],
                ['b', '01', 15, 0, 1, 0, 30, 2, 'Not met'],
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_at_risk(self):
        # test case example from initial_rules_visualization doc
        month_days = 30
        days_left = 10
        example_df = pd.DataFrame(
            [
                ['a', '01', 15, 0, 7, 0, 30, 8],
                ['b', '01', 15, 0, 1, 0, 30, 8],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 15, 0, 7, 0, 30, 8, 'At risk'],
                ['b', '01', 15, 0, 1, 0, 30, 8, 'At risk'],
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_on_track_threshold_met_no_full_attendance(self):
        month_days = 30
        days_left = 10
        example_df = pd.DataFrame(
            [
                ['a', '01', 2, 8, 0, 8, 10, 8],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 2, 8, 0, 8, 10, 8, 'On track'],
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

    def test_on_track_threshold_met_no_part_attendance(self):
        month_days = 30
        days_left = 10
        example_df = pd.DataFrame(
            [
                ['a', '01', 8, 2, 8, 0, 10, 8],
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 8, 2, 8, 0, 10, 8, 'On track'],
            ],
            columns=self.columns + ['attendance_category']
        )
        assert_frame_equal(
            categorize_family_attendance_risk(example_df, month_days, days_left),
            expected_df
        )

class TestCalculateMaxRevenuePerChild:
    def setup_class(self):
        self.columns=[
            'adj_full_days_approved',
            'full_day_rate',
            'adj_part_days_approved',
            'part_day_rate',
            'copay',
        ]

    def test_calculate_max_revenue_per_child(self):
        example_df = pd.DataFrame(
            [
                [10, 20, 5, 10, 20]
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                [10, 20, 5, 10, 20, 230]
            ],
            columns=self.columns + ['max_monthly_payment']
        )
        assert_frame_equal(
            calculate_max_revenue_per_child(example_df),
            expected_df
        )

class TestCalculatePotentialRevenuePerChild:
    def setup_class(self):
        self.columns = [
            'child_id',
            'case_number',
            'adj_full_days_approved',
            'adj_part_days_approved',
            'full_days_attended',
            'part_days_attended',
            'attendance_category',
            'full_day_rate',
            'part_day_rate',
            'copay',
        ]

    def test_other_category(self):
        days_left = 5
        example_df = pd.DataFrame(
            [
                ['a', '01', 10, 5, 8, 4, 'Sure bet', 20.0, 10.0, 5.0]
            ],
            columns=self.columns
        )

        expected_df = pd.DataFrame(
            [
                ['a', '01', 10, 5, 8, 4, 'Sure bet', 20.0, 10.0, 5.0, 245.0]
            ],
            columns=self.columns + ['potential_revenue']
        )

        assert_frame_equal(
            calculate_potential_revenue_per_child(example_df, days_left),
            expected_df
        )

    def test_not_met_all_potential_full_days(self):
        # test case from initial_rules_visualization doc
        days_left = 5
        example_df = pd.DataFrame(
            [
                ['a', '01', 10, 5, 1, 1, 'Not met', 20.0, 10.0, 5.0],
            ],
            columns=self.columns
        )
        expected_df = pd.DataFrame(
            [
                ['a', '01', 10, 5, 1, 1, 'Not met', 20.0, 10.0, 5.0, 125.0],
            ],
            columns=self.columns + ['potential_revenue']
        )

        assert_frame_equal(
            calculate_potential_revenue_per_child(example_df, days_left),
            expected_df
        )

    def test_not_met_potential_full_and_part_days(self):
        days_left = 5
        example_df = pd.DataFrame(
            [
                ['a', '01', 2, 20, 1, 1, 'Not met', 20.0, 10.0, 5.0],
            ],
            columns=self.columns
        )
        expected_df = pd.DataFrame(
            [
                ['a', '01', 2, 20, 1, 1, 'Not met', 20.0, 10.0, 5.0, 85.0],
            ],
            columns=self.columns + ['potential_revenue']
        )

        assert_frame_equal(
            calculate_potential_revenue_per_child(example_df, days_left),
            expected_df
        )

    def test_not_met_only_full_days_approved(self):
        days_left = 5
        example_df = pd.DataFrame(
            [
                ['a', '01', 20, 0, 1, 0, 'Not met', 20.0, 10.0, 5.0],
            ],
            columns=self.columns
        )
        expected_df = pd.DataFrame(
            [
                ['a', '01', 20, 0, 1, 0, 'Not met', 20.0, 10.0, 5.0, 115.0],
            ],
            columns=self.columns + ['potential_revenue']
        )

        assert_frame_equal(
            calculate_potential_revenue_per_child(example_df, days_left),
            expected_df
        )

    def test_not_met_only_part_days_approved(self):
        days_left = 5
        example_df = pd.DataFrame(
            [
                ['a', '01', 0, 20, 0, 1, 'Not met', 20.0, 10.0, 5.0],
            ],
            columns=self.columns
        )
        expected_df = pd.DataFrame(
            [
                ['a', '01', 0, 20, 0, 1, 'Not met', 20.0, 10.0, 5.0, 55.0],
            ],
            columns=self.columns + ['potential_revenue']
        )

        assert_frame_equal(
            calculate_potential_revenue_per_child(example_df, days_left),
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

def test_calculate_attendance_rate():
    example_df = pd.DataFrame(
        [
            ['a', '01', 10, 5]
        ],
        columns=[
            'child_id', 'case_number', 'family_total_days_approved',
            'family_total_days_attended'
        ]
    )
    expected_df = pd.DataFrame(
        [
            ['a', '01', 10, 5, 0.5]
        ],
        columns=[
            'child_id', 'case_number', 'family_total_days_approved',
            'family_total_days_attended', 'attendance_rate'
        ]
    )

    assert_frame_equal(calculate_attendance_rate(example_df), expected_df)
