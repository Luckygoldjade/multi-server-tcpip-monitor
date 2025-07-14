# Socket Programming - Project 2 SPP2
# CS372 Introduction to Networking
# Tony Chan
# Due 5/15/2024
# Requires the following packages:
# pip install prompt-toolkit

import os
import socket
import json
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from monitoring_service import STATION_IDENTIFIER_PORT
from timestamp_printing import timestamped_print

STATION_IDENTIFIER_1 = "Berlin"
STATION_IDENTIFIER_1_IP = "127.0.0.1"
STATION_IDENTIFIER_1_PORT = 10100
STATION_IDENTIFIER_2 = "Hong Kong"
STATION_IDENTIFIER_2_IP = "127.0.0.1"
STATION_IDENTIFIER_2_PORT = 10202

# Declare client_socket as a global variable
client_socket = None

# function to configure the TCP socket with custom options
def configure_tcp_socket(server_ip: str, server_port: int, servers_json_byte: json) -> None:
    """
    Configures a TCP socket with custom options for low latency (TCP_NODELAY)
    and connection reliability (SO_KEEPALIVE), then connects to a server
    
    :parma server_ip: IP address of the server to connect to
    :param server_port: Port number of the server to connect to
    """
    global client_socket  # Access the global client_socket variable

    while True:
        try:
            # Create a new socket object for IPv4, TCP
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Disable Nagle's algorithm for this socket to send small packets immediately.
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
            # Enable SO_KEEPALIVE to send keepalive messages for detecting dead connections.
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
            # Additional keepalive options for finer control may vary by OS.
            if os.name == 'posix':
                client_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
                client_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
                client_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)
            
            # Establish a connection to the server
            client_socket.connect((server_ip, server_port))
            print(f"Connected to server at {server_ip}:{server_port} with customized TCP client socket options.\nTCP_NODELAY\nSO_KEEPALIVE\n")
            client_socket.sendall(servers_json_byte)
            print("Sent server list to Monitoring Service.")
        
            # Receive initial response from the server
            response = client_socket.recv(2048)
            response_str = response.decode('utf-8')

            # Extract the station identifier and response message
            station_identifier = response_str.split(':')[0]
            response_str = response_str.split(':')[1]

            # Print the response with the station identifier
            print(f"Received response from {station_identifier} Monitoring Service: {response_str}")
        
            # Exit the loop if the connection is successful
            break

        except ConnectionRefusedError:
            print(f"Connection refused. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Error configuring TCP socket: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            # Handle keyboard interrupt (Ctrl+C) gracefully
            print("Keyboard interrupt detected. Exiting...")
            break

def reconnect_client(server_ip: str, server_port: int, servers_json_byte: json) -> None:
    while True:
        try:
            configure_tcp_socket(server_ip, server_port, servers_json_byte)
            print("Reconnected to the server.")
            break
        except socket.error as e:
            print(f"Reconnection failed: {e}")
            time.sleep(5)  # Wait before trying to reconnect

def receive_and_print_response(server_ip: str, server_port: int, servers_json_byte: json) -> None:
    global client_socket
    while True:
        try:
            response = client_socket.recv(2048)
            response_str = response.decode('utf-8')
                    
            # Detect server disconnection
            if not response:
                timestamped_print("No more data received. Closing connection.")
                raise ConnectionError("Server disconnected")

            timestamped_print(f"Received response: {response_str}")

        except (socket.error, ConnectionError):
            timestamped_print("Connection lost. Attempting to reconnect...")
            client_socket.close()
            reconnect_client(server_ip, server_port, servers_json_byte)  # Attempt to reconnect
            break  # Exit the loop when there is a connection error

# List of servers to monitor in dictionary format
def servers_dict() -> list:
    """
    Returns a list of servers to monitor in dictionary format.
    """
    # Fixed server list for testing
    # User defines which services to check for each server
    servers = [
        {
            "address": "8.8.8.8",
            "services": ["ping", "icmp", "DNS"],
            "interval": 60,
            "station": "Berlin"
        },
        {
            "address": "http://example.com",
            "services": ["HTTP"],
            "interval": 120,
            "station": "Berlin"
        },
        {
            "address": "https://example.com",
            "services": ["HTTP"],
            "interval": 180,
            "station": "Berlin"
        },
        {
            "address": "www.example.com",
            "services": ["NTP", "TCP", "UDP"],
            "interval": 240,
            "station": "Berlin"
        },
        {
            "address": "127.0.0.1",
            "services": ["udp_echo_client", "udp_echo_client"],
            "interval": 300,
            "station": "Berlin"
        },
        {
            "address": "8.8.8.8",
            "services": ["ping", "icmp", "DNS"],
            "interval": 60,
            "station": "Hong Kong"
        },
        {
            "address": "http://example.com",
            "services": ["HTTP"],
            "interval": 120,
            "station": "Hong Kong"
        },
        {
            "address": "https://example.com",
            "services": ["HTTP"],
            "interval": 180,
            "station": "Hong Kong"
        },
        {
            "address": "www.example.com",
            "services": ["NTP", "TCP", "UDP"],
            "interval": 240,
            "station": "Hong Kong"
        },
        {
            "address": "127.0.0.1",
            "services": ["udp_echo_client", "udp_echo_client"],
            "interval": 300,
            "station": "Hong Kong"
        },
    ]
    return servers

# Main function
def main() -> None:
    """
    Uses prompt-toolkit for handling user input with auto-completion and ensures
    the prompt stays at the bottom of the terminal.
    """
    # Specify the server's IP address and port number
    # SERVER_IP: str = "127.0.0.1"

    # Convert the dictionary to a JSON string
    json_string = json.dumps(servers_dict(), indent=4)
    
    # Encode the JSON string to bytes
    servers_json_bytes = json_string.encode('utf-8')

    # Command completer for auto-completion
    # This is where you will add new auto-complete commands
    command_completer: WordCompleter = WordCompleter(['exit'], ignore_case=True)

    # Variable to control the main loop
    is_running: bool = True
    
    # Run Without using prompt-toolkit for input
    # Berlin station
    # timestamped_print(f"Sending station configuration to {STATION_IDENTIFIER_1} Monitoring Service...")
    # configure_tcp_socket(STATION_IDENTIFIER_1_IP, STATION_IDENTIFIER_1_PORT, servers_json_bytes)
    # receive_and_print_response(STATION_IDENTIFIER_1_IP, STATION_IDENTIFIER_1_PORT, servers_json_bytes)
    
    # Hong Kong station
    # timestamped_print(f"Sending station configuration to {STATION_IDENTIFIER_2} Monitoring Service...")
    # configure_tcp_socket(STATION_IDENTIFIER_2_IP, STATION_IDENTIFIER_2_PORT, servers_json_bytes)
    # receive_and_print_response(STATION_IDENTIFIER_2_IP, STATION_IDENTIFIER_2_PORT, servers_json_bytes)

    # Create a prompt session
    session: PromptSession = PromptSession(completer=command_completer)

    try:
        with patch_stdout():
            while is_running:
                # Using prompt-toolkit for input with auto-completion
                user_input: str = session.prompt("Enter command: ")

                # Configure the TCP socket with custom options and connect to the server
                if user_input == "Berlin":
                    timestamped_print(f"Sending station configuration to {STATION_IDENTIFIER_1} Monitoring Service...")
                    configure_tcp_socket(STATION_IDENTIFIER_1_IP, STATION_IDENTIFIER_1_PORT, servers_json_bytes)
                    receive_and_print_response(STATION_IDENTIFIER_1_IP, STATION_IDENTIFIER_1_PORT, servers_json_bytes)

                if user_input == "Hong Kong":
                    timestamped_print(f"Sending station configuration to {STATION_IDENTIFIER_2} Monitoring Service...")
                    configure_tcp_socket(STATION_IDENTIFIER_2_IP, STATION_IDENTIFIER_2_PORT, servers_json_bytes)
                    receive_and_print_response(STATION_IDENTIFIER_2_IP, STATION_IDENTIFIER_2_PORT, servers_json_bytes)

                if user_input == "exit":
                    timestamped_print("Exiting application...")
                    is_running = False
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C) gracefully
        timestamped_print("Keyboard interrupt detected. Exiting...")
    finally:
        # Close socket connections and cleanup
        if client_socket:
            client_socket.close()
        print("Cleaning up and exiting...")
    return 0

if __name__ == "__main__":
    main()
