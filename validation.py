# ========== validation.py - Updated with secret sharing ==========

def is_valid_hbb99_round(bases):
    """Check if basis combination is valid for HBB99"""
    combo = (bases["Alice"], bases["Bob"], bases["Charlie"])
    return combo in [
        ("X", "X", "X"),
        ("X", "Y", "Y"),
        ("Y", "X", "Y"),
        ("Y", "Y", "X")
    ]

def check_hbb99_parity(bases, outcomes):
    """
    Verify GHZ correlation with correct parity rules.
    
    For GHZ state |000⟩ + |111⟩:
    - Measurement outcomes are ±1
    - For X measurements: eigenvalues are ±1
    - For Y measurements: eigenvalues are ±1
    
    Expected correlations (product of outcomes):
    - XXX: A × B × C = +1 (even number of -1s)
    - XYY: A × B × C = -1 (odd number of -1s)
    - YXY: A × B × C = -1 (odd number of -1s)
    - YYX: A × B × C = -1 (odd number of -1s)
    """
    
    # Extract values from lists if needed
    alice_outcome = outcomes["Alice"][0] if isinstance(outcomes["Alice"], list) else outcomes["Alice"]
    bob_outcome = outcomes["Bob"][0] if isinstance(outcomes["Bob"], list) else outcomes["Bob"]
    charlie_outcome = outcomes["Charlie"][0] if isinstance(outcomes["Charlie"], list) else outcomes["Charlie"]
    
    # Convert from computational basis (0,1) to eigenvalues (+1,-1)
    # 0 -> +1, 1 -> -1
    alice_val = 1 if alice_outcome == 0 else -1
    bob_val = 1 if bob_outcome == 0 else -1
    charlie_val = 1 if charlie_outcome == 0 else -1
    
    # Get the basis combination
    combo = (bases["Alice"], bases["Bob"], bases["Charlie"])
    
    # Calculate the product of all three outcomes
    product = alice_val * bob_val * charlie_val
    
    # Expected product for each valid combination
    if combo == ("X", "X", "X"):
        expected_product = +1  # Even parity
    elif combo in [("X", "Y", "Y"), ("Y", "X", "Y"), ("Y", "Y", "X")]:
        expected_product = -1  # Odd parity
    else:
        # This shouldn't happen if is_valid_hbb99_round was called first
        return False
    
    return product == expected_product


def reconstruct_alice_secret(bases, bob_outcome, charlie_outcome):
    """
    Bob and Charlie work together to reconstruct Alice's measurement outcome.
    
    This demonstrates the SECRET SHARING property of HBB99:
    - Neither Bob nor Charlie alone can determine Alice's outcome
    - But together, they can reconstruct it perfectly (in valid rounds)
    
    Args:
        bases: Dictionary with basis choices for all parties
        bob_outcome: Bob's measurement outcome (0 or 1)
        charlie_outcome: Charlie's measurement outcome (0 or 1)
    
    Returns:
        Reconstructed Alice outcome (0 or 1)
    """
    # Extract values from lists if needed
    bob_val = bob_outcome[0] if isinstance(bob_outcome, list) else bob_outcome
    charlie_val = charlie_outcome[0] if isinstance(charlie_outcome, list) else charlie_outcome
    
    combo = (bases["Alice"], bases["Bob"], bases["Charlie"])
    
    # Apply the secret sharing formula based on basis combination
    if combo == ("X", "X", "X"):
        # For XXX: Alice = Bob ⊕ Charlie
        alice_reconstructed = bob_val ^ charlie_val
    elif combo in [("X", "Y", "Y"), ("Y", "X", "Y"), ("Y", "Y", "X")]:
        # For XYY, YXY, YYX: Alice = Bob ⊕ Charlie ⊕ 1
        alice_reconstructed = bob_val ^ charlie_val ^ 1
    else:
        # Invalid combination
        return None
    
    return alice_reconstructed


def verify_secret_sharing(bases, outcomes):
    """
    Verify that Bob and Charlie can correctly reconstruct Alice's secret.
    
    Returns:
        (success: bool, reconstructed: int, actual: int)
    """
    # Extract actual Alice outcome
    alice_actual = outcomes["Alice"][0] if isinstance(outcomes["Alice"], list) else outcomes["Alice"]
    
    # Bob and Charlie reconstruct Alice's outcome
    alice_reconstructed = reconstruct_alice_secret(bases, outcomes["Bob"], outcomes["Charlie"])
    
    if alice_reconstructed is None:
        return False, None, alice_actual
    
    # Check if reconstruction matches actual
    success = (alice_reconstructed == alice_actual)
    
    return success, alice_reconstructed, alice_actual