import netsquid as ns
from party_protocols import HBB99PartyProtocol
from validation import is_valid_hbb99_round, check_hbb99_parity, verify_secret_sharing, reconstruct_alice_secret

def run_hbb99_with_eve(n_rounds, with_eve=True, intercept_target="Bob", verbose=False):
    """
    Run HBB99 protocol with or without Eve
    
    Args:
        n_rounds: Number of rounds to run
        with_eve: If True, use Eve's intercept-resend attack
        intercept_target: "Bob" or "Charlie" - who Eve intercepts
        verbose: If True, print detailed round-by-round info
    """
    if with_eve:
        # Import network with Eve
        from network import Alice, Bob, Charlie, Eve
        from eve import distribute_ghz_with_eve
        print("\n" + "="*60)
        print(f"RUNNING HBB99 WITH EVE INTERCEPTING {intercept_target.upper()}'S QUBIT")
        print("="*60)
    else:
        # Import normal network
        from network import Alice, Bob, Charlie
        from ghz_resource import distribute_ghz_state
        print("\n" + "="*60)
        print("RUNNING HBB99 WITHOUT EVE (BASELINE)")
        print("="*60)
    
    valid_rounds = 0
    passed_rounds = 0
    secret_sharing_successes = 0
    
    for i in range(n_rounds):
        if not verbose and (i + 1) % 10 == 0:
            print(f"Round {i+1}/{n_rounds}...")
        
        # Reset simulation
        ns.sim_reset()
        Alice.subcomponents["memory1"].reset()
        Bob.subcomponents["memory1"].reset()
        Charlie.subcomponents["memory1"].reset()
        
        if with_eve:
            Eve.subcomponents["memory1"].reset()
            distribute_ghz_with_eve(Eve, intercept_target=intercept_target)
        else:
            distribute_ghz_state()
        
        # Create and start party protocols
        alice_protocol = HBB99PartyProtocol(Alice, "Alice", ["Bob", "Charlie"])
        bob_protocol = HBB99PartyProtocol(Bob, "Bob", ["Alice", "Charlie"])
        charlie_protocol = HBB99PartyProtocol(Charlie, "Charlie", ["Alice", "Bob"])
        
        alice_protocol.start()
        bob_protocol.start()
        charlie_protocol.start()
        ns.sim_run(duration=1000)
        
        # Collect bases
        bases = {
            "Alice": alice_protocol.basis,
            "Bob": bob_protocol.basis,
            "Charlie": charlie_protocol.basis
        }
        
        # Check if round is valid
        if is_valid_hbb99_round(bases):
            valid_rounds += 1
            
            # Collect outcomes
            outcomes = {
                "Alice": alice_protocol.outcome,
                "Bob": bob_protocol.outcome,
                "Charlie": charlie_protocol.outcome
            }
            
            # Check parity
            parity_passed = check_hbb99_parity(bases, outcomes)
            if parity_passed:
                passed_rounds += 1
            
            # Verify secret sharing
            ss_success, alice_reconstructed, alice_actual = verify_secret_sharing(bases, outcomes)
            if ss_success:
                secret_sharing_successes += 1
            
            if verbose:
                print(f"\n--- Round {i+1} (Valid: {bases}) ---")
                print(f"Alice outcome: {alice_actual}")
                print(f"Bob outcome: {outcomes['Bob'][0]}")
                print(f"Charlie outcome: {outcomes['Charlie'][0]}")
                print(f"Bob & Charlie reconstruct Alice's bit: {alice_reconstructed}")
                print(f"Reconstruction {'✅ SUCCESS' if ss_success else '❌ FAILED'}")
                print(f"Parity check: {'✅ PASSED' if parity_passed else '❌ FAILED'}")
    
    # Calculate results
    error_rounds = valid_rounds - passed_rounds
    qber = (error_rounds / valid_rounds * 100) if valid_rounds > 0 else 0
    ss_rate = (secret_sharing_successes / valid_rounds * 100) if valid_rounds > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"RESULTS {'WITH EVE' if with_eve else 'WITHOUT EVE'}")
    print(f"{'='*60}")
    print(f"Total rounds: {n_rounds}")
    print(f"Valid rounds: {valid_rounds} ({valid_rounds/n_rounds*100:.1f}%)")
    print(f"\n--- Security Check (Parity) ---")
    print(f"Passed parity check: {passed_rounds}/{valid_rounds}")
    print(f"Failed parity check: {error_rounds}/{valid_rounds}")
    print(f"QBER: {qber:.2f}%")
    print(f"\n--- Secret Sharing ---")
    print(f"Successful reconstructions: {secret_sharing_successes}/{valid_rounds} ({ss_rate:.1f}%)")
    print('='*60)
    
    if with_eve:
        print(f"\n💡 Expected with Eve:")
        print(f"   - QBER: ~25% (Eve disrupts correlations)")
        print(f"   - Secret sharing: ~50% (Eve breaks some reconstructions)")
    else:
        print("\n💡 Expected without Eve:")
        print("   - QBER: ~0% (Perfect correlations)")
        print("   - Secret sharing: 100% (Perfect reconstructions)")
    
    return {
        "total_rounds": n_rounds,
        "valid_rounds": valid_rounds,
        "passed_rounds": passed_rounds,
        "error_rounds": error_rounds,
        "qber": qber,
        "secret_sharing_successes": secret_sharing_successes,
        "secret_sharing_rate": ss_rate,
        "with_eve": with_eve
    }


