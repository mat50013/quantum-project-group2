import random
import netsquid as ns
from netsquid.protocols import Protocol

class PartyProtocol(Protocol):
    """
    Generic party protocol for GHZ-based secret sharing.

    Each party:
    1. Waits for qubit to arrive in memory
    2. Chooses random X or Y basis
    3. Measures qubit
    4. Broadcasts basis choice to all other parties
    """

    def __init__(self, node, party_name: str, other_parties: list):
        super().__init__(name=f"Protocol_{party_name}")
        self.node = node
        self.party_name = party_name
        self.other_parties = other_parties
        self.memory = node.subcomponents["memory"]

        # Results
        self.basis = None
        self.outcome = None
        self.received_bases = {}

    def run(self):
        # Wait for qubit in memory
        while len(self.memory.used_positions) < 1:
            yield self.await_timer(1)

        # Choose random basis (X or Y for GHZ protocol)
        self.basis = random.choice(["X", "Y"])
        observable = ns.X if self.basis == "X" else ns.Y

        # Measure qubit
        self.outcome, _ = self.memory.measure([0], observable)

        # Broadcast basis to all other parties
        for other in self.other_parties:
            port_name = f"c_port_to{other}"
            if port_name in self.node.ports:
                self.node.ports[port_name].tx_output((self.party_name, self.basis))

        # Collect bases from other parties
        for other in self.other_parties:
            port_name = f"c_port_from{other}"
            if port_name in self.node.ports:
                port = self.node.ports[port_name]
                yield self.await_port_input(port)
                msg = port.rx_input()
                if msg and msg.items:
                    sender, basis = msg.items[0]
                    self.received_bases[sender] = basis


class DealerProtocol(Protocol):
    """
    Dealer protocol - same as party but may have different memory position.
    """
    def __init__(self, node, dealer_name: str, recipient_names: list):
        super().__init__(name=f"Protocol_{dealer_name}")
        self.node = node
        self.dealer_name = dealer_name
        self.recipient_names = recipient_names
        self.memory = node.subcomponents["memory"]

        self.basis = None
        self.outcome = None
        self.received_bases = {}

    def run(self):
        # Dealer's qubit is at position 0
        while 0 not in self.memory.used_positions:
            yield self.await_timer(1)

        # Choose random basis
        self.basis = random.choice(["X", "Y"])
        observable = ns.X if self.basis == "X" else ns.Y

        # Measure
        self.outcome, _ = self.memory.measure([0], observable)

        # Broadcast basis to recipients
        for recipient in self.recipient_names:
            port_name = f"c_port_to{recipient}"
            if port_name in self.node.ports:
                self.node.ports[port_name].tx_output((self.dealer_name, self.basis))

        # Collect bases from recipients
        for recipient in self.recipient_names:
            port_name = f"c_port_from{recipient}"
            if port_name in self.node.ports:
                port = self.node.ports[port_name]
                yield self.await_port_input(port)
                msg = port.rx_input()
                if msg and msg.items:
                    sender, basis = msg.items[0]
                    self.received_bases[sender] = basis