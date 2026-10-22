"""Tests unitaires des règles de calcul de pénalité (late_fee)."""

import pytest

from rules import late_fee


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
        pytest.param(3, "magazine", "student", 5.0, 0.3, id="arrondie_au_centime"),
    ],
)
def test_late_fee_applies_library_rules(days_late, kind, member_type, price, expected):
    assert late_fee(days_late, kind, member_type, price) == pytest.approx(expected)


def test_late_fee_is_rounded_to_the_cent():
    fee = late_fee(3, "magazine", "student", 5.0)

    assert fee == round(fee, 2)
