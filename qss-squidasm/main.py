import random
from typing import List

import numpy as np
from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from squidasm.run.stack.config import HeraldedLinkConfig

from squidasm.run.stack.run import run
from squidasm.sim.stack.program import ProgramContext, ProgramMeta
from squidasm.util.util import create_complete_graph_network
from ghz_program import GHZProgram

class DealerProgram(GHZProgram):
    def __init__(self, name: str, recipient_names: List[str], num_states: int):
        self.name = name
        self.recipient_names = recipient_names
        self.previous_peer = None
        self.next_peer = recipient_names[0]
        self.num_states = num_states

    @property
    def meta(self) -> ProgramMeta:
        # Dealer has classic links to all recipients.
        # Dealer has quantum link to first recipient (for GHZ).
        return ProgramMeta(
            name="dealer",
            csockets=self.recipient_names,
            epr_sockets=[self.next_peer],
            max_qubits=2,
        )

    def run(self, context: ProgramContext):
        connection = context.connection

        valid_results = []

        for i in range(self.num_states):
            qubit, _ = yield from self.get_ghz_qubit(context)

            basis = random.choice(["X", "Y"])

            if basis == "X":
                qubit.H()
            else:
                qubit.rot_Z(n=3, d=0)
                qubit.H()

            q_measure = qubit.measure()
            yield from connection.flush()

            Y_count = 1 if basis == "Y" else 0

            for recipient_name in self.recipient_names:
                basis = yield from context.csockets[recipient_name].recv()
                if basis == "Y":
                    Y_count += 1

            is_valid = Y_count % 2 == 0

            for recipient_name in self.recipient_names:
                context.csockets[recipient_name].send("y" if is_valid else "n")

            if not is_valid:
                # Invalid
                continue

            valid_results.append(int(q_measure))

        return {"name": self.name, "result": np.array(valid_results)}

class RecipientProgram(GHZProgram):
    def __init__(self, name: str, dealer_name: str, recipient_names: List[str], num_states: int):
        self.name = name
        self.dealer_name = dealer_name
        self.num_states = num_states

        i = recipient_names.index(name)

        if i > 0:
            self.previous_peer = recipient_names[i - 1]
        else:
            self.previous_peer = dealer_name

        if i < len(recipient_names) - 1:
            self.next_peer = recipient_names[i + 1]
        else:
            self.next_peer = None


    @property
    def meta(self) -> ProgramMeta:
        # Recipients have classical connections to the dealer and the previous and next peer where applicable (for GHZ).
        # Recipients have quantum links to the previous and next peer where applicable (for GHZ).
        return ProgramMeta(
            name="recipient",
            csockets=[self.dealer_name] + [p for p in [self.previous_peer, self.next_peer] if p is not None and p is not self.dealer_name],
            epr_sockets=[p for p in [self.previous_peer, self.next_peer] if p is not None],
            max_qubits=2,
        )

    def run(self, context: ProgramContext):
        connection = context.connection

        valid_results = []

        for i in range(self.num_states):
            qubit, _ = yield from self.get_ghz_qubit(context)

            basis = random.choice(["X", "Y"])

            if basis == "X":
                qubit.H()
            else:
                qubit.rot_Z(n=3, d=0)
                qubit.H()

            q_measure = qubit.measure()
            yield from connection.flush()

            context.csockets[self.dealer_name].send(basis)

            is_valid = (yield from context.csockets[self.dealer_name].recv()) == "y"

            if not is_valid:
                # Invalid
                continue

            valid_results.append(int(q_measure))

        return {"name": self.name, "result": np.array(valid_results)}


if __name__ == "__main__":
    dealer_name = "alice"
    recipient_names = ["bob", "charlie", "diana"]
    num_states = 10

    node_names = [dealer_name] + recipient_names

    cfg = create_complete_graph_network(
        node_names,
        "heralded",
        HeraldedLinkConfig(length=5, emission_fidelity=0.95),
        clink_typ="default",
        clink_cfg=DefaultCLinkConfig(delay=10),
    )

    programs = { dealer_name: DealerProgram(dealer_name, recipient_names, num_states) } | { recipient_name: RecipientProgram(recipient_name, dealer_name, recipient_names, num_states) for recipient_name in recipient_names }

    num_times = 20
    results = run(config=cfg, programs=programs, num_times=num_times)

    mean_qber = 0

    for n in range(num_times):
        dealer_results = results[0][n]['result']

        parity = np.zeros_like(dealer_results)

        for i in range(len(recipient_names)):
            recipient_results = results[i + 1][n]['result']
            parity = np.bitwise_xor(parity, recipient_results)

        qber = np.not_equal(dealer_results, parity).sum() / parity.size
        mean_qber += qber / num_times
        print(f"Round {n}: QBER = {qber}")

    print(f"Mean QBER = {mean_qber}")