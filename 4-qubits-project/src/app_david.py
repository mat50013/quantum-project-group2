import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, x=0, y=0):
    socket_charlie = Socket("david", "charlie", log_config=app_config.log_config)
    epr_socket = EPRSocket("charlie")

    david = NetQASMConnection(
        "david",
        log_config=app_config.log_config,
        epr_sockets=[epr_socket]
    )

    valid_results = []

    with david:
        for _ in range(num_rounds):
            # David is END node in chain
            q, m = create_ghz(
                down_epr_socket=epr_socket,
                down_socket=socket_charlie,
                do_corrections=True
            )

            # Random basis choice
            basis = random.choice(['X', 'Y'])

            if basis == 'X':
                q.H()
            else:
                q.rot_Z(angle=-math.pi/2)
                q.H()

            result = q.measure()
            david.flush()
            outcome = int(result)

            # Send to Charlie
            socket_charlie.send(basis)
            socket_charlie.send(str(outcome))

            # Receive all other parties' info
            charlie_basis = socket_charlie.recv()
            charlie_outcome = int(socket_charlie.recv())
            bob_basis = socket_charlie.recv()
            bob_outcome = int(socket_charlie.recv())
            alice_basis = socket_charlie.recv()
            alice_outcome = int(socket_charlie.recv())

            # Count Y measurements
            bases_list = [alice_basis, bob_basis, charlie_basis, basis]
            y_count = bases_list.count('Y')

            # Valid only when y_count is even (0, 2, or 4)
            # From paper: odd Y-count means "no correlations"
            if y_count % 2 == 0:
                xor_val = alice_outcome ^ bob_outcome ^ charlie_outcome ^ outcome

                # Parity rules from paper:
                # y=0 or y=4: even parity (XOR = 0)
                # y=2: odd parity (XOR = 1)
                if y_count == 0 or y_count == 4:
                    expected_xor = 0
                else:
                    expected_xor = 1

                is_correct = (xor_val == expected_xor)
                valid_results.append(1 if is_correct else 0)

    valid = len(valid_results)
    correct = sum(valid_results)
    qber = 1 - (correct / valid) if valid > 0 else 0

    return {
        "role": "david (recipient)",
        "num_rounds": num_rounds,
        "valid_rounds": valid,
        "correct": correct,
        "qber": round(qber, 4)
    }

if __name__ == "__main__":
    main()