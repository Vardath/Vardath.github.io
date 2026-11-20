import pytest
from capability.capacity import estimate


def test_planner_has_correct_units():
    info = estimate(10_000_000, 20_000_000, tokens_per_second=1000)
    assert info['dense_training_flops_approx'] == 1_200_000_000_000_000
    assert info['measured_machine_projection']['training_hours_at_that_rate'] == round(20_000/3600, 2)
    assert 'not a benchmark' in info['assumptions'][0]


def test_planner_rejects_unfounded_values():
    with pytest.raises(ValueError):
        estimate(0, 100)
    with pytest.raises(ValueError):
        estimate(10, 10, tokens_per_second=0)
