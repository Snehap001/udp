import socket
import time
import argparse
import json
class Mode(object):
    slow_start=0
    congestion_avoidance=1
    fast_recovery=2
# Constants
MSS = 1400  # Maximum Segment Size for each packet
DUP_ACK_THRESHOLD = 3  # Threshold for duplicate ACKs to trigger fast recovery
FILE_PATH = "input_file.txt"
 # Initialize timeout to some value but update it as ACK packets arrive
congestion_control={
    "cwnd":1,
    "dec_factor":2,
    "ssthres":1000,
    "W_max":1,
    "beta_cubic":0.5,
    "C":0.4,
    "time":0,
    "timeout":False
    
}
#Contains the state of the retransmission timer
rtt={
    'alpha':0.125,
    'beta':0.25,
    'k':4,
    'est_rtt':-1,
    'dev_rtt':-1
}

import sys
sys.stdout.reconfigure(line_buffering=True)
def w_est(congestion_control,RTT):
    t=time.time()-(congestion_control["time"])
    w_max=congestion_control["W_max"]
    beta=congestion_control["beta_cubic"]
    return (w_max*beta) +(3*(1-beta)/(1+beta))*(t/RTT)

def w_cubic(congestion_control,time,k_value):
    t=time-(congestion_control["time"])
    w_max=congestion_control["W_max"]
    beta=congestion_control["beta_cubic"]
    c=congestion_control["C"]
    if k_value==0:
        
        value=(w_max*(1-beta)/c)
        k=pow(value,0.33)
    else:
        k=0
    return c*pow((t-k),3) + w_max
def find_signal(packet):
    
    # Load the JSON data
    packet_info = json.loads(packet)
    return packet_info['signal']

