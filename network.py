import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumMemory
from netsquid.components import QuantumChannel, ClassicalChannel

# Create Alice, Bob, Charlie, and Eve nodes
Alice = Node("Alice")
Bob = Node("Bob")
Charlie = Node("Charlie")
Eve = Node("Eve")

# Add quantum memory to Alice
qmemory_Alice = QuantumMemory("AliceMemory", num_positions=3)
Alice.add_subcomponent(qmemory_Alice, name="memory1")

# Add quantum memory to Bob
qmemory_Bob = QuantumMemory("BobMemory", num_positions=1)
Bob.add_subcomponent(qmemory_Bob, name="memory1")

# Add quantum memory to Charlie
qmemory_Charlie = QuantumMemory("CharlieMemory", num_positions=1)
Charlie.add_subcomponent(qmemory_Charlie, name="memory1")

# Add quantum memory to Eve (needs only 1 position - intercepts ONE qubit)
qmemory_Eve = QuantumMemory("EveMemory", num_positions=1)
Eve.add_subcomponent(qmemory_Eve, name="memory1")

# ========== ALICE PORTS ==========
Alice.add_ports([
    # Quantum output ports - one to Eve, one direct (depending on who Eve intercepts)
    "q_port_toEve", "q_port_toBob", "q_port_toCharlie",
    # Classical ports (unchanged - Alice doesn't know about Eve)
    "c_port_toBob", "c_port_toCharlie",
    "c_port_fromBob", "c_port_fromCharlie"
])

# ========== BOB PORTS ==========
Bob.add_ports([
    # Quantum input - either from Alice directly or from Eve
    "q_port_fromAlice", "q_port_fromEve",
    # Classical ports
    "c_port_fromAlice", "c_port_fromCharlie",
    "c_port_toAlice", "c_port_toCharlie"
])

# ========== CHARLIE PORTS ==========
Charlie.add_ports([
    # Quantum input - either from Alice directly or from Eve
    "q_port_fromAlice", "q_port_fromEve",
    # Classical ports
    "c_port_fromAlice", "c_port_fromBob",
    "c_port_toAlice", "c_port_toBob"
])

# ========== EVE PORTS ==========
Eve.add_ports([
    # Quantum input from Alice (ONE qubit)
    "q_port_fromAlice",
    # Quantum output to target (Bob or Charlie)
    "q_port_toBob", "q_port_toCharlie"
])

# ========== CREATE QUANTUM CHANNELS ==========
# Alice → Eve channel (for intercepted qubit)
q_channel_AE = ns.components.QuantumChannel("Channel_Alice_Eve", length=5)

# Eve → Bob channel
q_channel_EB = ns.components.QuantumChannel("Channel_Eve_Bob", length=5)

# Eve → Charlie channel
q_channel_EC = ns.components.QuantumChannel("Channel_Eve_Charlie", length=5)

# Alice → Bob direct channel (when Eve intercepts Charlie)
q_channel_AB = ns.components.QuantumChannel("Channel_Alice_Bob", length=10)

# Alice → Charlie direct channel (when Eve intercepts Bob)
q_channel_AC = ns.components.QuantumChannel("Channel_Alice_Charlie", length=10)

# ========== CREATE CLASSICAL CHANNELS (unchanged) ==========
c_channel_AB = ns.components.ClassicalChannel("ClassicalChannel_Alice_Bob", length=10)
c_channel_AC = ns.components.ClassicalChannel("ClassicalChannel_Alice_Charlie", length=10)
c_channel_BC = ns.components.ClassicalChannel("ClassicalChannel_Bob_Charlie", length=10)
c_channel_CB = ns.components.ClassicalChannel("ClassicalChannel_Charlie_Bob", length=10)

# ========== CONNECT QUANTUM CHANNELS ==========
# Alice → Eve
q_channel_AE.ports["send"].connect(Alice.ports["q_port_toEve"])
q_channel_AE.ports["recv"].connect(Eve.ports["q_port_fromAlice"])

# Eve → Bob
q_channel_EB.ports["send"].connect(Eve.ports["q_port_toBob"])
q_channel_EB.ports["recv"].connect(Bob.ports["q_port_fromEve"])

# Eve → Charlie
q_channel_EC.ports["send"].connect(Eve.ports["q_port_toCharlie"])
q_channel_EC.ports["recv"].connect(Charlie.ports["q_port_fromEve"])

# Alice → Bob (direct)
q_channel_AB.ports["send"].connect(Alice.ports["q_port_toBob"])
q_channel_AB.ports["recv"].connect(Bob.ports["q_port_fromAlice"])

# Alice → Charlie (direct)
q_channel_AC.ports["send"].connect(Alice.ports["q_port_toCharlie"])
q_channel_AC.ports["recv"].connect(Charlie.ports["q_port_fromAlice"])

# ========== CONNECT CLASSICAL CHANNELS (unchanged) ==========
c_channel_AB.ports["send"].connect(Alice.ports["c_port_toBob"])
c_channel_AB.ports["recv"].connect(Bob.ports["c_port_fromAlice"])

c_channel_AC.ports["send"].connect(Alice.ports["c_port_toCharlie"])
c_channel_AC.ports["recv"].connect(Charlie.ports["c_port_fromAlice"])

c_channel_BC.ports["send"].connect(Bob.ports["c_port_toCharlie"])
c_channel_BC.ports["recv"].connect(Charlie.ports["c_port_fromBob"])

c_channel_CB.ports["send"].connect(Charlie.ports["c_port_toBob"])
c_channel_CB.ports["recv"].connect(Bob.ports["c_port_fromCharlie"])

print("=== Network without Eve Setup Complete ===")
print("=== Network with Eve Setup Complete ===")

print("Eve will intercept ONE qubit (either Bob's or Charlie's)")