import netsquid as ns
from netsquid.protocols import Protocol
from netsquid.qubits.operators import H, CNOT

class QubitReceiverProtocol(Protocol):
    """Protocol to receive a qubit and store it in memory."""

    def __init__(self, node, port_name):
        super().__init__(name=f"Receiver_{node.name}")
        self.node = node
        self.port_name = port_name
        self.memory = node.subcomponents["memory"]
        self.received = False

    def run(self):
        port = self.node.ports[self.port_name]
        yield self.await_port_input(port)
        msg = port.rx_input()
        if msg and msg.items:
            qubit = msg.items[0]
            self.memory.put(qubit, [0])
            self.received = True


def create_ghz_state(n_qubits: int):
    """
    Create an n-qubit GHZ state: (|00...0⟩ + |11...1⟩) / √2

    Args:
        n_qubits: Number of qubits

    Returns:
        List of entangled qubits
    """
    qubits = ns.qubits.create_qubits(n_qubits)

    # Apply H to first qubit
    ns.qubits.operate(qubits[0], H)

    # Apply CNOT from first to all others
    for i in range(1, n_qubits):
        ns.qubits.operate([qubits[0], qubits[i]], CNOT)

    return qubits


def distribute_ghz_state(nodes, dealer_name: str, recipient_names: list):
    """
    Create and distribute GHZ state from dealer to recipients.
    """

    dealer = nodes[dealer_name]
    dealer_mem = dealer.subcomponents["memory"]
    n_parties = 1 + len(recipient_names)

    # Create GHZ state
    qubits = create_ghz_state(n_parties)

    # Store all qubits in dealer's memory
    dealer_mem.put(qubits, list(range(n_parties)))

    # Setup receivers
    receivers = []
    for recipient in recipient_names:
        receiver = QubitReceiverProtocol(
            nodes[recipient],
            f"q_port_from{dealer_name}"
        )
        receiver.start()
        receivers.append(receiver)

    # Send qubits to recipients (dealer keeps position 0)
    for i, recipient in enumerate(recipient_names):
        qubit = dealer_mem.pop([i + 1])[0]
        dealer.ports[f"q_port_to{recipient}"].tx_output(qubit)

    # Wait for distribution
    ns.sim_run(duration=100)

    return receivers


def distribute_ghz_with_eve(nodes, dealer_name: str, recipient_names: list,
                            eve_node, eve_target: str, eve_protocol_class):
    """
    Distribute GHZ state with Eve intercepting one recipient's qubit.

    Returns:
        eve_protocol: Eve's protocol instance (for accessing results)
    """

    dealer = nodes[dealer_name]
    dealer_mem = dealer.subcomponents["memory"]
    n_parties = 1 + len(recipient_names)

    # Create GHZ state
    qubits = create_ghz_state(n_parties)
    dealer_mem.put(qubits, list(range(n_parties)))

    # Setup receivers
    receivers = []
    for recipient in recipient_names:
        if recipient == eve_target:
            port_name = "q_port_fromEve"
        else:
            port_name = f"q_port_from{dealer_name}"

        receiver = QubitReceiverProtocol(nodes[recipient], port_name)
        receiver.start()
        receivers.append(receiver)

    # Setup Eve's intercept protocol
    eve_protocol = eve_protocol_class(eve_node, eve_target)
    eve_protocol.start()

    for i, recipient in enumerate(recipient_names):
        qubit = dealer_mem.pop([i + 1])[0]

        if recipient == eve_target:
            # Send through Eve
            dealer.ports["q_port_toEve"].tx_output(qubit)
        else:
            # Send directly
            dealer.ports[f"q_port_to{recipient}"].tx_output(qubit)

    # Wait for distribution
    ns.sim_run(duration=100)

    return eve_protocol, receivers