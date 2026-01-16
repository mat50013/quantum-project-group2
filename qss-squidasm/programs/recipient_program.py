import random
from typing import List

import numpy as np

from squidasm.sim.stack.program import ProgramContext, ProgramMeta
from .ghz_program import GHZProgram

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