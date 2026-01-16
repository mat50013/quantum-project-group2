import netsquid as ns
import random
from netsquid.protocols import Protocol

class HBB99PartyProtocol(Protocol):
    """Generic party protocol for HBB99"""
    def __init__(self, node, party_name, other_parties):
        super().__init__()
        self.node = node
        self.party_name = party_name
        self.other_parties = other_parties
        self.memory = node.subcomponents["memory1"]
        self.basis = None
        self.outcome = None
        self.received_bases = {}

    def run(self):
        # Wait until qubit is in memory
        while len(self.memory.used_positions) < 1:  # FIXED: Use len(used_positions) instead
            yield self.await_timer(1)

        # Choose basis randomly
        self.basis = random.choice(["X", "Y"])
        observable = ns.X if self.basis == "X" else ns.Y

        # Measure qubit
        self.outcome, _ = self.memory.measure([0], observable)
        
        print(f"{self.party_name} measured in {self.basis}-basis with outcome {self.outcome}")

        # Broadcast basis to all other parties
        for port in self.node.ports.values():
            if port.name.startswith("c_port_to"):
                port.tx_output((self.party_name, self.basis))

        # Collect bases from other parties
        for _ in range(len(self.other_parties)):
            # Wait for any classical message
            for party in self.other_parties:
                port_name = f"c_port_from{party}"
                if port_name in self.node.ports:
                    port = self.node.ports[port_name]
                    yield self.await_port_input(port)
                    msg = port.rx_input()
                    if msg is not None:
                        sender, basis = msg.items[0]
                        self.received_bases[sender] = basis
                        break