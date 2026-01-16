import netsquid as ns
from netsquid.protocols import Protocol
from netsquid.qubits.operators import H, CNOT
from network import Alice, Bob, Charlie

class QubitReceiverProtocol(Protocol):
    """Protocol to receive a qubit and store it in memory"""
    def __init__(self, node, port_name):
        super().__init__()
        self.node = node
        self.port_name = port_name
        self.memory = node.subcomponents["memory1"]
    
    def run(self):
        port = self.node.ports[self.port_name]
        yield self.await_port_input(port)
        msg = port.rx_input()
        qubit = msg.items[0]
        self.memory.put(qubit, [0])

def distribute_ghz_state():
    """Create and distribute GHZ state |000⟩ + |111⟩"""
    alice_mem = Alice.subcomponents["memory1"]

    # Create 3 qubits and apply GHZ circuit
    qubits = ns.qubits.create_qubits(3)
    alice_mem.put(qubits, [0, 1, 2])

    # Apply H to first qubit and CNOT gates
    ns.qubits.operate(alice_mem.peek([0])[0], H)
    ns.qubits.operate([alice_mem.peek([0])[0], alice_mem.peek([1])[0]], CNOT)
    ns.qubits.operate([alice_mem.peek([0])[0], alice_mem.peek([2])[0]], CNOT)

    # Create receiver protocols
    bob_receiver = QubitReceiverProtocol(Bob, "q_port_fromAlice")
    charlie_receiver = QubitReceiverProtocol(Charlie, "q_port_fromAlice")
    
    bob_receiver.start()
    charlie_receiver.start()

    # Send qubits
    Alice.ports["q_port_toBob"].tx_output(alice_mem.pop([1])[0])
    Alice.ports["q_port_toCharlie"].tx_output(alice_mem.pop([2])[0])

    # Wait for distribution to complete
    ns.sim_run(duration=100)