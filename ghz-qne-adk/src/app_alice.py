from netqasm.sdk import EPRSocket, create_ghz
from netqasm.sdk.external import NetQASMConnection, Socket

def main(app_config=None, num_states=10):
    log_config = app_config.log_config

    up_socket = Socket("alice", "bob", log_config=log_config)
    up_epr_socket = EPRSocket("bob")

    conn = NetQASMConnection(
        app_name=app_config.app_name, log_config=log_config, epr_sockets=[up_epr_socket]
    )

    measurements = []

    with conn:
        for _ in range(num_states):
            # Create GHZ state
            q, _ = create_ghz(
                up_epr_socket=up_epr_socket, up_socket=up_socket,
                do_corrections=True
            )

            # Measure
            m = q.measure()
            conn.flush()

            # Sync with other parties
            up_socket.send_silent("")
            up_socket.recv_silent()

            measurements.append(int(m))

    return { "measurements": str(measurements) }

if __name__ == "__main__": 
    main()
