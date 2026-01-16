from dataclasses import dataclass
from typing import Optional

from netqasm.sdk import Qubit
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz

import random

def forward_to_bob(conn, m, basis, forward_epr_socket, forward_socket):
    epr_qubit = forward_epr_socket.create_keep()[0]
    
    q = Qubit(conn)

    if m == 1:
        q.X()
    
    q.H()
    if basis == 1:
        q.S()
    
    # Teleportation protocol
    q.cnot(epr_qubit)
    q.H()
    m1 = q.measure()
    m2 = epr_qubit.measure()

    # Send classical corrections
    forward_socket.send_structured(StructuredMessage(header="Correction", payload=m1))
    forward_socket.send_structured(StructuredMessage(header="Correction", payload=m2))
    
    conn.flush()

    forward_socket.send_silent("")
    forward_socket.recv_silent()

def distribute_ghz_states(conn, up_epr_socket, up_socket, forward_epr_socket, forward_socket, n_bits):
    bases = [random.randint(0, 1) for _ in range(n_bits)] # 0 = X, 1 = Y

    for i in range(n_bits):
        q, _ = create_ghz(
            up_epr_socket=up_epr_socket,
            up_socket=up_socket,
            do_corrections=True
        )
        if bases[i] == 1:
            q.rot_Z(n=3, d=1)
        q.H()
        m = q.measure()
        conn.flush()
        forward_to_bob(conn, m, bases[i], forward_epr_socket, forward_socket)
        up_socket.send_silent("")
        up_socket.recv_silent()

    return

def main(app_config=None, num_rounds=4, eve_intercept=0):
    # Initialize classical communication sockets
    alice_socket = Socket("eve", "alice", log_config=app_config.log_config)
    bob_socket = Socket("eve", "bob", log_config=app_config.log_config)

    # Initialize quantum EPR sockets for entanglement with Alice and Bob
    alice_epr_socket = EPRSocket("alice")
    bob_epr_socket = EPRSocket("bob")

    # Create NetQASM connection for quantum operations
    eve = NetQASMConnection(
        "eve",
        log_config=app_config.log_config,
        epr_sockets=[alice_epr_socket, bob_epr_socket]
    )
    if eve_intercept == 1:
        with eve:
            distribute_ghz_states(eve, alice_epr_socket, alice_socket, bob_epr_socket, bob_socket, num_rounds)

    return {
        "role": "eve",
        "num_rounds": num_rounds
    }

if __name__ == "__main__":
    main()