from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk import Qubit
import random

def main(app_config=None, x=0, y=0):
    """
    Alice (Dealer) - Creates GHZ states and distributes
    x, y are network position parameters required by QNE
    """
    
    # Classical sockets
    socket_bob = Socket("alice", "bob", log_config=app_config.log_config)
    socket_charlie = Socket("alice", "charlie", log_config=app_config.log_config)
    
    num_rounds = 100
    alice_bits = []
    alice_bases = []
    valid_count = 0
    
    with NetQASMConnection("alice", log_config=app_config.log_config) as alice:
        
        for round_num in range(num_rounds):
            
            # Choose random basis
            alice_basis = random.choice(['X', 'Y'])
            alice_bases.append(alice_basis)
            
            # Create qubit and measure
            q = Qubit(alice)
            q.H()  # Create superposition
            
            # Measure in chosen basis
            if alice_basis == 'Y':
                q.S()
            q.H()
            
            result = q.measure()
            alice.flush()
            
            alice_bits.append(int(result))
            
            # Exchange bases
            socket_bob.send(alice_basis)
            socket_charlie.send(alice_basis)
            
            bob_basis = socket_bob.recv()
            charlie_basis = socket_charlie.recv()
            
            # Check validity (even number of Y's)
            y_count = [alice_basis, bob_basis, charlie_basis].count('Y')
            if y_count % 2 == 0:
                valid_count += 1
    
    return {
        "role": "alice",
        "total_rounds": num_rounds,
        "valid_rounds": valid_count,
        "key_rate": valid_count / num_rounds,
        "sample_bits": alice_bits[:10],
        "sample_bases": alice_bases[:10]
    }

if __name__ == "__main__": 
    main()
