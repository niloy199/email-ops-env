from main import _strict_score
from graders.graders import MIN_SCORE, MAX_SCORE


def test_strict_score_rejects_non_numeric_inputs():
    assert _strict_score(None) == MIN_SCORE
    assert _strict_score("not-a-number") == MIN_SCORE


def test_strict_score_rejects_non_finite_inputs():
    assert _strict_score(float("nan")) == MIN_SCORE
    assert _strict_score(float("inf")) == MIN_SCORE
    assert _strict_score(float("-inf")) == MIN_SCORE


def test_strict_score_clamps_out_of_range_values():
    assert _strict_score(-100.0) == MIN_SCORE
    assert _strict_score(100.0) == MAX_SCORE


def test_strict_score_preserves_in_range_values():
    assert _strict_score(0.5) == 0.5
    assert _strict_score(MIN_SCORE) == MIN_SCORE
    assert _strict_score(MAX_SCORE) == MAX_SCORE
