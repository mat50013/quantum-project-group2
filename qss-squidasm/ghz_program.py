from typing import Generator, Tuple

from netqasm.sdk import Qubit
from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from squidasm.util.routines import create_ghz

class GHZProgram(Program):
    """
    Base class for programs relying on creation of GHZ states.
    """

    def get_ghz_qubit(self, context: ProgramContext) -> Generator[None, None, Tuple[Qubit, int]]:
        connection = context.connection

        down_epr_socket = None
        up_epr_socket = None
        down_socket = None
        up_socket = None

        if self.previous_peer is not None:
            down_epr_socket = context.epr_sockets[self.previous_peer]
            down_socket = context.csockets[self.previous_peer]
        if self.next_peer is not None:
            up_epr_socket = context.epr_sockets[self.next_peer]
            up_socket = context.csockets[self.next_peer]

        # noinspection PyTupleAssignmentBalance
        return create_ghz(
            connection,
            down_epr_socket,
            up_epr_socket,
            down_socket,
            up_socket,
            do_corrections=True,
        )
