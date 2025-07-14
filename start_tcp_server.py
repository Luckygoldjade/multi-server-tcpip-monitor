import socket

def start_tcp_server(server_ip: str, server_port: int) -> None:
    """
    Start a TCP server that listens for incoming connections on a simplified IP address and port number.
    
    :param server_ip: The IP address of the server will listen on.
    :param server_port: The port number the server will listen on.
    """
    # Create a socket object using AF_INET (IPv4) and SOCK_STREAM (TCP)
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the server socket to the IP address and port number
    server_socket.bind((server_ip, server_port))
    
    # Listen for incoming connections (the argument specifies the maximum number of queued connections)
    server_socket.listen(5)
    print(f"Server is listening on {server_ip}:{server_port}")
    
    try:
        while True:
            # Accept an incoming connection (this is a blocking until a connection is received)
            client_socket, client_address = server_socket.accept()
            print(f"Connection received from {client_address}")
            
            message: bytes = client_socket.recv(1024)
            print(f"Received message: {message.decode()}")



            # Handle the client connection
            handle_client_connection(client_socket, message)
    finally:
        # Close the server socket to release resources and allow the program to exit cleanly
        server_socket.close()
        print("Server socket closed")


def handle_client_connection(client_socket: socket.socket, message) -> None:
    """
    Handles the communication with a connected client.
        
    :param client_socket: The socket object representing the connected client.
    """
    try:
        # Receive data from the client (blocking call, with a maximum buffer size of 1024 bytes)
        # message: bytes = client_socket.recv(1024)
        print(f"Received message: {message.decode()}")
            
        # Send a response back to the client
        response: str = "Message received"
        client_socket.sendall(response.encode())
    finally:
        # Close the client socket to release resources
        client_socket.close()
        print("Client socket closed")


if __name__ == "__main__":
    # Management Service and Monitoring Service IP and Port
    SERVER_IP: str = "127.0.0.1"
    SERVER_PORT: int = 10100
    
    # Start the TCP server
    start_tcp_server(SERVER_IP, SERVER_PORT)
    