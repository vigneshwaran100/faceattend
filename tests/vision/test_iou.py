import pytest

from app.vision.iou import calculate_iou


def test_exact_same_boxes() -> None:
    box = (10, 10, 100, 100)

    result = calculate_iou(box, box)

    assert result == pytest.approx(1.0)


def test_no_overlap() -> None:
    box_a = (10, 10, 50, 50)
    box_b = (100, 100, 150, 150)

    result = calculate_iou(box_a, box_b)

    assert result == pytest.approx(0.0)


def test_partial_overlap() -> None:
    box_a = (10, 10, 100, 100)
    box_b = (50, 50, 150, 150)

    result = calculate_iou(box_a, box_b)

    assert 0.0 < result < 1.0


def test_zero_area_box() -> None:
    box_a = (10, 10, 10, 100)
    box_b = (20, 20, 100, 100)

    result = calculate_iou(box_a, box_b)

    assert result == pytest.approx(0.0)