"""Tests unitaires des dataclasses Member et Loan."""

from bibliotech import Member


def test_member_from_row_converts_active_flag():
    member = Member.from_row(
        ["M004", "David Moreau", "david.moreau@example.com", "standard", "0"]
    )

    assert member == Member(
        id="M004",
        name="David Moreau",
        email="david.moreau@example.com",
        type="standard",
        active=False,
    )


def test_library_loads_members_as_dataclasses(library):
    assert isinstance(library.find_member("M001"), Member)
    assert library.find_member("M001").active is True
