import numpy as np

from src.models.data import (
    N_FEATURES,
    N_SAMPLES,
    TEST_FRACTION,
    generate_dataset,
    split_dataset,
)


def test_generate_dataset_shape() -> None:
    x, y = generate_dataset(seed=42)
    assert x.shape == (N_SAMPLES, N_FEATURES)
    assert y.shape == (N_SAMPLES,)


def test_generate_dataset_is_deterministic_under_seed() -> None:
    x1, y1 = generate_dataset(seed=42)
    x2, y2 = generate_dataset(seed=42)
    np.testing.assert_array_equal(x1, x2)
    np.testing.assert_array_equal(y1, y2)


def test_generate_dataset_differs_across_seeds() -> None:
    x1, _ = generate_dataset(seed=42)
    x2, _ = generate_dataset(seed=7)
    assert not np.array_equal(x1, x2)


def test_category_column_is_int_valued() -> None:
    x, _ = generate_dataset(seed=42)
    assert np.all(x[:, 2] == np.floor(x[:, 2]))


def test_split_partitions_the_full_dataset() -> None:
    x, y = generate_dataset(seed=42)
    data = split_dataset(x, y, seed=42)
    total = len(data.x_train) + len(data.x_val) + len(data.x_test)
    assert total == N_SAMPLES
    assert len(data.x_test) == int(N_SAMPLES * TEST_FRACTION)
    assert len(data.y_test) == len(data.x_test)


def test_split_is_deterministic_under_seed() -> None:
    x, y = generate_dataset(seed=42)
    a = split_dataset(x, y, seed=42)
    b = split_dataset(x, y, seed=42)
    np.testing.assert_array_equal(a.x_test, b.x_test)
    np.testing.assert_array_equal(a.y_test, b.y_test)
    np.testing.assert_array_equal(a.x_train, b.x_train)
