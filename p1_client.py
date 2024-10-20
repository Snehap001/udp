import socket
import argparse
import time
# Constants
MSS = 1400  # Maximum Segment Size
buffer = {}
def receive_file(server_ip, server_port):
    """
    Receive the file from the server with reliability, handling packet loss
    and reordering.
    """
    # Initialize UDP socket
    
    ## Add logic for handling packet loss while establishing connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2)  # Set timeout for server response

    server_address = (server_ip, server_port)
    expected_seq_num = 0
    output_file_path = "received_file.txt"  # Default file name
    k=0
    with open(output_file_path, 'wb') as file:
        num=-1
        client_socket.sendto(b"-1|START", server_address)
        while True:

            try:
                # Send initial connection request to server
                
                # Receive the packet
                packet, _ = client_socket.recvfrom(MSS + 100)  # Allow room for headers
                
                # Logic to handle end of file
                end_signal=packet.decode()
                if end_signal=="END" :
                    while expected_seq_num in buffer:
                        file.write(buffer.pop(expected_seq_num))  # Write the next in-order packet from the buffer
                        print(f"Buffered packet {expected_seq_num}, writing to file")
                        expected_seq_num += 1
                    print("Received END signal from server, file transfer complete")
                    break
                
                seq_num, data = parse_packet(packet)
                # print(f"received seq num {seq_num}")
                # If the packet is in order, write it to the file
                if seq_num == expected_seq_num:
                    file.write(data)
                    print(f"Received packet {seq_num}, writing to file")
                    expected_seq_num+=1
                    # Update expected seq number and send cumulative ACK for the received packet
                    send_ack(client_socket, server_address, expected_seq_num)
                    while expected_seq_num in buffer:
                        file.write(buffer.pop(expected_seq_num))  # Write the next in-order packet from the buffer
                        print(f"Buffered packet {expected_seq_num}, writing to file")
                        expected_seq_num += 1
                        send_ack(client_socket, server_address, expected_seq_num)
                elif seq_num < expected_seq_num:
                    # Duplicate or old packet, send ACK again
                    send_ack(client_socket, server_address, seq_num)
                else:
                    # packet arrived out of order
                    # handle_pkt()
                    buffer[seq_num] = data  # Store the packet's data in the buffer
                    print(f"Out-of-order packet {seq_num}, buffering it")
                   
                    send_ack(client_socket, server_address, expected_seq_num)


                k+=1

            except socket.timeout:
                print("Timeout waiting for data")
                
                

def parse_packet(packet):
    """
    Parse the packet to extract the sequence number and data.
    """
    seq_num, data = packet.split(b'|', 1)
    return int(seq_num), data

def send_ack(client_socket, server_address, seq_num):
    """
    Send a cumulative acknowledgment for the received packet.
    """
    ack_packet = f"{seq_num}|ACK".encode()
    client_socket.sendto(ack_packet, server_address)
    print(f"Sent cumulative ACK for packet {seq_num}")


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Reliable file receiver over UDP.')
parser.add_argument('server_ip', help='IP address of the server')
parser.add_argument('server_port', type=int, help='Port number of the server')

args = parser.parse_args()

# Run the client
receive_file(args.server_ip, args.server_port)

