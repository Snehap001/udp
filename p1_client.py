import socket
import argparse
import time
import json
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

    packet_info = {
            'signal': "START",
                # Convert bytes to string for JSON serialization
        }
        
    # Convert the packet_info dictionary to a JSON string and append a newline
    json_packet = json.dumps(packet_info)
    json_packet+="<EOP>"
    
    
    start_packet = json_packet.encode() 
    while True:
        try:
            client_socket.sendto(start_packet, server_address)
            packet_data, _ = client_socket.recvfrom(MSS + 100) 
            start=packet_data.decode().split('<EOP>')
            sign=find_signal(start[0])
            if sign=="CONNECT":
                print(f"Connection established with server")
                packet_info = {
                    'signal': "RECEIVE",
                        # Convert bytes to string for JSON serialization
                }
                
                # Convert the packet_info dictionary to a JSON string and append a newline
                json_packet = json.dumps(packet_info)
                json_packet+="<EOP>"
                
                
                receive_packet = json_packet.encode() 
                client_socket.sendto(receive_packet, server_address)


                break
        except socket.timeout:
            print("waiting for reply")

    with open(output_file_path, 'wb') as file:
        
        


        file_transfer_ongoing=True
        while file_transfer_ongoing:

            try:
                # Send initial connection request to server
                
                # Receive the packet
                packet_data, _ = client_socket.recvfrom(MSS + 100)  # Allow room for headers

                packets = packet_data.decode().split('<EOP>')
             
                for packet in packets[:-1]:
                    
                    # Logic to handle end of file
                  
                    end_signal=find_signal(packet)
                    if end_signal=="CONNECT":
                        client_socket.sendto(receive_packet, server_address)
                        break

                    if end_signal=="END" :
                        while expected_seq_num in buffer:
                            file.write(buffer.pop(expected_seq_num))  # Write the next in-order packet from the buffer
                            print(f"Buffered packet {expected_seq_num}, writing to file")
                            expected_seq_num += 1
                        print("Received END signal from server, file transfer complete")
                        file_transfer_ongoing=False
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

    client_socket.close()
                
                
def find_signal(packet):
    
    packet_info = json.loads(packet)
    return packet_info['signal']
def parse_packet(packet):
    """
    Parse the packet (in JSON format) to extract the sequence number.
    """
    
    
    # Load the JSON data
    packet_info = json.loads(packet)
    
    seq_num = packet_info['seq_num']
    data=packet_info['data'].encode()
    return seq_num, data
def create_packet(seq_num):
    """
    Create a packet with the sequence number and data as a JSON object, and append a newline.
    """
    packet_info = {
        'seq_num': seq_num,
        'signal':"ACK"
         # Convert bytes to string for JSON serialization
    }
    
    # Convert the packet_info dictionary to a JSON string and append a newline
    json_packet = json.dumps(packet_info)
    json_packet+="<EOP>"
    
    return json_packet.encode()  # Convert to bytes before sending

def send_ack(client_socket, server_address, seq_num):
    """
    Send a cumulative acknowledgment for the received packet.
    """
    ack_packet = create_packet(seq_num)
    client_socket.sendto(ack_packet, server_address)
    print(f"Sent cumulative ACK for packet {seq_num}")


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Reliable file receiver over UDP.')
parser.add_argument('server_ip', help='IP address of the server')
parser.add_argument('server_port', type=int, help='Port number of the server')

args = parser.parse_args()

# Run the client
receive_file(args.server_ip, args.server_port)

