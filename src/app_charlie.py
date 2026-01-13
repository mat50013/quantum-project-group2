import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, x=0, y=0):
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
            # Receive Charlie's qubit from the GHZ state
            # Bob coordinates the GHZ state creation
            # The GHZ state is: |000⟩ + |111⟩ (entangled across Alice, Bob, Charlie)
            q, m = create_ghz(
                down_epr_socket=epr_socket,
                down_socket=socket_bob,
                do_corrections=True  # Apply corrections for perfect GHZ state
            )

            # Charlie randomly chooses measurement basis (X or Y)
            basis = random.choice(['X', 'Y'])

            # Apply basis rotation gates before measurement
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

            # Perform measurement in computational basis
            # After the basis rotation, this effectively measures in X or Y basis
            result = q.measure()
            charlie.flush()  # Execute all queued quantum operations
            outcome = int(result)

            # Send Charlie's basis choice and measurement outcome to Bob
            socket_bob.send(basis)
            socket_bob.send(str(outcome))

            # Receive Bob's and Alice's basis choices and outcomes
            # Bob acts as coordinator and relays Alice's information to Charlie
            bob_basis = socket_bob.recv()
            bob_outcome = int(socket_bob.recv())
            alice_basis = socket_bob.recv()
            alice_outcome = int(socket_bob.recv())

            # Basis sifting - check if this round is valid for secret sharing
            # Count how many parties measured in Y basis (vs X basis)
            y_count = [alice_basis, bob_basis, basis].count('Y')

            # Only process rounds with EVEN number of Y measurements
            if y_count % 2 == 0:
                # Check parity of measurement outcomes
                xor_val = alice_outcome ^ bob_outcome ^ outcome

                # Verify correctness based on GHZ state correlation rules
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
        "valid_rounds": valid,
        "correct": correct,
        "qber": round(qber, 4)
    }

if __name__ == "__main__":
    main()