import socket
import time
import argparse

# Constants
MSS = 1400  # Maximum Segment Size for each packet
WINDOW_SIZE = 10  # Number of packets in flight
DUP_ACK_THRESHOLD = 3  # Threshold for duplicate ACKs to trigger fast recovery
FILE_PATH = "input_file.txt"
timeout = 3.0  # Initialize timeout to some value but update it as ACK packets arrive
def send_file(server_ip, server_port, enable_fast_recovery):
    """
    Send a predefined file to the client, ensuring reliability over UDP.
    """
    # Initialize UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))

    print(f"Server listening on {server_ip}:{server_port}")

    # Wait for client to initiate connection
    client_address = None
    file_path = FILE_PATH  # Predefined file name

    with open(file_path, 'rb') as file:
        seq_num = 0
        window_base = 0
        unacked_packets = {}
        duplicate_ack_count = 0
        last_ack_received = -1

        isTrue=True
        while True:
            while len(unacked_packets)<WINDOW_SIZE: ## Use window-based sending
                chunk = file.read(MSS)
                if not chunk:
                    # End of file
                    # Send end signal to the client 
                    end_packet = "END".encode()
                    server_socket.sendto(end_packet, client_address)
                    
                    break

                # Create and send the packet
                packet = create_packet(seq_num, chunk)
                if client_address:
                    server_socket.sendto(packet, client_address)
                else:
                    
                    print("Waiting for client connection...")
                    data, client_address = server_socket.recvfrom(1024)
                    print(data)
                    if data=="-1|START":
                        print(f"Connection established with client {client_address}")
                    server_socket.sendto(packet, client_address)

                

                

                ## 

                unacked_packets[seq_num] = (packet, time.time())  # Track sent packets
                print(f"Sent packet {seq_num}")
                seq_num += 1
      
            # Wait for ACKs and retransmit if needed
            try:
            	## Handle ACKs, Timeout, Fast retransmit
                server_socket.settimeout(timeout)
                ack_packet, _ = server_socket.recvfrom(1024)
                ack_seq_num = process_buffer(ack_packet)

                if ack_seq_num > last_ack_received:
                    print(f"Received cumulative ACK for packet {ack_seq_num}")
                    for pk in range(last_ack_received,ack_seq_num):
                        if pk in unacked_packets:
                            del unacked_packets[pk]
                    last_ack_received = ack_seq_num
                    # Slide the window forward

                    
                    # Remove acknowledged packets from the buffer 
                    
                


                    
                else:
                    # Duplicate ACK received
                    
                    print(f"Received duplicate ACK for packet {ack_seq_num}, count={duplicate_ack_count}")
                    duplicate_ack_count+=1
                    if enable_fast_recovery and duplicate_ack_count >= DUP_ACK_THRESHOLD:
                        print("Entering fast recovery mode")
                        
                        fast_recovery(server_socket,client_address,unacked_packets)
                        duplicate_ack_count=0

            except socket.timeout:
                # Timeout handling: retransmit all unacknowledged packets
                print("Timeout occurred, retransmitting unacknowledged packets")
                retransmit_unacked_packets(server_socket, client_address, unacked_packets)

            # Check if we are done sending the file
            if not chunk and len(unacked_packets) == 0:
                print("File transfer complete")
                break

def process_buffer(buffer):
    """
    Function to process a buffer that contains multiple packets.
    Each packet is in the format: "seq_num|ACK".
    The buffer may contain several concatenated packets.
    This function extracts each packet, parses the sequence number, 
    and finds the packet with the highest sequence number.
    """
    # First, decode the buffer to a string
    decoded_buffer = buffer.decode()

    # Split the buffer by a newline or other delimiter if packets are separated by it
    # Assuming packets are newline-separated for now
    packets = decoded_buffer.split("\n")
    
    # Remove any empty strings that may result from splitting
    packets = [pkt for pkt in packets if pkt]

    # Initialize variables to track the highest sequence number and the corresponding packet
    max_seq_num = -1
    # max_packet = None

    # Iterate over each packet, extract the sequence number and find the max
    for packet in packets:
        seq_num, _ = parse_ack_packet(packet.encode())  # Re-encode to byte format for parsing
        
        if seq_num > max_seq_num:
            max_seq_num = seq_num
            # max_packet = packet

    return max_seq_num
def parse_ack_packet(packet):
    """
    Function to parse the ack packet and return the sequence number.
    Packet format: "seq_num|ACK"
    """
    # Decode the packet back to a string
    decoded_packet = packet.decode()
    # Split the packet by '|' to extract the sequence number
    seq_num_str, _ = decoded_packet.split('|')
    
    # Convert the sequence number to an integer
    seq_num = int(seq_num_str)
    
    return seq_num, decoded_packet
def create_packet(seq_num, data):
    """
    Create a packet with the sequence number and data.
    """
    return f"{seq_num}|".encode() + data
    

def retransmit_unacked_packets(server_socket, client_address, unacked_packets):
    """
    Retransmit all unacknowledged packets.
    """
    for (packet,time) in unacked_packets.values():
        server_socket.sendto(packet, client_address)
    

def fast_recovery(server_socket, client_address, unacked_packets):
    """
    Retransmit the earliest unacknowledged packet (fast recovery).
    """
    min_seq_num=min(unacked_packets)
    packet,_=unacked_packets[min_seq_num]
    server_socket.sendto(packet, client_address)



    

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Reliable file transfer server over UDP.')
parser.add_argument('server_ip', help='IP address of the server')
parser.add_argument('server_port', type=int, help='Port number of the server')
parser.add_argument('fast_recovery', type=int, help='Enable fast recovery')

args = parser.parse_args()

# Run the server
send_file(args.server_ip, args.server_port, args.fast_recovery)
