
# in this context, this program is acting as a client trying to establish a 
# connection to a server. It's not acting as a server waiting for clients to 
# connect to it.



# configure tcp socket server
import socket
import os
import json


def configure_tcp_socket(server_ip: str, server_port: int, servers_json_byte: json) -> None:
    """
    Configures a TCP socket with custom options for low latency (TCP_NODELAY)
    and connection reliability (SO_KEEPALIVE), then connects to a server
    
    :parma server_ip: IP address of the server to connect to
    :param server_port: Port number of the server to connect to
     """

    # Create a socket object for IPv4, TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Disable Nagle's algorithm for this socket to send small packets immediately.
        # reducing the latency for critical, time-sensitive applications like online gaming or VoIP.
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # Enable SO_KEEPALIVE to send keepalive messages for detecting dead connections.
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        # Additional keepalive options for finer control may vary by OS.
        # These options are not universally supported and require OS-specific imports.
        if os.name == 'posix':
            # The following options are for linux as an example.
            client_socket.setsockopt(socket.SOL_TCP, socket.SO_KEEPIDLE, 1) # seconds before starting keepalive probes
            client_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEEPINTVL, 1) # interval between keepalive probes
            client_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5) # failed keepalive probes before declaring other end dead
            
        # Establish a connection to the server
        client_socket.connect((server_ip, server_port))

        print(f"Connected to server at {server_ip}:{server_port} with customized TCP client socket options.\n, TCP_NODELAY\n, SO_KEEPALIVE\n")
        
        # Perform additional operations here...
        client_socket.sendall(servers_json_byte)
        
    except Exception as e:
        print(f"Error configuring TCP socket: {e}")
    finally:
        # Close the socket connection to the server
        client_socket.close()
        print("Socket connection closed.")


# List of servers to monitor in dictionary format
def servers_dict() -> dict:
    """
    Returns a list of servers to monitor in dictionary format.
    """
    # Fixed server list for testing
    # User defines which services to check for each server
    servers = [
        {
            "address": "8.8.8.8",
            "services": ["ping", "icmp", "DNS"],
            "interval": 60
        },

        {
            "address": "http://example.com",
            "services": ["HTTP"],
            "interval": 120
        },
        {
            "address": "https://example.com",
            "services": ["HTTP"],
            "interval": 180
        },

        {
            "address": "www.example.com",
            "services": ["NTP", "TCP", "UDP"],
            "interval": 240
        },
        {
            "address": "127.0.0.1",
            "services": ["udp_echo_client", "udp_echo_client"],
            "interval": 300
        },
    ]
    return servers




if __name__ == "__main__":
    # Specify the server's IP address and port number
    SERVER_IP: str = "127.0.0.1"
    SERVER_PORT: int = 10100
    
    # Convert the dictionary to a JSON string
    json_string = json.dumps(servers_dict(), indent=4)
    
    # Encode the JSON string to bytes
    servers_json_bytes = json_string.encode('utf-8')

    # Configure the TCP socket with custom options and connect to the server
    configure_tcp_socket(SERVER_IP, SERVER_PORT, servers_json_bytes)
    