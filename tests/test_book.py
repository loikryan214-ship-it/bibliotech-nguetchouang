"""Tests unitaires de la dataclass Book."""

import pytest

from bibliotech import Book


def test_book_from_row_converts_csv_fields():
    book = Book.from_row(["B001", "Dune", "Frank Herbert", "book", "12.90", "3"])

    assert book == Book(
        id="B001",
        title="Dune",
        author="Frank Herbert",
        kind="book",
        price=12.9,
        copies=3,
    )


def test_book_from_row_never_evaluates_the_price():
    row = ["B666", "Piege", "X", "book", "__import__('os').getcwd()", "1"]

    with pytest.raises(ValueError):
        Book.from_row(row)


def test_library_loads_books_as_dataclasses(library):
    dune = library.find_book("B001")

    assert isinstance(dune, Book)
    assert dune.copies == 3
