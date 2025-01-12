from unittest.mock import patch

import pytest
from fakeredis import FakeRedis

from search.knn_search import KNNSearch


@pytest.fixture
def redis_mock():
    return FakeRedis()


def parse_and_sanitize_input():
    input = " dogs cats frogs@"

    sanitized_input = parse_and_sanitize_input()

    assert input == sanitized_input


def knn_search_mock(redis_mock):
    pass


@patch.object(KNNSearch, "__init__", knn_search_mock)
def test_dedup(redis_mock):
    result_list = [
        KNNSearch.BookEntries(0.888, "dogs", "lassie", "http://", 10),
        KNNSearch.BookEntries(0.666, "dogs", "lassie", "http://", 20),
        KNNSearch.BookEntries(0.777, "cats", "hello kitty", "http://", 30),
        KNNSearch.BookEntries(0.666, "birds", "big bird", "http://", 40),
    ]
    expected_list = [
        KNNSearch.BookEntries(0.888, "dogs", "lassie", "http://", 10),
        KNNSearch.BookEntries(0.777, "cats", "hello kitty", "http://", 30),
        KNNSearch.BookEntries(0.666, "birds", "big bird", "http://", 40),
    ]

    rescore = KNNSearch().dedup_by_number_of_reviews(result_list)
    assert rescore == expected_list


@patch.object(KNNSearch, "__init__", knn_search_mock)
def test_skip_dedup(redis_mock):
    result_list = [
        KNNSearch.BookEntries(0.888, "dogs", "lassie", "http://", 10),
        KNNSearch.BookEntries(0.777, "cats", "hello kitty", "http://", 30),
        KNNSearch.BookEntries(0.666, "dogs", "lassie", "http://", 20),
        KNNSearch.BookEntries(0.666, "birds", "big bird", "http://", 40),
    ]
    expected_list = [
        KNNSearch.BookEntries(0.888, "dogs", "lassie", "http://", 10),
        KNNSearch.BookEntries(0.777, "cats", "hello kitty", "http://", 30),
        KNNSearch.BookEntries(0.666, "birds", "big bird", "http://", 40),
    ]

    rescore = KNNSearch().dedup_by_number_of_reviews(result_list)
    assert rescore == expected_list
