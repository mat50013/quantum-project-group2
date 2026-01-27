import random
import netsquid as ns
from netsquid.protocols import Protocol
from netsquid.qubits import qubitapi as qapi

class EveInterceptProtocol(Protocol):
    def __init__(self, eve_node, target_name: str, strategy: str = "random"):
        super().__init__(name="EveIntercept")
        self.eve_node = eve_node
        self.target_name = target_name
        self.strategy = strategy
        self.memory = eve_node.subcomponents["memory"]
        self.basis = None
        self.outcome = None
        self.intercepted = False

    def _choose_basis(self):
        if self.strategy == "random":
            return random.choice(["X", "Y"])
        elif self.strategy in ["X", "Y", "Z"]:
            return self.strategy
        else:
            return random.choice(["X", "Y"])

    def _create_epr_pair(self):
        q_eve, q_target = qapi.create_qubits(2)
        qapi.operate(q_eve, ns.H)
        qapi.operate([q_eve, q_target], ns.CNOT)
        return q_eve, q_target

    def _forward_to_target(self, measurement, basis):
        q = qapi.create_qubits(1)[0]
        if measurement == 1:
            qapi.operate(q, ns.X)

        qapi.operate(q, ns.H)
        if basis == "Y":
            qapi.operate(q, ns.S)
        return q

    def run(self):
        input_port = self.eve_node.ports["q_port_fromAlice"]
        yield self.await_port_input(input_port)

        msg = input_port.rx_input()
        if not msg or not msg.items:
            return
        qubit = msg.items[0]

        self.basis = self._choose_basis()
        if self.basis == "X":
            observable = ns.X
        elif self.basis == "Y":
            observable = ns.Y
        else:
            observable = ns.Z

        self.outcome, _ = qapi.measure(qubit, observable=observable)
        self.intercepted = True

        qubit_for_target = self._forward_to_target(self.outcome, self.basis)
        output_port = self.eve_node.ports[f"q_port_to{self.target_name}"]
        output_port.tx_output(qubit_for_target)