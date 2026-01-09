from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import Qubit
import random

def main(app_config=None, x=0, y=0):
    """
    Bob (Receiver 1)
    x, y are network position parameters required by QNE
    """
    
    socket_alice = Socket("bob", "alice", log_config=app_config.log_config)
    socket_charlie = Socket("bob", "charlie", log_config=app_config.log_config)
    
    num_rounds = 100
    bob_bits = []
    bob_bases = []
    
    with NetQASMConnection("bob", log_config=app_config.log_config) as bob:
        
        for round_num in range(num_rounds):
            
            # Choose random basis
            bob_basis = random.choice(['X', 'Y'])
            bob_bases.append(bob_basis)
            
            # Create and measure qubit
            q = Qubit(bob)
            q.H()
            
            if bob_basis == 'Y':
                q.S()
            q.H()
            
            result = q.measure()
            bob.flush()
            
            bob_bits.append(int(result))
            
            # Exchange bases
            alice_basis = socket_alice.recv()
            socket_alice.send(bob_basis)
            
            socket_charlie.send(bob_basis)
            charlie_basis = socket_charlie.recv()
    
    return {
        "role": "bob",
        "total_rounds": num_rounds,
        "sample_bits": bob_bits[:10],
        "sample_bases": bob_bases[:10]
    }

if __name__ == "__main__": 
    main()
