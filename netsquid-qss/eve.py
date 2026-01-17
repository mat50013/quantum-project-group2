import random
import netsquid as ns
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

class EveInterceptProtocol(Protocol):
    def __init__(self, eve_node, target_name: str, strategy: str = "random"):
        """
        Args:
            eve_node: Eve's node
            target_name: Name of recipient Eve is intercepting for
            strategy: Measurement strategy ("random", "X", "Y", "Z")
        """
        super().__init__(name="EveIntercept")
        self.eve_node = eve_node
        self.target_name = target_name
        self.strategy = strategy
        self.memory = eve_node.subcomponents["memory"]

        # Results
        self.basis = None
        self.outcome = None
        self.intercepted = False

    def _choose_basis(self):
        """Choose measurement basis based on strategy."""
        if self.strategy == "random":
            return random.choice(["X", "Y"])
        elif self.strategy in ["X", "Y", "Z"]:
            return self.strategy
        else:
            return random.choice(["X", "Y"])

    def _create_epr_pair(self):
        """Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2"""
        q_eve, q_target = qapi.create_qubits(2)
        qapi.operate(q_eve, ns.H)
        qapi.operate([q_eve, q_target], ns.CNOT)
        return q_eve, q_target

    def _forward_to_target(self, measurement, basis):
        """
        Recreate state based on measurement and teleport to target.
        """
        # Create EPR pair
        epr_eve, epr_target = self._create_epr_pair()

        # Prepare qubit encoding measurement result
        q = qapi.create_qubits(1)[0]
        if measurement == 1:
            qapi.operate(q, ns.X)

        # Apply basis encoding
        qapi.operate(q, ns.H)
        if basis == "Y":
            qapi.operate(q, ns.S)

        # Teleportation: Bell measurement
        qapi.operate([q, epr_eve], ns.CNOT)
        qapi.operate(q, ns.H)

        m1, _ = qapi.measure(q, observable=ns.Z)
        m2, _ = qapi.measure(epr_eve, observable=ns.Z)

        # Apply corrections to target's qubit
        if m2 == 1:
            qapi.operate(epr_target, ns.X)
        if m1 == 1:
            qapi.operate(epr_target, ns.Z)

        return epr_target

    def run(self):
        # Wait for incoming qubit from dealer
        input_port = self.eve_node.ports["q_port_fromAlice"]
        yield self.await_port_input(input_port)

        # Receive qubit
        msg = input_port.rx_input()
        if not msg or not msg.items:
            return

        qubit = msg.items[0]

        # Choose measurement basis
        self.basis = self._choose_basis()

        if self.basis == "X":
            observable = ns.X
        elif self.basis == "Y":
            observable = ns.Y
        else:
            observable = ns.Z

        # Measure the intercepted qubit
        self.outcome, _ = qapi.measure(qubit, observable=observable)
        self.intercepted = True

        # Teleport to target instead of simple prepare-and-send
        qubit_for_target = self._forward_to_target(self.outcome, self.basis)

        # Forward to target recipient
        output_port = self.eve_node.ports[f"q_port_to{self.target_name}"]
        output_port.tx_output(qubit_for_target)