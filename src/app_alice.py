from dataclasses import dataclass
from typing import Optional

from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import EPRSocket
from netqasm.sdk.toolbox.multi_node import create_ghz

import random
from rich.progress import Progress, TimeElapsedColumn, SpinnerColumn, MofNCompleteColumn

def distribute_ghz_states(conn, down_epr_socket, down_socket, up_epr_socket, up_socket, n_bits):
    bases = [random.randint(0, 1) for _ in range(n_bits)] # 0 = X, 1 = Y
    outcomes = [None for _ in range(n_bits)]

    with Progress(SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), MofNCompleteColumn()) as p:
        task = p.add_task("Distributing GHZ states...", total=n_bits)

        for i in range(n_bits):
            q, _ = create_ghz(
                down_epr_socket=down_epr_socket,
                down_socket=down_socket,
                up_epr_socket=up_epr_socket,
                up_socket=up_socket,
                do_corrections=True
            )
            if bases[i] == 1:
                q.rot_Z(n=3, d=1)
            q.H()
            m = q.measure()
            conn.flush()
            down_socket.recv_silent()
            down_socket.send_silent("")
            up_socket.send_silent("")
            up_socket.recv_silent()
            outcomes[i] = int(m)

            p.update(task, advance=1)

    return bases, outcomes

def exchange_bases(bob_socket, charlie_socket, triplets_info):
    alice_bases = [triplet.alice_basis for triplet in triplets_info]
    bob_bases = bob_socket.recv_structured().payload
    charlie_bases = charlie_socket.recv_structured().payload

    bob_socket.send_structured(StructuredMessage(header="Bases", payload=alice_bases))
    bob_socket.send_structured(StructuredMessage(header="Bases", payload=charlie_bases))

    charlie_socket.send_structured(StructuredMessage(header="Bases", payload=alice_bases))
    charlie_socket.send_structured(StructuredMessage(header="Bases", payload=bob_bases))

    for i in range(len(triplets_info)):
        triplets_info[i].bob_basis = bob_bases[i]
        triplets_info[i].charlie_basis = charlie_bases[i]
    
    return triplets_info

def sift_bases(triplets_info):
    for triplet in triplets_info:
        if (triplet.alice_basis + triplet.bob_basis + triplet.charlie_basis) % 2 == 0:
            triplet.is_valid = True
        else:
            triplet.is_valid = False

    return triplets_info

def receive_outcomes_for_qber(bob_socket, charlie_socket, triplets_info):
    bob_outcomes = bob_socket.recv_structured().payload
    charlie_outcomes = charlie_socket.recv_structured().payload

    for outcome in bob_outcomes:
        triplets_info[outcome[0]].bob_outcome = outcome[1]
    
    for outcome in charlie_outcomes:
        triplets_info[outcome[0]].charlie_outcome = outcome[1]
    
    return triplets_info

def calculate_qber(triplets_info, test_num_rounds):
    qber = 0

    for triplet in triplets_info:
        if triplet.is_valid and triplet.bob_outcome != None and triplet.charlie_outcome != None:
            xor = triplet.alice_outcome ^ triplet.bob_outcome ^ triplet.charlie_outcome

            if triplet.alice_basis + triplet.bob_basis + triplet.charlie_basis == 0:
                qber += xor % 2 + 1
            else:
                qber += xor
    
    return 1 - (qber / test_num_rounds)


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

def main(app_config=None, num_rounds=10, eve_intercept=0):
    # Initialize classical communication sockets
    bob_socket = Socket("alice", "bob", log_config=app_config.log_config)
    charlie_socket = Socket("alice", "charlie", log_config=app_config.log_config)
    eve_socket = Socket("alice", "eve", log_config=app_config.log_config)

    # Initialize quantum EPR sockets for entanglement generation
    bob_epr_socket = EPRSocket("bob")
    charlie_epr_socket = EPRSocket("charlie")
    eve_epr_socket = EPRSocket("eve")

    # Create NetQASM connection for quantum operations
    alice = NetQASMConnection(
        "alice",
        log_config=app_config.log_config,
        epr_sockets=[bob_epr_socket, charlie_epr_socket, eve_epr_socket]
    )

    with alice:
        if eve_intercept == 0:
            bases, outcomes = distribute_ghz_states(alice, bob_epr_socket, bob_socket, charlie_epr_socket, charlie_socket, num_rounds)
        else:
            bases, outcomes = distribute_ghz_states(alice, eve_epr_socket, eve_socket, charlie_epr_socket, charlie_socket, num_rounds)

    triplets_info = []
    for i in range(num_rounds):
        triplets_info.append(
            TripletInfo(
                index=i,
                alice_basis=bases[i],
                alice_outcome=outcomes[i]
            )
        )
        
    triplets_info = exchange_bases(bob_socket, charlie_socket, triplets_info)
    triplets_info = sift_bases(triplets_info)

    valid_amount = sum(list(map(lambda triplet: 1 if triplet.is_valid else 0, triplets_info)))

    triplets_info = receive_outcomes_for_qber(bob_socket, charlie_socket, triplets_info)

    qber = calculate_qber(triplets_info, max(valid_amount // 4, 1)) if valid_amount > 0 else -1

    print("QBER: " + str(round(qber, 2)))

    return {
        "role": "alice",
        "num_rounds": num_rounds,
        "qber": round(qber, 4),
        "key_rate": round(valid_amount / num_rounds, 4)  # Fraction of rounds that were valid
    }

if __name__ == "__main__":
    main()