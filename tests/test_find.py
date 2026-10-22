"""Tests unitaires de la recherche par identifiant (find_by_id et find_*)."""

from types import SimpleNamespace

from bibliotech import find_by_id


def test_find_by_id_returns_the_matching_record():
    items = [SimpleNamespace(id="A1"), SimpleNamespace(id="B2")]

    assert find_by_id(items, "B2") is items[1]


def test_find_by_id_returns_none_when_absent():
    assert find_by_id([SimpleNamespace(id="A1")], "Z9") is None


def test_library_finds_book_member_and_loan_by_id(library):
    assert library.find_book("B001").title == "Dune"
    assert library.find_member("M005").name == "Emma Laurent"
    assert library.find_loan("L004").book_id == "B006"


def test_library_returns_none_for_unknown_ids(library):
    assert library.find_book("B999") is None
    assert library.find_member("M999") is None
    assert library.find_loan("L999") is None
