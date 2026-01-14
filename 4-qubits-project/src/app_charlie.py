import math
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz
import random

def main(app_config=None, num_rounds=50, x=0, y=0):
    socket_bob = Socket("charlie", "bob", log_config=app_config.log_config)
    socket_david = Socket("charlie", "david", log_config=app_config.log_config)

    epr_bob = EPRSocket("bob")
    epr_david = EPRSocket("david")

    charlie = NetQASMConnection(
        "charlie",
        log_config=app_config.log_config,
        epr_sockets=[epr_bob, epr_david]
    )

    with charlie:
        for _ in range(num_rounds):
            # Charlie is middle node: Bob <- Charlie -> David
            q, m = create_ghz(
                down_epr_socket=epr_bob,
                up_epr_socket=epr_david,
                down_socket=socket_bob,
                up_socket=socket_david,
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
            charlie.flush()
            outcome = int(result)

            # Receive from David first (END of chain)
            david_basis = socket_david.recv()
            david_outcome = int(socket_david.recv())

            # Send Charlie + David info to Bob
            socket_bob.send(basis)
            socket_bob.send(str(outcome))
            socket_bob.send(david_basis)
            socket_bob.send(str(david_outcome))

            # Receive Bob + Alice info from Bob
            bob_basis = socket_bob.recv()
            bob_outcome = int(socket_bob.recv())
            alice_basis = socket_bob.recv()
            alice_outcome = int(socket_bob.recv())

            # Send all info to David
            socket_david.send(basis)
            socket_david.send(str(outcome))
            socket_david.send(bob_basis)
            socket_david.send(str(bob_outcome))
            socket_david.send(alice_basis)
            socket_david.send(str(alice_outcome))

    return {
        "role": "charlie (recipient)",
        "num_rounds": num_rounds
    }

if __name__ == "__main__":
    main()