def compare_with_and_without_eve(n_rounds, intercept_target="Bob", verbose=False):
    """
    Run comparison between baseline and Eve attack
    
    Args:
        n_rounds: Number of rounds
        intercept_target: "Bob" or "Charlie" - who Eve intercepts
        verbose: Show detailed round info
    """
    
    print("\n" + "="*70)
    print("COMPARING HBB99: BASELINE vs EVE ATTACK")
    print("="*70)
    
    # Run without Eve
    results_no_eve = run_hbb99_with_eve(n_rounds=n_rounds, with_eve=False, verbose=verbose)
    
    print("\n" + "-"*70 + "\n")
    
    # Run with Eve
    results_with_eve = run_hbb99_with_eve(n_rounds=n_rounds, with_eve=True, 
                                          intercept_target=intercept_target, verbose=verbose)
    
    # Summary comparison
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print(f"{'Scenario':<25} {'QBER':>10} {'Secret Sharing':>15} {'Security':>15}")
    print("-"*70)
    print(f"{'Without Eve':<25} {results_no_eve['qber']:>9.2f}% "
          f"{results_no_eve['secret_sharing_rate']:>14.1f}% {'✅ SECURE':>15}")
    print(f"{'With Eve':<25} {results_with_eve['qber']:>9.2f}% "
          f"{results_with_eve['secret_sharing_rate']:>14.1f}% {'⚠️  COMPROMISED':>15}")
    print("="*70)
    print(f"\nQBER increase due to Eve: {results_with_eve['qber'] - results_no_eve['qber']:.2f}%")
    print(f"Secret sharing degradation: {results_no_eve['secret_sharing_rate'] - results_with_eve['secret_sharing_rate']:.1f}%")
    

def demo_secret_sharing_single_round():
    """
    Demonstrate secret sharing in detail for a single round
    """
    from network import Alice, Bob, Charlie
    from ghz_resource import distribute_ghz_state
    
    print("\n" + "="*70)
    print("DEMONSTRATION: SECRET SHARING IN HBB99")
    print("="*70)
    print("\nThis shows how Bob and Charlie can reconstruct Alice's measurement,")
    print("but neither can do it alone - they MUST cooperate!")
    print("="*70)
    
    ns.sim_reset()
    Alice.subcomponents["memory1"].reset()
    Bob.subcomponents["memory1"].reset()
    Charlie.subcomponents["memory1"].reset()
    
    distribute_ghz_state()
    
    alice_protocol = HBB99PartyProtocol(Alice, "Alice", ["Bob", "Charlie"])
    bob_protocol = HBB99PartyProtocol(Bob, "Bob", ["Alice", "Charlie"])
    charlie_protocol = HBB99PartyProtocol(Charlie, "Charlie", ["Alice", "Bob"])
    
    alice_protocol.start()
    bob_protocol.start()
    charlie_protocol.start()
    ns.sim_run(duration=1000)
    
    bases = {
        "Alice": alice_protocol.basis,
        "Bob": bob_protocol.basis,
        "Charlie": charlie_protocol.basis
    }
    
    outcomes = {
        "Alice": alice_protocol.outcome,
        "Bob": bob_protocol.outcome,
        "Charlie": charlie_protocol.outcome
    }
    
    alice_val = outcomes["Alice"][0]
    bob_val = outcomes["Bob"][0]
    charlie_val = outcomes["Charlie"][0]
    
    print(f"\nBasis choices: Alice={bases['Alice']}, Bob={bases['Bob']}, Charlie={bases['Charlie']}")
    print(f"Valid round: {'✅ YES' if is_valid_hbb99_round(bases) else '❌ NO'}")
    
    if is_valid_hbb99_round(bases):
        print(f"\nMeasurement outcomes:")
        print(f"  Alice:   {alice_val} (🔒 KEPT SECRET)")
        print(f"  Bob:     {bob_val}")
        print(f"  Charlie: {charlie_val}")
        
        alice_reconstructed = reconstruct_alice_secret(bases, bob_val, charlie_val)
        
        print(f"\n🤝 Bob and Charlie collaborate:")
        combo = (bases["Alice"], bases["Bob"], bases["Charlie"])
        if combo == ("X", "X", "X"):
            print(f"  Formula: Alice = Bob ⊕ Charlie")
            print(f"  Calculation: {bob_val} ⊕ {charlie_val} = {alice_reconstructed}")
        else:
            print(f"  Formula: Alice = Bob ⊕ Charlie ⊕ 1")
            print(f"  Calculation: {bob_val} ⊕ {charlie_val} ⊕ 1 = {alice_reconstructed}")
        
        print(f"\n✨ Reconstructed Alice's bit: {alice_reconstructed}")
        print(f"🎯 Alice's actual bit:        {alice_val}")
        print(f"{'✅ SUCCESS!' if alice_reconstructed == alice_val else '❌ FAILED'}")
        
        
    else:
        print("\n(Discarded round - not valid for secret sharing)")
    
    print("="*70)


if __name__ == "__main__":
    # Run detailed demo of secret sharing
    demo_secret_sharing_single_round()
    
    print("\n\n")
    
    # Run comparison with moderate verbosity
    compare_with_and_without_eve(n_rounds=100, intercept_target="Bob", verbose=False)


    