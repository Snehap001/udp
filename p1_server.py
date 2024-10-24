import socket
import time
import argparse
import json
# Constants
MSS = 1400  # Maximum Segment Size for each packet
WINDOW_SIZE = 10  # Number of packets in flight
DUP_ACK_THRESHOLD = 3  # Threshold for duplicate ACKs to trigger fast recovery
FILE_PATH = "input_file.txt"
 # Initialize timeout to some value but update it as ACK packets arrive
import sys
sys.stdout.reconfigure(line_buffering=True)
def find_signal(packet):
    
    # Load the JSON data
    packet_info = json.loads(packet)
    return packet_info['signal']

def send_file(server_ip, server_port, enable_fast_recovery):
    """
    Send a predefined file to the client, ensuring reliability over UDP.
    """
    # Initialize UDP socket

    SAMPLE_RTT=0.05
    ALPHA=0.125
    BETA=0.25
    ESTIMATED_RTT=0.025
    DEV_RTT=BETA*(abs(SAMPLE_RTT-ESTIMATED_RTT))
    timeout = ESTIMATED_RTT+4*DEV_RTT 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))

    print(f"Server listening on {server_ip}:{server_port}")

    # Wait for client to initiate connection
    client_address = None
    file_path = FILE_PATH  # Predefined file name
    connection=False
    while True:
        try:
            print("Waiting for client connection...")
            data, client_address = server_socket.recvfrom(1024)
            data_packet=data.decode().split('<EOP>')
            sign=find_signal(data_packet[0])
            
            if sign=="START":
                print(f"Connection established with client {client_address}")
                break
                 
        except socket.timeout:
            print("waiting")
    with open(file_path, 'rb') as file:
        seq_num = 0
        window_base = 0
        unacked_packets = {}
        duplicate_ack_count = 0
        last_ack_received = -1

        isTrue=True
        eof=False
        while True:
            while len(unacked_packets)<WINDOW_SIZE: ## Use window-based sending
                chunk = file.read(MSS)
                start_time=time.time()
                if not chunk :
                    # End of file
                    # Send end signal to the client 
                    eof=True
                    break
                
                # Create and send the packet
                packet = create_packet(seq_num, chunk)

                
                server_socket.sendto(packet, client_address)
                

                ## 

                unacked_packets[seq_num] = (packet, time.time())  # Track sent packets
                print(f"Sent packet {seq_num}")
                seq_num += 1
            print(f"len of unacked packets: {len(unacked_packets)} ")
            if eof and len(unacked_packets)==0:
                packet_info = {
                        'signal': "END",
                          # Convert bytes to string for JSON serialization
                          'seq_num':seq_num,
                          'data':"END"
                }
                
                # Convert the packet_info dictionary to a JSON string and append a newline
                json_packet = json.dumps(packet_info)
                json_packet+="<EOP>"
                
                
                end_packet = json_packet.encode() 
                while True:
                    server_socket.sendto(end_packet, client_address)
                    try:
                        packet_data, _ = server_socket.recvfrom(1024)
                        receive=packet_data.decode().split('<EOP>')
                        sign=find_signal(receive[0])
                        if sign=="RECEIVE":
                            break
                    except socket.timeout:
                        print("again sending")
                print("File transfer complete")
                break
            # Wait for ACKs and retransmit if needed
            try:
            	## Handle ACKs, Timeout, Fast retransmit
            
                server_socket.settimeout(timeout)
                ack_packet, _ = server_socket.recvfrom(1024)
                data_packet=ack_packet.decode().split('<EOP>')
                sign=find_signal(data_packet[0])
                if sign!="ACK":
                    continue
                ack_seq_num = process_buffer(ack_packet)
                end_time=time.time()
                
                
                if ack_seq_num > last_ack_received:
                    if ack_seq_num-1 in unacked_packets:
                        
                        SAMPLE_RTT=end_time-unacked_packets[ack_seq_num-1][1]
                        ESTIMATED_RTT=(1-ALPHA)*ESTIMATED_RTT+ALPHA*SAMPLE_RTT
                        DEV_RTT=(1-BETA)*DEV_RTT+BETA*(abs(SAMPLE_RTT-ESTIMATED_RTT))
                        timeout=ESTIMATED_RTT+4*DEV_RTT
                        print(timeout)
                    print(f"Received cumulative ACK for packet {ack_seq_num}")
                    for pk in range(last_ack_received,ack_seq_num):
                        if pk in unacked_packets:
                            del unacked_packets[pk]
                    last_ack_received = ack_seq_num
                    duplicate_ack_count=0

                else:
                    # Duplicate ACK received
                    
                    print(f"Received duplicate ACK for packet {ack_seq_num}, count={duplicate_ack_count}")
                    
                    duplicate_ack_count+=1
                    if enable_fast_recovery and duplicate_ack_count >= DUP_ACK_THRESHOLD:
                        print("Entering fast recovery mode")
                        
                        fast_recovery(server_socket,client_address,unacked_packets)
                        
                    

            except socket.timeout:
                # Timeout handling: retransmit all unacknowledged packets
                # update_timeout()
                
                print("Timeout occurred, retransmitting unacknowledged packets")
                print(len(unacked_packets))
                retransmit_unacked_packets(server_socket, client_address, unacked_packets)

            # Check if we are done sending the file
    server_socket.close()

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

    packets = decoded_buffer.split("<EOP>")
    
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
    Parse the packet (in JSON format) to extract the sequence number.
    """
    decoded_packet = packet.decode()
    
    # Load the JSON data
    packet_info = json.loads(decoded_packet)
    
    seq_num = packet_info['seq_num']
    
    return seq_num, packet_info
def create_packet(seq_num, data):
    """
    Create a packet with the sequence number and data as a JSON object, and append a newline.
    """
    packet_info = {
        'seq_num': seq_num,
        'length': len(data),
        'data': data.decode(),
        'signal':"DATA" # Convert bytes to string for JSON serialization
    }
    
    # Convert the packet_info dictionary to a JSON string and append a newline
    json_packet = json.dumps(packet_info)
    json_packet+="<EOP>"
    
    return json_packet.encode()  # Convert to bytes before sending

def read_until_delimiter(sock, delimiter="<EOP>"):
    """
    Read from the socket buffer until the custom delimiter is encountered.
    """
    buffer = ''
    while True:
        # Receive data in chunks
        chunk, _ = sock.recvfrom(1024)
        buffer += chunk.decode()  # Decode to string and append to buffer
        print(buffer)
        
        # Check if the custom delimiter is in buffer (end of one packet)
        if delimiter in buffer:
            # Split the buffer at the delimiter
            packet, remaining_buffer = buffer.split(delimiter, 1)
            
            # Return the complete packet and the remaining buffer
            return packet, remaining_buffer

    

def retransmit_unacked_packets(server_socket, client_address, unacked_packets):
    """
    Retransmit all unacknowledged packets.
    """
    for seq_num,(packet,time) in unacked_packets.items():
        print(f"retransmitted packet: {seq_num}")
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
