"""Règles métier de BiblioTech : durées, limites et pénalités de retard.

Les valeurs sont celles du README (section « Règles métier »).
"""

# Durée d'emprunt en jours, selon le type de document
LOAN_DAYS = {"book": 21, "dvd": 7, "magazine": 3}
DEFAULT_LOAN_DAYS = LOAN_DAYS["book"]

# Nombre maximum d'emprunts simultanés, selon le type de membre
MAX_LOANS = {"student": 5, "premium": 8}
DEFAULT_MAX_LOANS = 3

# Pénalité par jour de retard (EUR), selon le type de document
DAILY_FEE = {"book": 0.5, "dvd": 1.0, "magazine": 0.2}
DEFAULT_DAILY_FEE = DAILY_FEE["book"]

# Coefficient appliqué à la pénalité, selon le type de membre
FEE_RATE = {"student": 0.5, "premium": 0}
DEFAULT_FEE_RATE = 1


def loan_days(kind: str) -> int:
    """Durée d'emprunt en jours ; un type inconnu suit la règle des livres."""
    return LOAN_DAYS.get(kind, DEFAULT_LOAN_DAYS)


def loan_limit(member_type: str) -> int:
    """Nombre maximum d'emprunts simultanés ; un type inconnu est standard."""
    return MAX_LOANS.get(member_type, DEFAULT_MAX_LOANS)


def late_fee(days_late: int, kind: str, member_type: str, price: float) -> float:
    """Pénalité de retard, réduite selon le membre et plafonnée au prix."""
    if days_late <= 0:
        return 0.0
    fee = days_late * DAILY_FEE.get(kind, DEFAULT_DAILY_FEE)
    fee = fee * FEE_RATE.get(member_type, DEFAULT_FEE_RATE)
    return round(min(fee, price), 2)
