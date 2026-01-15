from netqasm.sdk import EPRSocket, create_ghz
from netqasm.sdk.external import NetQASMConnection, Socket

def main(app_config=None, num_states=10):
    log_config = app_config.log_config

    down_socket = Socket("bob", "alice", log_config=log_config)
    up_socket = Socket("bob", "charlie", log_config=log_config)

    down_epr_socket = EPRSocket("alice")
    up_epr_socket = EPRSocket("charlie")

    conn = NetQASMConnection(
        app_name=app_config.app_name, log_config=log_config, epr_sockets=[down_epr_socket, up_epr_socket]
    )

    measurements = []

    with conn:
        for _ in range(num_states):
            # Create GHZ state
            q, _ = create_ghz(
                down_epr_socket=down_epr_socket, up_epr_socket=up_epr_socket,
                down_socket=down_socket, up_socket=up_socket,
                do_corrections=True
            )

            # Measure
            m = q.measure()
            conn.flush()

            # Sync with other parties
            down_socket.recv_silent()
            down_socket.send_silent("")
            up_socket.send_silent("")
            up_socket.recv_silent()

            measurements.append(int(m))

    return { "measurements": str(measurements) }

if __name__ == "__main__": 
    main()
