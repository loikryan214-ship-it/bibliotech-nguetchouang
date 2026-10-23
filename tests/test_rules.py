"""Tests unitaires des règles de calcul de pénalité (late_fee)."""

import pytest

from rules import late_fee, loan_days, loan_limit


@pytest.mark.parametrize(
    ("days_late", "kind", "member_type", "price", "expected"),
    [
        pytest.param(
            0, "book", "standard", 20.0, 0.0, id="rendu_a_temps_sans_penalite"
        ),
        pytest.param(
            -3, "dvd", "standard", 20.0, 0.0, id="retard_negatif_sans_penalite"
        ),
        pytest.param(
            10, "book", "standard", 20.0, 5.0, id="livre_50_centimes_par_jour"
        ),
        pytest.param(10, "dvd", "standard", 30.0, 10.0, id="dvd_1_euro_par_jour"),
        pytest.param(
            3, "magazine", "standard", 5.0, 0.6, id="magazine_20_centimes_par_jour"
        ),
        pytest.param(10, "dvd", "student", 30.0, 5.0, id="etudiant_paye_moitie"),
        pytest.param(10, "book", "premium", 20.0, 0.0, id="premium_ne_paye_rien"),
        pytest.param(
            70, "book", "standard", 7.5, 7.5, id="plafonnee_au_prix_du_document"
        ),
        pytest.param(40, "dvd", "student", 9.9, 9.9, id="etudiant_plafonne_au_prix"),
        pytest.param(4, "cd", "standard", 20.0, 2.0, id="type_inconnu_tarif_livre"),
        pytest.param(
            100, "dvd", "premium", 5.0, 0.0, id="premium_gratuit_meme_au_dela_du_prix"
        ),
    ],
)
def test_late_fee_applies_library_rules(days_late, kind, member_type, price, expected):
    assert late_fee(days_late, kind, member_type, price) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("days_late", "kind", "member_type", "expected"),
    [
        pytest.param(3, "magazine", "student", 0.3, id="3x0.20x50%_donne_0.30"),
        pytest.param(3, "magazine", "standard", 0.6, id="3x0.20_donne_0.60"),
        pytest.param(7, "magazine", "student", 0.7, id="7x0.20x50%_donne_0.70"),
    ],
)
def test_late_fee_is_exactly_rounded_to_the_cent(
    days_late, kind, member_type, expected
):
    # Comparaison exacte (==) : pytest.approx accepterait une valeur non arrondie
    # comme 0.30000000000000004.
    assert late_fee(days_late, kind, member_type, 5.0) == expected


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        pytest.param("book", 21, id="livre_21_jours"),
        pytest.param("dvd", 7, id="dvd_7_jours"),
        pytest.param("magazine", 3, id="magazine_3_jours"),
        pytest.param("cd", 21, id="type_inconnu_duree_livre"),
        pytest.param("", 21, id="type_vide_duree_livre"),
    ],
)
def test_loan_days_depends_on_document_kind(kind, expected):
    assert loan_days(kind) == expected


@pytest.mark.parametrize(
    ("member_type", "expected"),
    [
        pytest.param("standard", 3, id="standard_3"),
        pytest.param("student", 5, id="etudiant_5"),
        pytest.param("premium", 8, id="premium_8"),
        pytest.param("vip", 3, id="type_inconnu_limite_standard"),
    ],
)
def test_loan_limit_depends_on_member_type(member_type, expected):
    assert loan_limit(member_type) == expected
