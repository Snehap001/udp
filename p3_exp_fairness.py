from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
import time, re, os
import sys
import hashlib
import subprocess 

class DumbbellTopo(Topo):    
    def build(self, d='50ms'):
        # Create hosts
        c1 = self.addHost('c1')
        c2 = self.addHost('c2')
        s1 = self.addHost('s1')
        s2 = self.addHost('s2')

        # Create switches
        sw1 = self.addSwitch('sw1')
        sw2 = self.addSwitch('sw2')

        # Add links with specified parameters
        # Links between clients/servers and switches
        self.addLink(c1, sw1, delay=d)
        self.addLink(c2, sw1, delay=d)
        self.addLink(s1, sw2, delay=d)

        buffer_size = 500
        # Link between sw1 and sw2 (bottleneck link)
        self.addLink(sw1, sw2, bw=100, delay=d, max_queue_size=buffer_size)
        
        print("delay is ", d)
        # Link between sw2 and s2 with specified latency
        self.addLink(s2, sw2, delay=d)

def jain_fairness_index(allocations):
    n = len(allocations)
    sum_of_allocations = sum(allocations)
    sum_of_squares = sum(x ** 2 for x in allocations)
    
    jfi = (sum_of_allocations ** 2) / (n * sum_of_squares)
    return jfi

def compute_md5(file_path):
    """Compute the MD5 hash of a file."""
    hasher = hashlib.md5()
    try:

        with open(file_path, 'rb') as file:
            # Read the file in chunks to avoid using too much memory for large files
            while chunk := file.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

def run():
    # Set the log level to info to see detailed output
    setLogLevel('info')
    
    # IP and port of the remote controller
    controller_ip = '127.0.0.1'  # Change to the controller's IP address if not local
    controller_port = 6653       # Default OpenFlow controller port
    
    # Output file 
    output_file = f'p2_fairness.csv'
    f_out = open(output_file, 'w')
    f_out.write("delay,md5_hash_1,md5_hash_2,ttc1,ttc2,jfi\n")


    SERVER_IP1 = "10.0.0.3"
    SERVER_PORT1 = 6555
    SERVER_IP2 = "10.0.0.4"
    SERVER_PORT2 = 6556
            
    NUM_ITERATIONS = 5 
    OUTFILE = 'received_file.txt'
    delay_list = [2,25]
    
    # Loop to create the topology 10 times with varying loss (1% to 10%)
    for DELAY in delay_list:
        os.system("mn -c")
        print(f"\n--- Running topology with {DELAY}ms delay --")
        print(DELAY)
        # Create the custom topology with the specified loss
        topo = DumbbellTopo(d=f"{DELAY}ms")

        # Initialize the network with the custom topology and TCLink for link configuration
        net = Mininet(topo=topo, link=TCLink, controller=None)
        # Add the remote controller to the network
        remote_controller = RemoteController('c0', ip=controller_ip, port=controller_port)
        net.addController(remote_controller)

        # Start the network
        net.start()
        #CLI(net)
        # Get references to h1 and h2
        c1 = net.get('c1')
        c2 = net.get('c2')
        s1 = net.get('s1')
        s2 = net.get('s2')
        
        pref_c1 = "1"
        pref_c2 = "2"
        log_files = ["server1_output_2.log", "server2_output_2.log","server2_output_25.log","server1_output_25.log", "client1_output_2.log", "client2_output_2.log","client2_output_25.log","client1_output_25.log"]

        # Remove old log files if they exist
        for log_file in log_files:
            if os.path.exists(log_file):
                os.remove(log_file)
                print(f"Removed old log file: {log_file}")
            else:
                print(f"No old log file found for: {log_file}")
        
        s1_cmd = f"python3 p2_server.py {SERVER_IP1} {SERVER_PORT1} >> server1_output_{DELAY}.log 2>&1 &"
        s2_cmd = f"python3 p3_server.py {SERVER_IP2} {SERVER_PORT2} >> server2_output_{DELAY}.log 2>&1 &"
        c1_cmd = f"python3 p2_client.py {SERVER_IP1} {SERVER_PORT1} --pref_outfile {pref_c1} >> client1_output_{DELAY}.log 2>&1 &"
        c2_cmd = f"python3 p2_client.py {SERVER_IP2} {SERVER_PORT2} --pref_outfile {pref_c2} >> client2_output_{DELAY}.log 2>&1 &"

        s1_pid = s1.cmd(s1_cmd)
        s2_pid = s2.cmd(s2_cmd)
        time.sleep(1)
                    
        s1_pid = s1.cmd(s1_cmd)
        s2_pid = s2.cmd(s2_cmd)
        time.sleep(1)
        start_time_c1 = time.time()
        c1.cmd(c1_cmd)
        print(f"Client 1 command executed")
        c1_pid_raw = c1.cmd('ps').strip()
        print(f"Checking PID: {c1_pid_raw}")
        pid_parts = c1_pid_raw.split()
        c1_pid = pid_parts[-8]
        print(f"Started client 1 with PID: {c1_pid}")
        start_time_c2 = time.time()
        c2_pid=c2.cmd(c2_cmd)
        print(f"Client 2 command executed")
        c2_pid_raw = c2.cmd('ps').strip()
        print(f"Checking PID: {c2_pid_raw}")
        pid_parts = c2_pid_raw.split()  
        c2_pid = pid_parts[-8]
        print(f"Started client 2 with PID: {c2_pid}")

        #CLI(net)
        end_time_c1 = None
        end_time_c2 = None
        # Polling loop to check when each process completes
        while end_time_c1 is None or end_time_c2 is None:
            # Check if process for c1 has completed
            if end_time_c1 is None:
                result_c1 = c1.cmd(f'ps')
                if not result_c1 or str(c1_pid) not in result_c1:  # Process is no longer running
                    end_time_c1 = time.time()

            if end_time_c2 is None:
                result_c2 = c2.cmd(f'ps')
                if not result_c2 or str(c2_pid) not in result_c2:  # Process is no longer running
                    end_time_c2 = time.time()
        

        # Stop the network
        net.stop()
            
        # calculate metrics
        dur_c1 = end_time_c1 - start_time_c1
        dur_c2 = end_time_c2 - start_time_c2
        
        jfi = jain_fairness_index([1/dur_c1, 1/dur_c2])
        
        print(dur_c1, dur_c2, jfi) 
        # calculate md5 hash
        hash1 = compute_md5(f"{pref_c1}received_file.txt")
        hash2 = compute_md5(f"{pref_c2}received_file.txt")


        f_out.write(f"{DELAY},{hash1},{hash2},{dur_c1},{dur_c2},{jfi}\n")
        # Wait a moment before starting the next iteration
        os.system(f"lsof -t -iUDP:{SERVER_PORT1} | xargs -r kill -9")
        os.system(f"lsof -t -iUDP:{SERVER_PORT2} | xargs -r kill -9")
        time.sleep(1)
    f_out.close()
    print("\n--- Completed all tests ---")


if __name__ == "__main__":
    run()