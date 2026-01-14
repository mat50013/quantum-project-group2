import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, x=0, y=0):
    socket_alice = Socket("bob", "alice", log_config=app_config.log_config)
    socket_charlie = Socket("bob", "charlie", log_config=app_config.log_config)

    epr_alice = EPRSocket("alice")
    epr_charlie = EPRSocket("charlie")

    bob = NetQASMConnection(
        "bob",
        log_config=app_config.log_config,
        epr_sockets=[epr_alice, epr_charlie]
    )

    with bob:
        for _ in range(num_rounds):
            # Bob is middle node in GHZ chain
            q, m = create_ghz(
                down_epr_socket=epr_alice,
                up_epr_socket=epr_charlie,
                down_socket=socket_alice,
                up_socket=socket_charlie,
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
            bob.flush()
            outcome = int(result)

            # Receive from Alice (dealer)
            alice_basis = socket_alice.recv()
            alice_outcome = int(socket_alice.recv())

            # Receive from Charlie (includes David's info)
            charlie_basis = socket_charlie.recv()
            charlie_outcome = int(socket_charlie.recv())
            david_basis = socket_charlie.recv()
            david_outcome = int(socket_charlie.recv())

            # Send all info to Alice
            socket_alice.send(basis)
            socket_alice.send(str(outcome))
            socket_alice.send(charlie_basis)
            socket_alice.send(str(charlie_outcome))
            socket_alice.send(david_basis)
            socket_alice.send(str(david_outcome))

            # Send Alice's and Bob's info to Charlie (for David)
            socket_charlie.send(basis)
            socket_charlie.send(str(outcome))
            socket_charlie.send(alice_basis)
            socket_charlie.send(str(alice_outcome))

    return {
        "role": "bob (recipient)",
        "num_rounds": num_rounds
    }

if __name__ == "__main__":
    main()