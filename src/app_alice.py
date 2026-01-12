import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, noise_level=0.0, eve_present=0, x=0, y=0):
    """
    Alice's role in HBB99 Quantum Secret Sharing protocol using GHZ states.

    Args:
        app_config: NetQASM application configuration
        num_rounds: Number of QSS rounds to execute
        noise_level: Probability of bit-flip error on Alice's measurements (0.0-1.0)
        eve_present: If True, Eve intercepts and measures all qubits (intercept-resend attack)
        x, y: Unused parameters for compatibility

    Returns:
        Dictionary with protocol statistics including QBER
    """
    # Initialize classical communication socket with Bob (coordinator)
    socket_bob = Socket("alice", "bob", log_config=app_config.log_config)

    # Initialize quantum EPR socket for entanglement generation with Bob
    epr_socket = EPRSocket("bob")

    # Create NetQASM connection for quantum operations
    alice = NetQASMConnection(
        "alice",
        log_config=app_config.log_config,
        epr_sockets=[epr_socket]
    )

    valid_results = []  # Store correctness of each valid round (1=correct, 0=error)
    all_bases = []  # Store basis choices for all rounds (for analysis)

    with alice:
        for round_num in range(num_rounds):
            # Step 1: Create GHZ state |000⟩ + |111⟩ shared between Alice, Bob, Charlie
            # Alice receives her qubit from the GHZ state creation
            q, m = create_ghz(
                up_epr_socket=epr_socket,
                up_socket=socket_bob,
                do_corrections=True  # Apply corrections automatically for perfect GHZ state
            )

            # Step 2: Alice randomly chooses measurement basis (X or Y)
            basis = random.choice(['X', 'Y'])

            # Step 3: Apply basis rotation gates before measurement
            # We measure in computational (Z) basis after rotation (for some reason here measuring directly into that basis does not work so that's why rotate and after that)
            if basis == 'X':
                # H gate: Rotates Z-basis to X-basis
                # Measures X observable: |+⟩ → 0, |-⟩ → 1
                q.H()
            elif basis == 'Y':
                # S-dagger (not implemented directly in the library) = Rz(-π/2) followed by H: Rotates Z-basis to Y-basis
                # Measures Y observable: |+i⟩ → 0, |-i⟩ → 1
                q.rot_Z(angle=-math.pi/2)
                q.H()

            # Step 4: Perform measurement (in computational basis after rotation)
            result = q.measure()
            alice.flush()  # Execute all queued quantum operations
            outcome = int(result)

            # Step 5: Simulate Eve's intercept-resend attack (if present)
            if eve_present:
                # Eve intercepts the qubit and measures in a random basis
                # This collapses the GHZ state and introduces errors
                eve_basis = random.choice(['X', 'Y'])
                # Eve's measurement destroys correlations ~50% of the time
                # when her basis differs from Alice's basis
                if eve_basis != basis and random.random() < 0.5:
                    outcome = 1 - outcome  # Eve causes bit flip error

            # Step 6: Apply channel noise (bit-flip error model)
            if noise_level > 0 and random.random() < noise_level:
                outcome = 1 - outcome  # Flip the bit with probability noise_level

            # Step 7: Send Alice's basis choice and measurement outcome to Bob
            socket_bob.send(basis)
            socket_bob.send(str(outcome))

            # Step 8: Receive Bob's and Charlie's basis choices and outcomes
            # Bob acts as coordinator and relays Charlie's information
            bob_basis = socket_bob.recv()
            bob_outcome = int(socket_bob.recv())
            charlie_basis = socket_bob.recv()
            charlie_outcome = int(socket_bob.recv())

            # Step 9: Check if this round is valid for secret sharing
            # Count how many parties measured in Y basis
            y_count = [basis, bob_basis, charlie_basis].count('Y')
            all_bases.append(f"{basis}{bob_basis}{charlie_basis}")

            # Only keep rounds with even number of Y measurements
            # This is based on GHZ state correlation properties
            if y_count % 2 == 0:
                # Step 10: Check parity of measurement outcomes
                # XOR all three outcomes to check correlation
                xor_val = outcome ^ bob_outcome ^ charlie_outcome

                # Step 11: Verify correctness based on GHZ correlations
                # For GHZ state |000⟩ + |111⟩:
                if y_count == 0:
                    # All X-basis (XXX): expect even parity (XOR = 0)
                    is_correct = (xor_val == 0)
                else:
                    # Two Y-basis (XYY, YXY, YYX): expect odd parity (XOR = 1)
                    # This follows from GHZ state phase relationships
                    is_correct = (xor_val == 1)

                # Record if this round matched expected correlation
                valid_results.append(1 if is_correct else 0)

    # Step 12: Calculate protocol statistics
    valid = len(valid_results)  # Number of rounds with even Y-count
    correct = sum(valid_results)  # Number of rounds with correct correlations

    # QBER (Quantum Bit Error Rate): fraction of valid rounds with errors
    # High QBER indicates presence of eavesdropper or noisy channel
    qber = 1 - (correct / valid) if valid > 0 else 0

    return {
        "role": "alice",
        "num_rounds": num_rounds,
        "noise_level": noise_level,
        "eve_present": eve_present,
        "valid_rounds": valid,
        "correct": correct,
        "qber": round(qber, 4),
        "key_rate": round(valid / num_rounds, 4)  # Fraction of rounds that were valid
    }

if __name__ == "__main__":
    main()