from typing import Dict, List, Tuple
from itertools import product

def count_y_bases(bases: Dict[str, str]) -> int:
    """Count number of Y basis measurements."""
    return sum(1 for b in bases.values() if b == "Y")

def is_valid_round(bases: Dict[str, str]) -> bool:
    """
    Check if basis combination is valid for n-party GHZ protocol.

    Valid combinations: total number of Y measurements is EVEN (0, 2, 4, ...)
    This ensures the measurement outcomes have deterministic correlations.

    Args:
        bases: Dict mapping party names to their basis choice ("X" or "Y")

    Returns:
        True if valid, False otherwise
    """
    y_count = count_y_bases(bases)
    return y_count % 2 == 0


def check_ghz_parity(bases: Dict[str, str], outcomes: Dict[str, int]) -> bool:
    """
    Verify GHZ correlation (parity check) for n parties.

    For n-party GHZ state with valid basis combinations:
    - All X (Y_count = 0): Product of outcomes = +1
    - Two Y (Y_count = 2): Product of outcomes = -1
    - Four Y (Y_count = 4): Product of outcomes = +1
    - General: Product = (-1)^(Y_count / 2)

    Args:
        bases: Dict mapping party names to basis choices
        outcomes: Dict mapping party names to measurement outcomes (0 or 1)

    Returns:
        True if parity check passes, False otherwise
    """
    if not is_valid_round(bases):
        return False

    # Convert outcomes from (0,1) to eigenvalues (+1,-1)
    # 0 -> +1, 1 -> -1
    eigenvalues = []
    for name in bases.keys():
        outcome = outcomes[name]
        if isinstance(outcome, (list, tuple)):
            outcome = outcome[0]
        eigenvalues.append(1 if outcome == 0 else -1)

    # Calculate product of all eigenvalues
    product = 1
    for ev in eigenvalues:
        product *= ev

    # Expected product based on number of Y measurements
    y_count = count_y_bases(bases)
    expected_product = (-1) ** (y_count // 2)

    return product == expected_product


def reconstruct_dealer_secret(bases: Dict[str, str],
                              outcomes: Dict[str, int],
                              dealer_name: str) -> int:
    """
    Recipients collaborate to reconstruct dealer's measurement outcome.

    This demonstrates the SECRET SHARING property:
    - No single recipient can determine dealer's outcome
    - All recipients together can reconstruct it perfectly

    For n-party GHZ with valid bases:
    - XOR all recipient outcomes
    - Apply correction based on Y count: if (Y_count/2) is odd, flip result

    Args:
        bases: Dict of all party bases
        outcomes: Dict of all party outcomes
        dealer_name: Name of the dealer

    Returns:
        Reconstructed dealer outcome (0 or 1)
    """
    if not is_valid_round(bases):
        return None

    # Get recipient outcomes (everyone except dealer)
    recipient_outcomes = []
    for name, outcome in outcomes.items():
        if name != dealer_name:
            val = outcome[0] if isinstance(outcome, (list, tuple)) else outcome
            recipient_outcomes.append(val)

    # XOR all recipient outcomes
    reconstructed = 0
    for val in recipient_outcomes:
        reconstructed ^= val

    # Apply correction based on Y count
    y_count = count_y_bases(bases)
    if (y_count // 2) % 2 == 1:
        reconstructed ^= 1

    return reconstructed


def verify_secret_sharing(bases: Dict[str, str],
                          outcomes: Dict[str, int],
                          dealer_name: str) -> Tuple[bool, int, int]:
    """
    Verify that recipients can correctly reconstruct dealer's secret.

    Args:
        bases: Dict of all party bases
        outcomes: Dict of all party outcomes
        dealer_name: Name of the dealer

    Returns:
        (success, reconstructed_value, actual_value)
    """
    if not is_valid_round(bases):
        return False, None, None

    # Get dealer's actual outcome
    dealer_outcome = outcomes[dealer_name]
    actual = dealer_outcome[0] if isinstance(dealer_outcome, (list, tuple)) else dealer_outcome

    # Reconstruct using recipient outcomes
    reconstructed = reconstruct_dealer_secret(bases, outcomes, dealer_name)

    success = (reconstructed == actual)
    return success, reconstructed, actual


def get_valid_basis_combinations(n_parties: int) -> List[Tuple[str, ...]]:
    """
    Generate all valid basis combinations for n parties.

    Valid = even number of Y measurements.

    Args:
        n_parties: Number of parties

    Returns:
        List of valid basis tuples
    """
    all_combos = list(product(["X", "Y"], repeat=n_parties))
    valid = [combo for combo in all_combos if combo.count("Y") % 2 == 0]
    return valid


def print_validation_info(n_parties: int):
    """Print information about valid combinations for n parties."""
    valid = get_valid_basis_combinations(n_parties)
    total = 2 ** n_parties

    print(f"\n{'='*50}")
    print(f"Validation info for {n_parties}-party GHZ protocol")
    print(f"{'='*50}")
    print(f"Total basis combinations: {total}")
    print(f"Valid combinations: {len(valid)} ({len(valid)/total*100:.1f}%)")
    print(f"\nValid combinations (even # of Y):")

    for combo in valid[:10]:  # Show first 10
        y_count = combo.count("Y")
        print(f"  {combo} (Y count: {y_count})")

    if len(valid) > 10:
        print(f"  ... and {len(valid) - 10} more")

    print(f"{'='*50}\n")