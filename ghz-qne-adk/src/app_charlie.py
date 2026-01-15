from netqasm.sdk import EPRSocket, create_ghz
from netqasm.sdk.external import NetQASMConnection, Socket

def main(app_config=None, num_states=10):
    log_config = app_config.log_config

    down_socket = Socket("charlie", "bob", log_config=log_config)
    down_epr_socket = EPRSocket("bob")

    conn = NetQASMConnection(
        app_name=app_config.app_name, log_config=log_config, epr_sockets=[down_epr_socket]
    )

    measurements = []

    with conn:
        for _ in range(num_states):
            # Create GHZ state
            q, _ = create_ghz(
                down_epr_socket=down_epr_socket, down_socket=down_socket,
                do_corrections=True
            )

            # Measure
            m = q.measure()
            conn.flush()

            # Sync with other parties
            down_socket.recv_silent()
            down_socket.send_silent("")

            measurements.append(int(m))

    return { "measurements": str(measurements) }

if __name__ == "__main__": 
    main()
