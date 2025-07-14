# Socket Programming - Project 2 SPP2
# CS372 Introduction to Networking
# Tony Chan
# Due 5/15/2024
# Requires the following packages:
# pip install requests
# pip install ntplib
# pip install dnspython

import queue
import json
import sys
import os
import socket
import struct
import threading
import time
from urllib import response
import zlib
import random
import string
import requests
import ntplib
import dns.resolver
import dns.exception
from socket import gaierror
from time import ctime
from typing import Tuple, Optional, Any

import threading
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from timestamp_printing import timestamped_print

# Global variables to hold the client socket and address
client_socket = None
# Create queue to store the results of the service checks
results_queue = queue.Queue()

STATION_IDENTIFIER = "Berlin"
STATION_IDENTIFIER_IP = "127.0.0.1"
STATION_IDENTIFIER_PORT = 10100

# Check if a command-line argument for the station identifier is provided
if len(sys.argv) > 1:
    STATION_IDENTIFIER = sys.argv[1]
    STATION_IDENTIFIER_IP = sys.argv[2]
    STATION_IDENTIFIER_PORT = int(sys.argv[3])
else:
    STATION_IDENTIFIER = "Berlin"  # Default station identifier if not provided
    STATION_IDENTIFIER_IP = "127.0.0.1"
    STATION_IDENTIFIER_PORT = 10100


def start_tcp_server(server_ip: str, server_port: int) -> dict:
    """
    Start a TCP server that listens for incoming connections on a simplified IP address and port number.
    
    :param server_ip: The IP address of the server will listen on.
    :param server_port: The port number the server will listen on.
    """
    # Create a socket object using AF_INET (IPv4) and SOCK_STREAM (TCP)
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
    # Set a large timeout (1 day)
    # server_socket.settimeout(24 * 60 * 60)

    # Bind the server socket to the IP address and port number
    server_socket.bind((server_ip, server_port))
    
    # Listen for incoming connections (the argument specifies the maximum number of queued connections)
    server_socket.listen(5)
    print(f"Server is listening on {server_ip}:{server_port}")
    
    try:
        # while True:
            # Accept an incoming connection (this is a blocking until a connection is received)
            global client_socket
            client_socket, client_address = server_socket.accept()
            print(f"Connection received from {client_address}")
            
            message: bytes = client_socket.recv(2048)
            print(f"Received message: {message.decode('utf-8')}")



            # Handle the client connection
            handle_client_connection(client_socket, message)
    except Exception as e:
        # Handle the error
        print(f"An error occurred: {str(e)}")
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C) gracefully
        print("Server stopped by the user")
        


    # finally:
    #     # Close the server socket to release resources and allow the program to exit cleanly
    #     server_socket.close()
    #     print("Server socket closed")
    return json.loads(message.decode('utf-8'))


def handle_client_connection(client_socket: socket.socket, message) -> None:
    """
    Handles the communication with a connected client.
        
    :param client_socket: The socket object representing the connected client.
    """
    try:
        # Receive data from the client (blocking call, with a maximum buffer size of 1024 bytes)
        # message: bytes = client_socket.recv(1024)
        print(f"Received message: {message.decode('utf-8')}")
            
        # Send a response back to the client with Monitoring Station identifier
        response: str = STATION_IDENTIFIER + ":Message received"
        client_socket.sendall(response.encode('utf-8'))
    except Exception as e:
        # Handle the error
        print(f"An error occurred: {str(e)}")
    # finally:
        # Close the client socket to release resources
        # client_socket.close()
        # print("Client socket closed")


    
def send_message_to_management_service():
    """
    Sends a message to the management service using the existing client socket connection.
    If connected, the message is sent from central mess queue; otherwise, an error message is displayed.
    """
    global client_socket

    if not results_queue.empty():
        if is_connected(client_socket):
            # Dequeue queue and send mess to the management service
            message: str = results_queue.get()
            try:
                client_socket.sendall(message.encode('utf-8'))
                # print(f"Sent message to management service: {message}")
            except ConnectionResetError:
                print("Connection reset. Reconnecting to management service...")
                client_socket = connect_to_management_service(STATION_IDENTIFIER_IP, STATION_IDENTIFIER_PORT)
                if is_connected(client_socket):
                    client_socket.sendall(message.encode('utf-8'))
                    print(f"Sent message to management service: {message}")
                else:
                    print("Failed to reconnect to management service.")
        else:
            print("Client socket is not connected.")




