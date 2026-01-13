import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, x=0, y=0):
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
            # Create GHZ state |000⟩ + |111⟩ shared between Alice, Bob, Charlie
            # Alice receives her qubit from the GHZ state creation
            q, m = create_ghz(
                up_epr_socket=epr_socket,
                up_socket=socket_bob,
                do_corrections=True  # Apply corrections automatically for perfect GHZ state
            )

            # Alice randomly chooses measurement basis (X or Y)
            basis = random.choice(['X', 'Y'])

            # Apply basis rotation gates before measurement
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

            # Perform measurement (in computational basis after rotation)
            result = q.measure()
            alice.flush()  # Execute all queued quantum operations
            outcome = int(result)

            # Send Alice's basis choice and measurement outcome to Bob
            socket_bob.send(basis)
            socket_bob.send(str(outcome))

            # Receive Bob's and Charlie's basis choices and outcomes
            # Bob acts as coordinator and relays Charlie's information
            bob_basis = socket_bob.recv()
            bob_outcome = int(socket_bob.recv())
            charlie_basis = socket_bob.recv()
            charlie_outcome = int(socket_bob.recv())

            # Check if this round is valid for secret sharing
            # Count how many parties measured in Y basis
            y_count = [basis, bob_basis, charlie_basis].count('Y')
            all_bases.append(f"{basis}{bob_basis}{charlie_basis}")

            # Only keep rounds with even number of Y measurements
            # This is based on GHZ state correlation properties
            if y_count % 2 == 0:
                # Check parity of measurement outcomes
                # XOR all three outcomes to check correlation
                xor_val = outcome ^ bob_outcome ^ charlie_outcome

                # Verify correctness based on GHZ correlations
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

    # Calculate protocol statistics
    valid = len(valid_results)  # Number of rounds with even Y-count
    correct = sum(valid_results)  # Number of rounds with correct correlations

    # QBER (Quantum Bit Error Rate): fraction of valid rounds with errors
    # High QBER indicates presence of eavesdropper or noisy channel
    qber = 1 - (correct / valid) if valid > 0 else 0

    return {
        "role": "alice",
        "num_rounds": num_rounds,
        "valid_rounds": valid,
        "correct": correct,
        "qber": round(qber, 4),
        "key_rate": round(valid / num_rounds, 4)  # Fraction of rounds that were valid
    }

if __name__ == "__main__":
    main()