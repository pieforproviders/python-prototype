import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from io import StringIO

from data_input import(
    calculate_month_days,
    process_attendance_data
    )

@pytest.fixture
def example_attendance_data():
    attendance_data = StringIO(
        '''child_id,date,biz_name,hours_checked_in,mins_checked_in,
        JanSchakowsky,2020-09-01,Lil Baby Ducklings,11,44
        KeithEllison,2020-09-01,Lil Baby Ducklings,3,34
        LaurenUnderwood,2020-09-02,Lil Baby Ducklings,10,26
        JanSchakowsky,2020-09-02,Lil Baby Ducklings,6,35
        '''
    )
    attendance = pd.read_csv(attendance_data)
    attendance['date'] = pd.to_datetime(attendance['date'])
    return attendance


def test_calculate_month_days(example_attendance_data):
    expected = (30, 28) # function returns month days, days left
    assert calculate_month_days(example_attendance_data) == expected

def test_process_attendance_data(example_attendance_data):
    expected_data = StringIO(
        '''child_id,full_days_attended,part_days_attended
        JanSchakowsky,2,0
        KeithEllison,0,1
        LaurenUnderwood,1,0
        ''' 
    )
    expected = pd.read_csv(expected_data, index_col='child_id')
    assert_frame_equal(process_attendance_data(example_attendance_data), expected,
                       check_like=True)



