import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, x=0, y=0):
    socket_bob = Socket("alice", "bob", log_config=app_config.log_config)
    epr_socket = EPRSocket("bob")

    alice = NetQASMConnection(
        "alice",
        log_config=app_config.log_config,
        epr_sockets=[epr_socket]
    )

    valid_results = []
    all_bases = []

    with alice:
        for round_num in range(num_rounds):
            # Alice initiates 4-party GHZ: Alice -> Bob -> Charlie -> Diana
            q, m = create_ghz(
                up_epr_socket=epr_socket,
                up_socket=socket_bob,
                do_corrections=True
            )

            # Random X or Y basis measurement
            basis = random.choice(['X', 'Y'])

            if basis == 'X':
                q.H()
            else:
                q.rot_Z(angle=-math.pi/2)
                q.H()

            result = q.measure()
            alice.flush()
            outcome = int(result)

            # Send Alice's basis to Bob (who coordinates)
            socket_bob.send(basis)
            socket_bob.send(str(outcome))

            # Receive all other parties' bases and outcomes
            bob_basis = socket_bob.recv()
            bob_outcome = int(socket_bob.recv())
            charlie_basis = socket_bob.recv()
            charlie_outcome = int(socket_bob.recv())
            diana_basis = socket_bob.recv()
            diana_outcome = int(socket_bob.recv())

            # Count Y-basis measurements
            bases_list = [basis, bob_basis, charlie_basis, diana_basis]
            y_count = bases_list.count('Y')
            all_bases.append(''.join(bases_list))

            # From paper: "If three particles are expressed in one basis
            # and the remaining one in the other, then |w4> is a superposition
            # of all 16 basis vectors. This means that there are no correlations."
            # Valid only when y_count is EVEN (0, 2, or 4)
            if y_count % 2 == 0:
                # XOR all four measurement outcomes
                xor_val = outcome ^ bob_outcome ^ charlie_outcome ^ diana_outcome

                # From paper:
                # - XXXX (y=0): even number of minus → XOR = 0
                # - YYYY (y=4): even number of minus → XOR = 0
                # - Two X + Two Y (y=2): odd number of minus → XOR = 1
                if y_count == 0 or y_count == 4:
                    expected_xor = 0  # Even parity
                else:  # y_count == 2
                    expected_xor = 1  # Odd parity

                is_correct = (xor_val == expected_xor)
                valid_results.append(1 if is_correct else 0)

    valid = len(valid_results)
    correct = sum(valid_results)
    qber = 1 - (correct / valid) if valid > 0 else 0

    return {
        "role": "alice (dealer)",
        "num_rounds": num_rounds,
        "valid_rounds": valid,
        "correct": correct,
        "qber": round(qber, 4),
        "key_rate": round(valid / num_rounds, 4),
        "expected_valid_fraction": 0.5
    }

if __name__ == "__main__":
    main()
