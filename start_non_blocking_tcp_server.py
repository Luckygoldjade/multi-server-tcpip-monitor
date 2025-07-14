import socket
import typing
import select

def start_non_blocking_tcp_server(server_ip: str, server_port: int) -> None:
    """
    Starts a non-blocking TCP server that listens on a specified IP address and port number.
    Uses the select module to manage multiple connections efficiently.
    
    :param server_ip: The IP address of the server will listen on.
    :param server_port: The port number the server will listen on.
    """
    # Create a TCP socket object using the IPv4 address family
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set the socket to non-blocking mode
    server_socket.setblocking(False)
    
    # Bind the server socket to the IP address and port number
    server_socket.bind((SERVER_IP, SERVER_PORT))
    
    # Listen for incoming connections (the argument specifies the maximum number of queued connections)
    server_socket.listen(5)
    print(f"Non-blocking TCP server is listening on {server_ip}:{server_port}")
    
    # List of sockets for select.select()
    sockets_list: typing.List[socket.socket] = [server_socket]
    
    try:
        while True:
            # Use select to handle socket I/O without blocking
            # It waits for at least one of the sockets to be ready for processing
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
            
            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    # Accept a new connection
                    client_socket, client_address = server_socket.accept()
                    print(f"Accepted new connection from {client_address}")
                    # Add the new client socket to the list of sockets
                    sockets_list.append(client_socket)
                else:
                    # Receive data from a client socket
                    message: bytes = notified_socket.recv(1024)
                    
                    if message:
                        # A readable client socket has data
                        print(f"Received message from {notified_socket.getpeername()}: {message.decode()}")
                    else:
                        # Close empty connection
                        print(f"Closed connection to {notified_socket.getpeername()}")
                        sockets_list.remove(notified_socket)
                        notified_socket.close()
                        
            # Handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                sockets_list.remove(notified_socket)
                notified_socket.close()
                
    finally:
        # Close the server socket to release resources
        server_socket.close()
        print("Server socket closed")

if __name__ == "__main__":
    SERVER_IP: str = "127.0.0.1"
    SERVER_PORT: int = 10100
    # Start the non-blocking TCP server
    start_non_blocking_tcp_server(SERVER_IP, SERVER_PORT)
