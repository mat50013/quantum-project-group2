import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

# Here Bob is dishonest by receiving Alice and Charlie's basis and measurement outcome before measuring his own, and then to force the parity
# We could also be dishonest by sending imperfect GHZ states, or tamper with forwarded messages by flipping, or just simply by lying about his own basis or measurement outcome
def main(app_config=None, num_rounds=50, x=0, y=0):
    # Initialize classical communication sockets
    socket_alice = Socket("bob", "alice", log_config=app_config.log_config)
    socket_charlie = Socket("bob", "charlie", log_config=app_config.log_config)

    # Initialize quantum EPR sockets for entanglement with Alice and Charlie
    epr_alice = EPRSocket("alice")
    epr_charlie = EPRSocket("charlie")

    # Create NetQASM connection for quantum operations
    bob = NetQASMConnection(
        "bob",
        log_config=app_config.log_config,
        epr_sockets=[epr_alice, epr_charlie]
    )

    with bob:
        for _ in range(num_rounds):
            # Create GHZ state |000⟩ + |111⟩
            # Bob is the coordinator who generates the GHZ state
            # and distributes qubits to Alice and Charlie
            q, m = create_ghz(
                down_epr_socket=epr_alice,    # EPR pair with Alice
                up_epr_socket=epr_charlie,    # EPR pair with Charlie
                down_socket=socket_alice,     # Classical channel to Alice
                up_socket=socket_charlie,     # Classical channel to Charlie
                do_corrections=True           # Apply corrections for perfect GHZ
            )

            # Receive Alice's basis and measurement outcome
            alice_basis = socket_alice.recv()
            alice_outcome = int(socket_alice.recv())

            # Receive Charlie's basis and measurement outcome
            charlie_basis = socket_charlie.recv()
            charlie_outcome = int(socket_charlie.recv())
            
            # Choose our basis to control even/odd Y-count
            k = [alice_basis, charlie_basis].count('Y')

            # Decide whether to force "even Y" this round, to sift out rounds to keep randomness
            force_even = (random.random() < 0.5)

            if force_even:
                # Make total Y even: if k is even -> choose X; if k is odd -> choose Y
                basis = 'X' if (k % 2 == 0) else 'Y'
            else:
                # Make total Y odd: if k is even -> choose Y; if k is odd -> choose X
                basis = 'Y' if (k % 2 == 0) else 'X'

            # Apply basis rotation gates before measurement
            if basis == 'X':
                # H gate: Rotates Z-basis to X-basis
                # Transforms: |0⟩ → |+⟩, |1⟩ → |-⟩
                q.H()
            else:
                # Y-basis: S† followed by H
                # S† = Rz(-π/2): applies phase rotation
                # Combined effect: rotates to Y-basis
                # Transforms: |0⟩ → |+i⟩, |1⟩ → |-i⟩
                q.rot_Z(angle=-math.pi/2)
                q.H()

            # Perform measurement in computational basis
            # After basis rotation, this effectively measures X or Y observable
            result = q.measure()
            bob.flush()  # Execute all queued quantum operations
            outcome = int(result)

            # Compute total Y-count as announced (includes our chosen basis)
            total_y = [alice_basis, charlie_basis, basis].count('Y')

            # Expected XOR parity for valid (even-Y) rounds:
            #  0 if total_y == 0 (XXX)
            #  1 if total_y == 2 (XYY/YXY/YYX)
            # If total_y is odd, Alice/Charlie will discard the round anyway,
            # but we still announce something consistent.
            if total_y == 0:
                expected_parity = 0
            elif total_y == 2:
                expected_parity = 1
            else:
                # Odd-Y: their sift will drop the round; parity doesn't matter.
                # We can keep it self-consistent anyway:
                expected_parity = (alice_outcome ^ charlie_outcome ^ outcome)

            # Choose our *announced* outcome to satisfy the parity rule:
            # alice ^ bob ^ charlie == expected_parity  ->  bob = expected_parity ^ alice ^ charlie
            announced_outcome = expected_parity ^ alice_outcome ^ charlie_outcome

            # Bob acts as coordinator - relay information between parties
            # Each party needs to know all three basis choices and outcomes
            # to perform the parity check and verify GHZ correlations

            # Send Bob's info and Charlie's info to Alice
            socket_alice.send(basis)
            socket_alice.send(str(announced_outcome))
            socket_alice.send(charlie_basis)
            socket_alice.send(str(charlie_outcome))

            # Send Bob's info and Alice's info to Charlie
            socket_charlie.send(basis)
            socket_charlie.send(str(announced_outcome))
            socket_charlie.send(alice_basis)
            socket_charlie.send(str(alice_outcome))

    return {
        "role": "bob",
        "num_rounds": num_rounds
    }

if __name__ == "__main__":
    main()