def send_file(server_ip, server_port):
    """
    Send a predefined file to the client, ensuring reliability over UDP.
    """
    # Initialize UDP socket

    timeout=1

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
            print(f"len_data : {len(data)}")            
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

        eof=False
        mode=Mode.slow_start
        while True:
            while len(unacked_packets)<congestion_control['cwnd']: ## Use window-based sending
                chunk = file.read(MSS)
                if not chunk :
                    # End of file
                    # Send end signal to the client 
                    eof=True
                    break
                
                # Create and send the packet
                packet = create_packet(seq_num, chunk)

                server_socket.sendto(packet, client_address)

                ## 

                unacked_packets[seq_num] = [packet, time.time(),False]  # Track sent packets
                print(f"Sent packet {seq_num}")
                seq_num += 1
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
                        print(f"len_data : {len(packet_data)}")
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
                end_time=time.time()
                print(f"len_data : {len(ack_packet)}")                
                data_packet=ack_packet.decode().split('<EOP>')
                sign=find_signal(data_packet[0])
                if sign!="ACK":
                    continue
                ack_seq_num = process_buffer(ack_packet)
                if(rtt["est_rtt"]==(-1)):
                    timeout=1
                else:
                    timeout = max(rtt['est_rtt'] + rtt['k'] * rtt['dev_rtt'], 0.001)
                print(f'New timeout : {timeout}')                 
                if ack_seq_num > last_ack_received:
                    print(f"Received cumulative ACK for packet {ack_seq_num}")

                    if( not(unacked_packets[ack_seq_num-1][2] )):
                        if(rtt["est_rtt"]==(-1)):
                            SAMPLE_RTT=end_time-unacked_packets[ack_seq_num-1][1]
                            rtt['est_rtt']=SAMPLE_RTT
                            rtt['dev_rtt']=SAMPLE_RTT/2
                            print("timeout calculated")
                        else:
                            SAMPLE_RTT=end_time-unacked_packets[ack_seq_num-1][1]
                            rtt['dev_rtt']=(1-rtt['beta'])*rtt['dev_rtt']+rtt['beta']*(abs(SAMPLE_RTT-rtt['est_rtt']))
                            rtt['est_rtt']=(1-rtt['alpha'])*rtt['est_rtt']+rtt['alpha']*SAMPLE_RTT
                        timeout = max(rtt['est_rtt'] + rtt['k'] * rtt['dev_rtt'], 0.001)



                    for pk in range(last_ack_received,ack_seq_num):
                        if pk in unacked_packets:
                            del unacked_packets[pk]
                    last_ack_received = ack_seq_num
                    duplicate_ack_count=0
                    if(mode==Mode.slow_start):
                        congestion_control["cwnd"]=congestion_control["cwnd"]+1
                        if(congestion_control["cwnd"]>=congestion_control["ssthres"]):
                            mode=Mode.congestion_avoidance
                            congestion_control["time"]=time.time()
                    elif(mode==Mode.congestion_avoidance):  
                        k=congestion_control["timeout"]==True
                        if congestion_control["timeout"]==True:
                            congestion_control["W_max"]=congestion_control["cwnd"]
                            
                            cubic=w_cubic(congestion_control,time.time(),k)
                        else:
                            cubic=w_cubic(congestion_control,time.time(),k)

                        est=w_est(congestion_control,rtt["est_rtt"])
                        if cubic<est:
                            congestion_control["cwnd"]=est
                        elif congestion_control["cwnd"]<congestion_control["W_max"]:
                            cwnd=congestion_control["cwnd"]
                            cubic_rtt=w_cubic(congestion_control,time.time()+rtt["est_rtt"],k)
                            congestion_control["cwnd"]=cwnd+((cubic_rtt-cwnd)/cwnd)
                        elif congestion_control["cwnd"]>=congestion_control["W_max"]:
                            cwnd=congestion_control["cwnd"]
                            cubic_rtt=w_cubic(congestion_control,time.time()+rtt["est_rtt"],k)
                            congestion_control["cwnd"]=cwnd+((cubic_rtt-cwnd)/cwnd)
                        if(congestion_control["cwnd"]<congestion_control["ssthres"]):
                            mode=Mode.slow_start
                            congestion_control["timeout"]=False
                    elif(mode==Mode.fast_recovery):
                        congestion_control['cwnd']=congestion_control['ssthres']
                        mode=Mode.congestion_avoidance
                        congestion_control["time"]=time.time()
                    else:
                        raise AttributeError

                else:
                    # Duplicate ACK received
                    
                    print(f"Received duplicate ACK for packet {ack_seq_num}, count={duplicate_ack_count}")
                    if(mode==Mode.slow_start):
                        duplicate_ack_count+=1
                        if(duplicate_ack_count==DUP_ACK_THRESHOLD):
                            congestion_control["ssthres"]=congestion_control["cwnd"]/congestion_control['dec_factor']
                            congestion_control["cwnd"]=congestion_control["ssthres"]+DUP_ACK_THRESHOLD
                            mode=Mode.fast_recovery
                            fast_retransmit(server_socket, client_address, unacked_packets)
                    elif(mode==Mode.congestion_avoidance):
                        duplicate_ack_count+=1
                        congestion_control["W_max"]=congestion_control["cwnd"]
                        congestion_control["ssthres"]=congestion_control["cwnd"]*(congestion_control["beta_cubic"])
                        congestion_control["ssthres"]=max(congestion_control["ssthres"],2)
                        congestion_control["cwnd"]=congestion_control["cwnd"]*congestion_control["beta_cubic"]
                        if(duplicate_ack_count==DUP_ACK_THRESHOLD):
                            w_last_max=congestion_control["W_max"]
                            
                            
                            mode=Mode.fast_recovery
                            congestion_control["timeout"]=False
                            # if congestion_control["W_max"]<w_last_max:
                            #     w_last_max=congestion_control["W_max"]
                            #     congestion_control["W_max"]=congestion_control["W_max"]*(1.0+congestion_control["beta_cubic"])/2.0
                            # else:
                            #     w_last_max=congestion_control["W_max"]
                            fast_retransmit(server_socket, client_address, unacked_packets)
                    elif(mode==Mode.fast_recovery):
                        congestion_control["cwnd"]=congestion_control["cwnd"]+1
                    else:
                        raise AttributeError
                    

            except socket.timeout:
                # Timeout handling: retransmit all unacknowledged packets
                
                print("Timeout occurred, retransmitting unacknowledged packets")
                fast_retransmit(server_socket, client_address, unacked_packets)
                if (mode==Mode.congestion_avoidance):
                    congestion_control["ssthres"]=congestion_control["cwnd"]*(congestion_control["beta_cubic"])
                    congestion_control["ssthres"]=max(congestion_control["ssthres"],2)
                    congestion_control["cwnd"]=1
                else:
                    congestion_control["ssthres"]=congestion_control["cwnd"]/congestion_control['dec_factor']
                    congestion_control["cwnd"]=1

                duplicate_ack_count=0
                mode=Mode.slow_start
                timeout=min(timeout*2,10)
                congestion_control["timeout"]=True
                print(f'New timeout : {timeout}')
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
    packet=json.loads(packets[0])
    return packet['seq_num']
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
    

def fast_retransmit(server_socket, client_address, unacked_packets):
    """
    Retransmit the earliest unacknowledged packet (fast recovery).
    """
    for packet in unacked_packets:
        unacked_packets[packet][2]=True
    min_seq_num=min(unacked_packets)
    packet,_,_=unacked_packets[min_seq_num]

    server_socket.sendto(packet, client_address)

    

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Reliable file transfer server over UDP.')
parser.add_argument('server_ip', help='IP address of the server')
parser.add_argument('server_port', type=int, help='Port number of the server')

args = parser.parse_args()

# Run the server
send_file(args.server_ip, args.server_port)