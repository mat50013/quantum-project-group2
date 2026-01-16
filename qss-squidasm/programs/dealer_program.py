import random
from typing import List

import numpy as np

from squidasm.sim.stack.program import ProgramContext, ProgramMeta
from .ghz_program import GHZProgram

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