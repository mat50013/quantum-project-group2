import netsquid as ns
import random
from netsquid.protocols import Protocol
from netsquid.qubits.operators import H, CNOT

class EveInterceptProtocol(Protocol):
    """
    Eve's intercept-resend attack protocol.
    
    Eve intercepts ONE qubit (either Bob's or Charlie's), measures it
    in a random basis, then prepares a fresh qubit in the measured state
    and forwards it. This breaks the GHZ correlations.
    """
    def __init__(self, eve_node, target_name):
        super().__init__()
        self.eve_node = eve_node
        self.target_name = target_name  # "Bob" or "Charlie"
        self.memory = eve_node.subcomponents["memory1"]
        self.basis = None
        self.outcome = None
        self.intercepted = False
        
    def run(self):
        # Wait for incoming qubit
        input_port_name = f"q_port_fromAlice"
        input_port = self.eve_node.ports[input_port_name]
        
        yield self.await_port_input(input_port)
        
        # Receive qubit
        msg = input_port.rx_input()
        qubit = msg.items[0]
        
        # Store in memory temporarily
        self.memory.put(qubit, [0])
        
        # Choose random basis for measurement
        self.basis = random.choice(["X", "Y"])
        observable = ns.X if self.basis == "X" else ns.Y
        
        # Measure the qubit
        self.outcome, _ = self.memory.measure([0], observable)
        self.intercepted = True
        
        print(f"🕵️  Eve intercepted qubit for {self.target_name}: measured in {self.basis}-basis, got {self.outcome}")
        
        # Prepare a fresh qubit in the measured outcome state
        new_qubit = ns.qubits.create_qubits(1)[0]
        
        # If outcome was 1, apply X gate to flip |0⟩ to |1⟩
        if self.outcome[0] == 1:
            ns.qubits.operate(new_qubit, ns.X)
        
        # Forward the new qubit to intended recipient
        output_port_name = f"q_port_to{self.target_name}"
        output_port = self.eve_node.ports[output_port_name]
        output_port.tx_output(new_qubit)
        
        print(f"🕵️  Eve forwarded fresh qubit to {self.target_name}")


def distribute_ghz_with_eve(Eve, intercept_target="Bob"):
    """
    Modified GHZ distribution where Eve intercepts ONE qubit.
    
    Args:
        Eve: Eve's node
        intercept_target: Either "Bob" or "Charlie" - who Eve intercepts
    """
    from network import Alice, Bob, Charlie
    
    alice_mem = Alice.subcomponents["memory1"]

    # Create 3 qubits and apply GHZ circuit at Alice
    qubits = ns.qubits.create_qubits(3)
    alice_mem.put(qubits, [0, 1, 2])

    # Apply H to first qubit and CNOT gates to create GHZ state
    ns.qubits.operate(alice_mem.peek([0])[0], H)
    ns.qubits.operate([alice_mem.peek([0])[0], alice_mem.peek([1])[0]], CNOT)
    ns.qubits.operate([alice_mem.peek([0])[0], alice_mem.peek([2])[0]], CNOT)

    # Create receiver protocols
    from ghz_resource import QubitReceiverProtocol
    
    if intercept_target == "Bob":
        # Eve intercepts Bob's qubit, Charlie receives directly
        bob_receiver = QubitReceiverProtocol(Bob, "q_port_fromEve")
        charlie_receiver = QubitReceiverProtocol(Charlie, "q_port_fromAlice")
        
        bob_receiver.start()
        charlie_receiver.start()
        
        # Create Eve's intercept protocol for Bob only
        eve_intercept = EveInterceptProtocol(Eve, "Bob")
        eve_intercept.start()
        
        # Alice sends: Bob's qubit through Eve, Charlie's directly
        Alice.ports["q_port_toEve"].tx_output(alice_mem.pop([1])[0])
        Alice.ports["q_port_toCharlie"].tx_output(alice_mem.pop([2])[0])
        
    else:  # intercept_target == "Charlie"
        # Eve intercepts Charlie's qubit, Bob receives directly
        bob_receiver = QubitReceiverProtocol(Bob, "q_port_fromAlice")
        charlie_receiver = QubitReceiverProtocol(Charlie, "q_port_fromEve")
        
        bob_receiver.start()
        charlie_receiver.start()
        
        # Create Eve's intercept protocol for Charlie only
        eve_intercept = EveInterceptProtocol(Eve, "Charlie")
        eve_intercept.start()
        
        # Alice sends: Bob's directly, Charlie's through Eve
        Alice.ports["q_port_toBob"].tx_output(alice_mem.pop([1])[0])
        Alice.ports["q_port_toEve"].tx_output(alice_mem.pop([2])[0])

    # Wait for distribution to complete
    ns.sim_run(duration=100)