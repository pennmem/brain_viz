import pytest
from brainviewer.deltarec import query_to_df, build_prior_stim_results_table, fix_contact_name


@pytest.mark.db
@pytest.mark.parametrize("query_num", [1, 2, 3, 4])
def test_query_to_df(query_num):
    df = query_to_df(query_num)
    assert len(df) > 0

@pytest.mark.db
def test_build_prior_stim_results_table():
    df = build_prior_stim_results_table()
    assert len(df) > 100


@pytest.mark.parametrize("input_label,exp_output", [
    ("LAD1-LAD2", "LAD1 - LAD2"), 
    ("LAD1", "LAD1"), 
    ("LAD2 - LAD3", "LAD2 - LAD3")
    ]
)
def test_fix_contact_name(input_label, exp_output):
    assert fix_contact_name(input_label) == exp_output

