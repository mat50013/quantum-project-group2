from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import Qubit
import random

def main(app_config=None, x=0, y=0):
    """
    Charlie (Receiver 2)
    x, y are network position parameters required by QNE
    """
    
    socket_alice = Socket("charlie", "alice", log_config=app_config.log_config)
    socket_bob = Socket("charlie", "bob", log_config=app_config.log_config)
    
    num_rounds = 100
    charlie_bits = []
    charlie_bases = []
    
    with NetQASMConnection("charlie", log_config=app_config.log_config) as charlie:
        
        for round_num in range(num_rounds):
            
            # Choose random basis
            charlie_basis = random.choice(['X', 'Y'])
            charlie_bases.append(charlie_basis)
            
            # Create and measure qubit
            q = Qubit(charlie)
            q.H()
            
            if charlie_basis == 'Y':
                q.S()
            q.H()
            
            result = q.measure()
            charlie.flush()
            
            charlie_bits.append(int(result))
            
            # Exchange bases
            alice_basis = socket_alice.recv()
            socket_alice.send(charlie_basis)
            
            bob_basis = socket_bob.recv()
            socket_bob.send(charlie_basis)
    
    return {
        "role": "charlie",
        "total_rounds": num_rounds,
        "sample_bits": charlie_bits[:10],
        "sample_bases": charlie_bases[:10]
    }


if __name__ == "__main__": 
    main()