def is_connected(sock):
    try:
        # Set the socket to non-blocking
        sock.setblocking(0)

        # Try to receive some data
        data = sock.recv(16)

        # Set the socket back to blocking
        sock.setblocking(1)

        # If recv() returned an empty string, the connection is closed
        if not data:
            return False
    except BlockingIOError:
        # If a BlockingIOError is raised, it means the socket is still connected
        pass
    except ConnectionResetError:
        # If a ConnectionResetError is raised, it means the connection is closed
        return False

    # If no errors were raised, the connection is open
    return True


def connect_to_management_service(server_ip: str, server_port: int) -> socket.socket:
    """
    Connect to the management service using a TCP socket and handle reconnection.
    """
    # Create a socket object using STATION_IDENTIFIER_IP (IPv4) and STATION_IDENTIFIER_PORT (TCP)
    client_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    while True:
        try:
            # Connect to the management service using the IP address and port number
            client_socket.connect((server_ip, server_port))
            print(f"Connected to management service at {server_ip}:{server_port}")
            return client_socket
        except ConnectionRefusedError:
            # Handle the case where the connection is refused (management service not running)
            print("Connection refused. Management service is not running.")
            time.sleep(5)
        except Exception as e:
            # Handle other exceptions
            print(f"An error occurred: {str(e)}")
    


# Worker thread function
def worker(station_servers_config: list, stop_event: threading.Event) -> None:
    """
    Function run by the worker thread.
    Prints a message every 5 seconds until stop_event is set.
    """
    # Access the station_servers_config dictionary to get the server configurations
    servers = station_servers_config

    # User defines which services to check for each server
    # Create and start a thread for each service
    # Station Servers Config file has designated station and services for each server
    threads = []
    for server in servers:
        for service in server["services"]:
            if STATION_IDENTIFIER == server["station"]:
                t = threading.Thread(target=check_service, args=(server["address"], service, server["interval"], stop_event))
                threads.append(t)
                t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Stop the worker thread
    stop_event.set()






