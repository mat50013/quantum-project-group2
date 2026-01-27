from typing import Dict, Tuple

def count_y_bases(bases: Dict[str, str]) -> int:
    return sum(1 for b in bases.values() if b == "Y")

def is_valid_round(bases: Dict[str, str]) -> bool:
    y_count = count_y_bases(bases)
    return y_count % 2 == 0

def check_ghz_parity(bases: Dict[str, str], outcomes: Dict[str, int]) -> bool:
    if not is_valid_round(bases):
        return False
    eigenvalues = []
    for name in bases.keys():
        outcome = outcomes[name]
        if isinstance(outcome, (list, tuple)):
            outcome = outcome[0]
        eigenvalues.append(1 if outcome == 0 else -1)
    product = 1
    for ev in eigenvalues:
        product *= ev
    y_count = count_y_bases(bases)
    expected_product = (-1) ** (y_count // 2)
    return product == expected_product


def reconstruct_dealer_secret(bases: Dict[str, str], outcomes: Dict[str, int], dealer_name: str) -> int:
    if not is_valid_round(bases):
        return None

    recipient_outcomes = []
    for name, outcome in outcomes.items():
        if name != dealer_name:
            val = outcome[0] if isinstance(outcome, (list, tuple)) else outcome
            recipient_outcomes.append(val)

    reconstructed = 0
    for val in recipient_outcomes:
        reconstructed ^= val

    y_count = count_y_bases(bases)
    if (y_count // 2) % 2 == 1:
        reconstructed ^= 1

    return reconstructed


def verify_secret_sharing(bases: Dict[str, str], outcomes: Dict[str, int], dealer_name: str) -> Tuple[bool, int, int]:
    if not is_valid_round(bases):
        return False, None, None

    dealer_outcome = outcomes[dealer_name]
    actual = dealer_outcome[0] if isinstance(dealer_outcome, (list, tuple)) else dealer_outcome

    reconstructed = reconstruct_dealer_secret(bases, outcomes, dealer_name)
    success = (reconstructed == actual)
    return success, reconstructed, actual