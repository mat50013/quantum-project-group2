from dataclasses import dataclass
import math
from typing import Optional

from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz

import random

def distribute_ghz_states(conn, down_epr_socket, down_socket, n_bits):
    bases = [random.randint(0, 1) for _ in range(n_bits)] # 0 = X, 1 = Y
    outcomes = [None for _ in range(n_bits)]

    for i in range(n_bits):
        q, _ = create_ghz(
            down_epr_socket=down_epr_socket,
            down_socket=down_socket,
            do_corrections=True
        )
        if bases[i] == 1:
            q.rot_Z(n=3, d=1)
        q.H()
        m = q.measure()
        conn.flush()
        outcomes[i] = int(m)

    return bases, outcomes

def exchange_bases(alice_socket, triplets_info):
    charlie_bases = [triplet.charlie_basis for triplet in triplets_info]

    alice_socket.send_structured(StructuredMessage(header="Bases", payload=charlie_bases))
    
    alice_bases = alice_socket.recv_structured().payload
    bob_bases = alice_socket.recv_structured().payload

    for i in range(len(triplets_info)):
        triplets_info[i].alice_basis = alice_bases[i]
        triplets_info[i].bob_basis = bob_bases[i]
    
    return triplets_info

def sift_bases(triplets_info):
    for triplet in triplets_info:
        if (triplet.alice_basis + triplet.bob_basis + triplet.charlie_basis) % 2 == 0:
            triplet.is_valid = True
        else:
            triplet.is_valid = False

    return triplets_info

def send_outcomes_for_qber(socket, triplets_info, test_num_rounds):
    valid_outcomes = list(map(
        lambda triplet: (triplet.index, triplet.charlie_outcome),
        list(filter(
            lambda triplet: triplet.is_valid,
            triplets_info
        ))
    ))

    socket.send_structured(StructuredMessage(header="Outcomes", payload=valid_outcomes[:test_num_rounds]))
    
    return

@dataclass
class TripletInfo:
    """Information that Alice has about one generated triplet.
    The information is filled progressively during the protocol."""

    # Index in list of all generated pairs.
    index: int

    # True if Bob and Charlie can deduct Alice's bit when they cooperate
    is_valid: Optional[bool] = None

    # Basis Alice measured in. 0 = X, 1 = Y.
    alice_basis: Optional[int] = None

    # Basis Bob measured in. 0 = X, 1 = Y.
    bob_basis: Optional[int] = None

    # Basis Charlie measured in. 0 = X, 1 = Y.
    charlie_basis: Optional[int] = None

    # Alice measurement outcome (0 or 1).
    alice_outcome: Optional[int] = None

    # Bob measurement outcome (0 or 1).
    bob_outcome: Optional[int] = None

    # Charlie measurement outcome (0 or 1).
    charlie_outcome: Optional[int] = None

def main(app_config=None, num_rounds=4):
    # Initialize classical communication sockets
    alice_socket = Socket("charlie", "alice", log_config=app_config.log_config)
    bob_socket = Socket("charlie", "bob", log_config=app_config.log_config)

    # Initialize quantum EPR socket for entanglement generation with Bob
    bob_epr_socket = EPRSocket("bob")

    # Create NetQASM connection for quantum operations
    charlie = NetQASMConnection(
        "charlie",
        log_config=app_config.log_config,
        epr_sockets=[bob_epr_socket]
    )

    with charlie:
        bases, outcomes = distribute_ghz_states(charlie, bob_epr_socket, bob_socket, num_rounds)

    triplets_info = []
    for i in range(num_rounds):
        triplets_info.append(
            TripletInfo(
                index=i,
                charlie_basis=bases[i],
                charlie_outcome=outcomes[i]
            )
        )

    triplets_info = exchange_bases(alice_socket, triplets_info)
    triplets_info = sift_bases(triplets_info)

    valid_amount = sum(list(map(lambda triplet: 1 if triplet.is_valid else 0, triplets_info)))

    send_outcomes_for_qber(alice_socket, triplets_info, max(valid_amount // 4, 1))

    return {
        "role": "charlie",
        "num_rounds": num_rounds
    }

if __name__ == "__main__":
    main()