def check_service(address: str, service: str, interval: int, stop_event: threading.Event) -> None:
    """
    Function to check a specific service for a given address at a specified interval.
    """
    while not stop_event.is_set():
        if service.lower() == "ping" or service.lower() == "icmp":
            # Ping Usage Example
            timestamped_print("Ping Example:")
            ping_addr, ping_time = ping(address)
                        
            print_contents = STATION_IDENTIFIER + " : " + (f"{address} (ping): {ping_addr[0]} - {ping_time:.2f} ms" if (ping_addr and ping_time is not None) else f"{address} (ping): Request timed out or no reply received")
            timestamped_print(STATION_IDENTIFIER + " : " + print_contents)      # prints in the monitoring service
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()

        elif service.lower() == "traceroute":
            # Traceroute Usage Example
            # Note: This function is included as an extra to round out the ICMP examples.
            print_contents = STATION_IDENTIFIER + " : " + ("\nTraceroute Example:")
            timestamped_print(STATION_IDENTIFIER + " : " + "\nTraceroute Example:")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()


            print_contents = STATION_IDENTIFIER + " : " + (f"{address} (traceroute):")
            timestamped_print(STATION_IDENTIFIER + " : " + f"{address} (traceroute):")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()
           

            print_contents = STATION_IDENTIFIER + " : " + (traceroute(address))
            timestamped_print(STATION_IDENTIFIER + " : " + traceroute(address))
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()



        elif service.lower() == "http":
            # HTTP/HTTPS Usage Examples
            timestamped_print("\nHTTP/HTTPS Examples:")
            http_url = address
            http_server_status, http_server_response_code = check_server_http(http_url)
            
            
            print_contents = STATION_IDENTIFIER + " : " + (f"HTTP URL: {http_url}, HTTP server status: {http_server_status}, Status Code: {http_server_response_code if http_server_response_code is not None else 'N/A'}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"HTTP URL: {http_url}, HTTP server status: {http_server_status}, Status Code: {http_server_response_code if http_server_response_code is not None else 'N/A'}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()






        elif service.lower() == "https":
            https_url = address
            https_server_status, https_server_response_code, description = check_server_https(https_url)
            
            print_contents = STATION_IDENTIFIER + " : " + (f"HTTPS URL: {https_url}, HTTPS server status: {https_server_status}, Status Code: {https_server_response_code if https_server_response_code is not None else 'N/A'}, Description: {description}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"HTTPS URL: {https_url}, HTTPS server status: {https_server_status}, Status Code: {https_server_response_code if https_server_response_code is not None else 'N/A'}, Description: {description}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()




        elif service.lower() == "ntp":
            # NTP Usage Example
            timestamped_print("\nNTP Example:")
            ntp_server = 'pool.ntp.org'  # Replace with your NTP server
            ntp_server_status, ntp_server_time = check_ntp_server(ntp_server)
            
            
            print_contents = STATION_IDENTIFIER + " : " + (f"{ntp_server} is up. Time: {ntp_server_time}" if ntp_server_status else f"{ntp_server} is down.")
            timestamped_print(STATION_IDENTIFIER + " : " + f"{ntp_server} is up. Time: {ntp_server_time}" if ntp_server_status else f"{ntp_server} is down.")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()



        elif service.lower() == "dns":
            # DNS Usage Examples
            timestamped_print("\nDNS Examples:")
            dns_server = address  # Google's public DNS server

            dns_queries = [
                ('google.com', 'A'),        # IPv4 Address
                ('google.com', 'MX'),       # Mail Exchange
                ('google.com', 'AAAA'),     # IPv6 Address
                ('google.com', 'CNAME'),    # Canonical Name
                ('yahoo.com', 'A'),         # IPv4 Address
            ]

            for dns_query, dns_record_type in dns_queries:
                dns_server_status, dns_query_results = check_dns_server_status(dns_server, dns_query, dns_record_type)
                
                
                print_contents = STATION_IDENTIFIER + " : " + (f"DNS Server: {dns_server}, Status: {dns_server_status}, {dns_record_type} Records Results: {dns_query_results}")
                timestamped_print(STATION_IDENTIFIER + " : " + f"DNS Server: {dns_server}, Status: {dns_server_status}, {dns_record_type} Records Results: {dns_query_results}")
                # results to central messaging queue
                results_queue.put(print_contents)
                send_message_to_management_service()




        elif service.lower() == "tcp":
            # TCP Port Usage Example
            timestamped_print("\nTCP Port Example:")
            tcp_port_server = address
            tcp_port_number = 80
            tcp_port_status, tcp_port_description = check_tcp_port(tcp_port_server, tcp_port_number)
            
            
            print_contents = STATION_IDENTIFIER + " : " + (f"Server: {tcp_port_server}, TCP Port: {tcp_port_number}, TCP Port Status: {tcp_port_status}, Description: {tcp_port_description}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"Server: {tcp_port_server}, TCP Port: {tcp_port_number}, TCP Port Status: {tcp_port_status}, Description: {tcp_port_description}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()



        elif service.lower() == "udp":
            # UDP Port Usage Example
            timestamped_print("\nUDP Port Example:")
            udp_port_server = address
            udp_port_number = 53
            udp_port_status, udp_port_description = check_udp_port(udp_port_server, udp_port_number)
            
            print_contents = STATION_IDENTIFIER + " : " + (f"Server: {udp_port_server}, UDP Port: {udp_port_number}, UDP Port Status: {udp_port_status}, Description: {udp_port_description}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"Server: {udp_port_server}, UDP Port: {udp_port_number}, UDP Port Status: {udp_port_status}, Description: {udp_port_description}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()



        elif service.lower() == "udp_echo_client":
            # UDP Echo Client Talking
            timestamped_print("\nUDP Echo Client Example:")
            udp_port_server = address
            udp_port_number = 10100
            udp_port_status, udp_port_description = check_udp_echo_client(udp_port_server, udp_port_number, "Hello from UDP Echo Client")
            
            print_contents = STATION_IDENTIFIER + " : " + (f"Server: {udp_port_server}, UDP Port: {udp_port_number}, UDP Port Status: {udp_port_status}, Description: {udp_port_description}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"Server: {udp_port_server}, UDP Port: {udp_port_number}, UDP Port Status: {udp_port_status}, Description: {udp_port_description}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()



        time.sleep(interval)






def calculate_icmp_checksum(data: bytes) -> int:
    """
    Calculate the checksum for the ICMP packet.

    The checksum is calculated by summing the 16-bit words of the entire packet,
    carrying any overflow bits around, and then complementing the result.

    Args:
    data (bytes): The data for which the checksum is to be calculated.

    Returns:
    int: The calculated checksum.
    """

    s: int = 0  # Initialize the sum to 0.

    # Iterate over the data in 16-bit (2-byte) chunks.
    for i in range(0, len(data), 2):
        # Combine two adjacent bytes (8-bits each) into one 16-bit word.
        # data[i] is the high byte, shifted left by 8 bits.
        # data[i + 1] is the low byte, added to the high byte.
        # This forms one 16-bit word for each pair of bytes.
        w: int = (data[i] << 8) + (data[i + 1])
        s += w  # Add the 16-bit word to the sum.

    # Add the overflow back into the sum.
    # If the sum is larger than 16 bits, the overflow will be in the higher bits.
    # (s >> 16) extracts the overflow by shifting right by 16 bits.
    # (s & 0xffff) keeps only the lower 16 bits of the sum.
    # The two parts are then added together.
    s = (s >> 16) + (s & 0xffff)

    # Complement the result.
    # ~s performs a bitwise complement (inverting all the bits).
    # & 0xffff ensures the result is a 16-bit value by masking the higher bits.
    s = ~s & 0xffff

    return s  # Return the calculated checksum.


def create_icmp_packet(icmp_type: int = 8, icmp_code: int = 0, sequence_number: int = 1, data_size: int = 192) -> bytes:
    """
    Creates an ICMP (Internet Control Message Protocol) packet with specified parameters.

    Args:
    icmp_type (int): The type of the ICMP packet. Default is 8 (Echo Request).
    icmp_code (int): The code of the ICMP packet. Default is 0.
    sequence_number (int): The sequence number of the ICMP packet. Default is 1.
    data_size (int): The size of the data payload in the ICMP packet. Default is 192 bytes.

    Returns:
    bytes: A bytes object representing the complete ICMP packet.

    Description:
    The function generates a unique ICMP packet by combining the specified ICMP type, code, and sequence number
    with a data payload of a specified size. It calculates a checksum for the packet and ensures that the packet
    is in the correct format for network transmission.
    """

    # Get the current thread identifier and process identifier.
    # These are used to create a unique ICMP identifier.
    thread_id = threading.get_ident()
    process_id = os.getpid()

    # Generate a unique ICMP identifier using CRC32 over the concatenation of thread_id and process_id.
    # The & 0xffff ensures the result is within the range of an unsigned 16-bit integer (0-65535).
    icmp_id = zlib.crc32(f"{thread_id}{process_id}".encode()) & 0xffff

    # Pack the ICMP header fields into a bytes object.
    # 'bbHHh' is the format string for struct.pack, which means:
    # b - signed char (1 byte) for ICMP type
    # b - signed char (1 byte) for ICMP code
    # H - unsigned short (2 bytes) for checksum, initially set to 0
    # H - unsigned short (2 bytes) for ICMP identifier
    # h - short (2 bytes) for sequence number
    header: bytes = struct.pack('bbHHh', icmp_type, icmp_code, 0, icmp_id, sequence_number)

    # Create the data payload for the ICMP packet.
    # It's a sequence of a single randomly chosen alphanumeric character (uppercase or lowercase),
    # repeated to match the total length specified by data_size.
    random_char: str = random.choice(string.ascii_letters + string.digits)
    data: bytes = (random_char * data_size).encode()

    # Calculate the checksum of the header and data.
    chksum: int = calculate_icmp_checksum(header + data)

    # Repack the header with the correct checksum.
    # socket.htons ensures the checksum is in network byte order.
    header = struct.pack('bbHHh', icmp_type, icmp_code, socket.htons(chksum), icmp_id, sequence_number)

    # Return the complete ICMP packet by concatenating the header and data.
    return header + data


def ping(host: str, ttl: int = 64, timeout: int = 1, sequence_number: int = 1) -> Tuple[Any, float] | Tuple[Any, None]:
    """
    Send an ICMP Echo Request to a specified host and measure the round-trip time.

    This function creates a raw socket to send an ICMP Echo Request packet to the given host.
    It then waits for an Echo Reply, measuring the time taken for the round trip. If the specified timeout is exceeded before receiving a reply, the function returns None for the ping time.

    Args:
    host (str): The IP address or hostname of the target host.
    ttl (int): Time-To-Live for the ICMP packet. Determines how many hops (routers) the packet can pass through.
    timeout (int): The time in seconds that the function will wait for a reply before giving up.
    sequence_number (int): The sequence number for the ICMP packet. Useful for matching requests with replies.

    Returns:
    Tuple[Any, float] | Tuple[Any, None]: A tuple containing the address of the replier and the total ping time in milliseconds.
    If the request times out, the function returns None for the ping time. The address part of the tuple is also None if no reply is received.
    """

    # Create a raw socket with the Internet Protocol (IPv4) and ICMP.
    # socket.AF_INET specifies the IPv4 address family.
    # socket.SOCK_RAW allows sending raw packets (including ICMP).
    # socket.IPPROTO_ICMP specifies the ICMP protocol.
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        # Set the Time-To-Live (TTL) for the ICMP packet.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

        # Set the timeout for the socket's blocking operations (e.g., recvfrom).
        sock.settimeout(timeout)

        # Create an ICMP Echo Request packet.
        # icmp_type=8 and icmp_code=0 are standard for Echo Request.
        # sequence_number is used to match Echo Requests with Replies.
        packet: bytes = create_icmp_packet(icmp_type=8, icmp_code=0, sequence_number=sequence_number)

        # Send the ICMP packet to the target host.
        # The second argument of sendto is a tuple (host, port).
        # For raw sockets, the port number is irrelevant, hence set to 1.
        sock.sendto(packet, (host, 1))

        # Record the current time to measure the round-trip time later.
        start: float = time.time()

        try:
            # Wait to receive data from the socket (up to 1024 bytes).
            # This will be the ICMP Echo Reply if the target host is reachable.
            data, addr = sock.recvfrom(1024)

            # Record the time when the reply is received.
            end: float = time.time()

            # Calculate the round-trip time in milliseconds.
            total_ping_time = (end - start) * 1000

            # Return the address of the replier and the total ping time.
            return addr, total_ping_time
        except socket.timeout:
            # If no reply is received within the timeout period, return None for the ping time.
            return None, None


def traceroute(host: str, max_hops: int = 30, pings_per_hop: int = 1, verbose: bool = False) -> str:
    """
    Perform a traceroute to the specified host, with multiple pings per hop.

    Args:
    host (str): The IP address or hostname of the target host.
    max_hops (int): Maximum number of hops to try before stopping.
    pings_per_hop (int): Number of pings to perform at each hop.
    verbose (bool): If True, print additional details during execution.

    Returns:
    str: The results of the traceroute, including statistics for each hop.
    """
    # Header row for the results. Each column is formatted for alignment and width.
    results = [f"{'Hop':>3} {'Address':<15} {'Min (ms)':>8}   {'Avg (ms)':>8}   {'Max (ms)':>8}   {'Count':>5}"]

    # Loop through each TTL (Time-To-Live) value from 1 to max_hops.
    for ttl in range(1, max_hops + 1):
        # Print verbose output if enabled.
        if verbose:
            print_contents = STATION_IDENTIFIER + " : " + (f"pinging {host} with ttl: {ttl}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"pinging {host} with ttl: {ttl}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()



        # List to store ping response times for the current TTL.
        ping_times = []

        # Perform pings_per_hop number of pings for the current TTL.
        for _ in range(pings_per_hop):
            # Ping the host with the current TTL and sequence number.
            # The sequence number is incremented with TTL for each ping.
            addr, response = ping(host, ttl=ttl, sequence_number=ttl)

            # If a response is received (not None), append it to ping_times.
            if response is not None:
                ping_times.append(response)

        # If there are valid ping responses, calculate and format the statistics.
        if ping_times:
            min_time = min(ping_times)  # Minimum ping time.
            avg_time = sum(ping_times) / len(ping_times)  # Average ping time.
            max_time = max(ping_times)  # Maximum ping time.
            count = len(ping_times)  # Count of successful pings.

            # Append the formatted results for this TTL to the results list.
            results.append(f"{ttl:>3} {addr[0] if addr else '*':<15} {min_time:>8.2f}ms {avg_time:>8.2f}ms {max_time:>8.2f}ms {count:>5}")
        else:
            # If no valid responses, append a row of asterisks and zero count.
            results.append(f"{ttl:>3} {'*':<15} {'*':>8}   {'*':>8}   {'*':>8}   {0:>5}")

        # Print the last entry in the results if verbose mode is enabled.
        if verbose and results:
            print_contents = STATION_IDENTIFIER + " : " + (f"\tResult: {results[-1]}")
            timestamped_print(STATION_IDENTIFIER + " : " + f"\tResult: {results[-1]}")
            # results to central messaging queue
            results_queue.put(print_contents)
            send_message_to_management_service()

        # If the address of the response matches the target host, stop the traceroute.
        if addr and addr[0] == host:
            break

    # Join all results into a single string with newline separators and return.
    return '\n'.join(results)


def check_server_http(url: str) -> Tuple[bool, Optional[int]]:
    """
    Check if an HTTP server is up by making a request to the provided URL.

    This function attempts to connect to a web server using the specified URL.
    It returns a tuple containing a boolean indicating whether the server is up,
    and the HTTP status code returned by the server.

    :param url: URL of the server (including http://)
    :return: Tuple (True/False, status code)
             True if server is up (status code < 400), False otherwise
    """
    try:
        # Making a GET request to the server
        response: requests.Response = requests.get(url)

        # The HTTP status code is a number that indicates the outcome of the request.
        # Here, we consider status codes less than 400 as successful,
        # meaning the server is up and reachable.
        # Common successful status codes are 200 (OK), 301 (Moved Permanently), etc.
        is_up: bool = response.status_code < 400

        # Returning a tuple: (True/False, status code)
        # True if the server is up, False if an exception occurs (see except block)
        return is_up, response.status_code

    except requests.RequestException:
        # This block catches any exception that might occur during the request.
        # This includes network problems, invalid URL, etc.
        # If an exception occurs, we assume the server is down.
        # Returning False for the status, and None for the status code,
        # as we couldn't successfully connect to the server to get a status code.
        return False, None


def check_server_https(url: str, timeout: int = 5) -> Tuple[bool, Optional[int], str]:
    """
    Check if an HTTPS server is up by making a request to the provided URL.

    This function attempts to connect to a web server using the specified URL with HTTPS.
    It returns a tuple containing a boolean indicating whether the server is up,
    the HTTP status code returned by the server, and a descriptive message.

    :param url: URL of the server (including https://)
    :param timeout: Timeout for the request in seconds. Default is 5 seconds.
    :return: Tuple (True/False for server status, status code, description)
    """
    try:
        # Setting custom headers for the request. Here, 'User-Agent' is set to mimic a web browser.
        headers: dict = {'User-Agent': 'Mozilla/5.0'}

        # Making a GET request to the server with the specified URL and timeout.
        # The timeout ensures that the request does not hang indefinitely.
        response: requests.Response = requests.get(url, headers=headers, timeout=timeout)

        # Checking if the status code is less than 400. Status codes in the 200-399 range generally indicate success.
        is_up: bool = response.status_code < 400

        # Returning a tuple: (server status, status code, descriptive message)
        return is_up, response.status_code, "Server is up"

    except requests.ConnectionError:
        # This exception is raised for network-related errors, like DNS failure or refused connection.
        return False, None, "Connection error"

    except requests.Timeout:
        # This exception is raised if the server does not send any data in the allotted time (specified by timeout).
        return False, None, "Timeout occurred"

    except requests.RequestException as e:
        # A catch-all exception for any error not covered by the specific exceptions above.
        # 'e' contains the details of the exception.
        return False, None, f"Error during request: {e}"


def check_ntp_server(server: str) -> Tuple[bool, Optional[str]]:
    """
    Checks if an NTP server is up and returns its status and time.

    Args:
    server (str): The hostname or IP address of the NTP server to check.

    Returns:
    Tuple[bool, Optional[str]]: A tuple containing a boolean indicating the server status
                                 (True if up, False if down) and the current time as a string
                                 if the server is up, or None if it's down.
    """
    # Create an NTP client instance
    client = ntplib.NTPClient()

    try:
        # Request time from the NTP server
        # 'version=3' specifies the NTP version to use for the request
        response = client.request(server, version=3)

        # If request is successful, return True and the server time
        # 'ctime' converts the time in seconds since the epoch to a readable format
        return True, ctime(response.tx_time)
    except (ntplib.NTPException, gaierror):
        # If an exception occurs (server is down or unreachable), return False and None
        return False, None


def check_dns_server_status(server, query, record_type) -> tuple[bool, str]:
    """
    Check if a DNS server is up and return the DNS query results for a specified domain and record type.

    :param server: DNS server name or IP address
    :param query: Domain name to query
    :param record_type: Type of DNS record (e.g., 'A', 'AAAA', 'MX', 'CNAME')
    :return: Tuple (status, query_results)
    """
    try:
        # Set the DNS resolver to use the specified server
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [socket.gethostbyname(server)]

        # Perform a DNS query for the specified domain and record type
        query_results = resolver.resolve(query, record_type)
        results = [str(rdata) for rdata in query_results]

        return True, results

    except (dns.exception.Timeout, dns.resolver.NoNameservers, dns.resolver.NoAnswer, socket.gaierror) as e:
        # Return False if there's an exception (server down, query failed, or record type not found)
        return False, str(e)


def check_tcp_port(ip_address: str, port: int) -> tuple[bool, str]:
    """
    Checks the status of a specific TCP port on a given IP address.

    Args:
    ip_address (str): The IP address of the target server.
    port (int): The TCP port number to check.

    Returns:
    tuple: A tuple containing a boolean and a string.
           The boolean is True if the port is open, False otherwise.
           The string provides a description of the port status.

    Description:
    This function attempts to establish a TCP connection to the specified port on the given IP address.
    If the connection is successful, it means the port is open; otherwise, the port is considered closed or unreachable.
    """

    try:
        # Create a socket object using the AF_INET address family (IPv4) and SOCK_STREAM socket type (TCP).
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set a timeout for the socket to avoid waiting indefinitely. Here, 3 seconds is used as a reasonable timeout duration.
            s.settimeout(3)

            # Attempt to connect to the specified IP address and port.
            # If the connection is successful, the port is open.
            s.connect((ip_address, port))
            return True, f"Port {port} on {ip_address} is open."

    except socket.timeout:
        # If a timeout occurs, it means the connection attempt took too long, implying the port might be filtered or the server is slow to respond.
        return False, f"Port {port} on {ip_address} timed out."

    except socket.error:
        # If a socket error occurs, it generally means the port is closed or not reachable.
        return False, f"Port {port} on {ip_address} is closed or not reachable."

    except Exception as e:
        # Catch any other exceptions and return a general failure message along with the exception raised.
        return False, f"Failed to check port {port} on {ip_address} due to an error: {e}"


def check_udp_port(ip_address: str, port: int, timeout: int = 3) -> tuple[bool, str]:
    """
    Checks the status of a specific UDP port on a given IP address.

    Args:
    ip_address (str): The IP address of the target server.
    port (int): The UDP port number to check.
    timeout (int): The timeout duration in seconds for the socket operation. Default is 3 seconds.

    Returns:
    tuple: A tuple containing a boolean and a string.
           The boolean is True if the port is open (or if the status is uncertain), False if the port is definitely closed.
           The string provides a description of the port status.

    Description:
    This function attempts to send a UDP packet to the specified port on the given IP address.
    Since UDP is a connectionless protocol, the function can't definitively determine if the port is open.
    It can only confirm if the port is closed, typically indicated by an ICMP 'Destination Unreachable' response.
    """

    try:
        # Create a socket object using the AF_INET address family (IPv4) and SOCK_DGRAM socket type (UDP).
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Set a timeout for the socket to avoid waiting indefinitely.
            s.settimeout(timeout)

            # Send a dummy packet to the specified IP address and port.
            # As UDP is connectionless, this does not establish a connection but merely sends the packet.
            s.sendto(b'', (ip_address, port))

            try:
                # Try to receive data from the socket.
                # If an ICMP 'Destination Unreachable' message is received, the port is considered closed.
                s.recvfrom(1024)
                return False, f"Port {port} on {ip_address} is closed."

            except socket.timeout:
                # If a timeout occurs, it's uncertain whether the port is open or closed, as no response is received.
                return True, f"Port {port} on {ip_address} is open or no response received."

    except Exception as e:
        # Catch any other exceptions and return a general failure message along with the exception raised.
        return False, f"Failed to check UDP port {port} on {ip_address} due to an error: {e}"


def check_udp_echo_client(server: str, port: int, message: str, timeout: int = 3) -> tuple[bool, str]:
    """
    Sends a UDP message to an echo server and checks if the server echoes the message back correctly.

    Args:
    server (str): The IP address or hostname of the UDP echo server.
    port (int): The UDP port number of the echo server.
    message (str): The message to send to the echo server.
    timeout (int): The timeout duration in seconds for the socket operation. Default is 3 seconds.

    Returns:
    tuple: A tuple containing a boolean and a string.
           The boolean is True if the server echoes the message correctly, False otherwise.
           The string provides a description of the echo server status.
    """

    try:
        # Create a socket object using the AF_INET address family (IPv4) and SOCK_DGRAM socket type (UDP).
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Set a timeout for the socket to avoid waiting indefinitely.
            s.settimeout(timeout)

            # Send the message to the specified server and port.
            s.sendto(message.encode(), (server, port))

            # Receive the echoed message from the server.
            data, addr = s.recvfrom(1024)

            # Check if the received message matches the original message.
            if data.decode() == message:
                return True, f"UDP echo server at {server}:{port} echoed the message correctly."
            else:
                return False, f"UDP echo server at {server}:{port} did not echo the message correctly."

    except Exception as e:
        # Catch any exceptions and return a general failure message along with the exception raised.
        return False, f"Failed to check UDP echo server at {server}:{port} due to an error: {e}"


# Main function
def main() -> None:
    """
    Main function to handle user input and manage threads.
    Uses prompt-toolkit for handling user input with auto-completion and ensures
    the prompt stays at the bottom of the terminal.
    """
    # Management Service and Monitoring Service IP and Port
    # SERVER_IP: str = "127.0.0.1"
    # SERVER_PORT: int = 10100
    station_servers_config = {}
    
    # Start the TCP server
    station_servers_config = start_tcp_server(STATION_IDENTIFIER_IP, STATION_IDENTIFIER_PORT)

    # Event to signal the worker thread to stop
    stop_event: threading.Event = threading.Event()

    # Create and start the worker thread
    worker_thread: threading.Thread = threading.Thread(target=worker, args=(station_servers_config, stop_event))
    worker_thread.start()

    # Command completer for auto-completion
    # This is where you will add new auto-complete commands
    command_completer: WordCompleter = WordCompleter(['exit'], ignore_case=True)

    # Create a prompt session
    session: PromptSession = PromptSession(completer=command_completer)

    # Variable to control the main loop
    is_running: bool = True

    try:
        with patch_stdout():
            while is_running:
                # Using prompt-toolkit for input with auto-completion
                user_input: str = session.prompt("Enter command: ")

                # Once this monitor is running, exiting is the only command available and needed






                if user_input == "exit":
                    timestamped_print("Exiting application...")
                    is_running = False
    finally:
        # Signal the worker thread to stop and wait for its completion
        stop_event.set()
        worker_thread.join()


if __name__ == "__main__":
    main()
    
