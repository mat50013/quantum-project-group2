import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, eve_present=0, x=0, y=0):
    """
    Charlie's role in HBB99 Quantum Secret Sharing protocol using GHZ states.
    
    Args:
        app_config: NetQASM application configuration
        num_rounds: Number of QSS rounds to execute
        eve_present: If True, Eve intercepts and measures all qubits
        x, y: Unused parameters for compatibility
    
    Returns:
        Dictionary with protocol statistics including QBER
    """
    # Initialize classical communication socket with Bob (coordinator)
    socket_bob = Socket("charlie", "bob", log_config=app_config.log_config)

    # Initialize quantum EPR socket for entanglement generation with Bob
    epr_socket = EPRSocket("bob")

    # Create NetQASM connection for quantum operations
    charlie = NetQASMConnection(
        "charlie",
        log_config=app_config.log_config,
        epr_sockets=[epr_socket]
    )

    valid_results = []  # Store correctness of each valid round (1=correct, 0=error)

    with charlie:
        for _ in range(num_rounds):
            # Step 1: Receive Charlie's qubit from the GHZ state
            # Bob coordinates the GHZ state creation
            # The GHZ state is: |000⟩ + |111⟩ (entangled across Alice, Bob, Charlie)
            q, m = create_ghz(
                down_epr_socket=epr_socket,
                down_socket=socket_bob,
                do_corrections=True  # Apply corrections for perfect GHZ state
            )

            # Step 2: Charlie randomly chooses measurement basis (X or Y)
            basis = random.choice(['X', 'Y'])

            # Step 3: Apply basis rotation gates before measurement
            if basis == 'X':
                # H gate: Rotates Z-basis to X-basis
                # Measures X observable: |+⟩ → 0, |-⟩ → 1
                q.H()
            elif basis == 'Y':
                # Y-basis: S† (phase gate) followed by H
                # S† = Rz(-π/2): rotates phase by -90 degrees
                # Combined: rotates to Y-basis
                # Measures Y observable: |+i⟩ → 0, |-i⟩ → 1
                q.rot_Z(angle=-math.pi/2)
                q.H()

            # Step 4: Perform measurement in computational basis
            # After the basis rotation, this effectively measures in X or Y basis
            result = q.measure()
            charlie.flush()  # Execute all queued quantum operations
            outcome = int(result)

            # Step 5: Simulate Eve's intercept-resend attack (if present)
            if eve_present:
                # Eve intercepts Charlie's qubit before it reaches Charlie
                # She measures in a random basis, destroying the GHZ correlations
                eve_basis = random.choice(['X', 'Y'])

                # When Eve's basis differs from Charlie's, she has ~50% chance
                # of measuring the wrong value, which she then forwards to Charlie
                # This causes Charlie to measure an incorrect correlated value
                if eve_basis != basis and random.random() < 0.5:
                    outcome = 1 - outcome  # Eve causes a bit flip error

            # Step 6: Send Charlie's basis choice and measurement outcome to Bob
            socket_bob.send(basis)
            socket_bob.send(str(outcome))

            # Step 7: Receive Bob's and Alice's basis choices and outcomes
            # Bob acts as coordinator and relays Alice's information to Charlie
            bob_basis = socket_bob.recv()
            bob_outcome = int(socket_bob.recv())
            alice_basis = socket_bob.recv()
            alice_outcome = int(socket_bob.recv())

            # Step 8: Basis sifting - check if this round is valid for secret sharing
            # Count how many parties measured in Y basis (vs X basis)
            y_count = [alice_basis, bob_basis, basis].count('Y')

            # Step 9: Only process rounds with EVEN number of Y measurements
            if y_count % 2 == 0:
                # Step 10: Check parity of measurement outcomes
                xor_val = alice_outcome ^ bob_outcome ^ outcome

                # Step 11: Verify correctness based on GHZ state correlation rules
                # For the GHZ state |000⟩ + |111⟩:
                if y_count == 0:
                    is_correct = (xor_val == 0)
                else:
                    is_correct = (xor_val == 1)

                # Record whether this round matched the expected correlation
                # 1 = correct correlation (no eavesdropper/noise detected)
                # 0 = incorrect correlation (possible Eve or channel noise)
                valid_results.append(1 if is_correct else 0)

    # Step 12: Calculate protocol statistics
    valid = len(valid_results)      # Number of rounds with even Y-count (usable rounds)
    correct = sum(valid_results)    # Number of rounds with correct GHZ correlations

    qber = 1 - (correct / valid) if valid > 0 else 0

    return {
        "role": "charlie",
        "num_rounds": num_rounds,
        "eve_present": eve_present,
        "valid_rounds": valid,
        "correct": correct,
        "qber": round(qber, 4)
    }

if __name__ == "__main__":
    main()