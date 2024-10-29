import matplotlib.pyplot as plt
import pandas as pd
import argparse

# Function to parse log file and return DataFrame with timestamps and data length
def parse_log(file):
    timestamps = []
    lengths = []
    
    with open(file, 'r') as f:
        for line in f:
            parts = line.strip().split(":")
            lengths.append(int(parts[1]))       # len_data
            timestamps.append(float(parts[2]))  # timestamp
    
    # Convert to DataFrame
    df = pd.DataFrame({'timestamp': timestamps, 'length': lengths})
    
    return df

# Main function to process log files and plot throughput
def main(delay):
    # Construct the log filenames using the provided delay
    server1_log = f'server1_output_{delay}.log'
    client1_log = f'client1_output_{delay}.log'
    server2_log = f'server2_output_{delay}.log'
    client2_log = f'client2_output_{delay}.log'

    # Parse logs for each client-server pair
    server1_data = parse_log(server1_log)
    client1_data = parse_log(client1_log)
    server2_data = parse_log(server2_log)
    client2_data = parse_log(client2_log)

    # Combine client and server data for each pair
    combined1 = pd.concat([client1_data, server1_data]).sort_values('timestamp')
    combined2 = pd.concat([client2_data, server2_data]).sort_values('timestamp')

    # Calculate cumulative data for the merged DataFrames
    combined1['cumulative_length'] = combined1['length'].cumsum()
    combined2['cumulative_length'] = combined2['length'].cumsum()

    # Combine both datasets to calculate the global minimum timestamp
    combined = pd.concat([combined1, combined2])

    # Calculate the minimum timestamp from the combined data
    min_timestamp = combined['timestamp'].min()

    # Calculate relative time and throughput for each combined dataset
    combined1['relative_time'] = combined1['timestamp'] - min_timestamp  # Relative time from global minimum
    combined1['throughput'] = combined1['cumulative_length'] / (combined1['relative_time'].replace(0, 1))  # Avoid division by zero

    combined2['relative_time'] = combined2['timestamp'] - min_timestamp  # Relative time from global minimum
    combined2['throughput'] = combined2['cumulative_length'] / (combined2['relative_time'].replace(0, 1))  # Avoid division by zero

    # Plot the throughput for each client-server pair
    plt.figure(figsize=(12, 6))
    plt.plot(combined1['relative_time'], combined1['throughput'], label='TCP Reno', color='blue')
    plt.plot(combined2['relative_time'], combined2['throughput'], label='TCP Cubic', color='orange')

    # Customize the plot
    plt.title('CCA Short Delay Comparison')
    plt.xlabel('Time (s)')
    plt.ylabel('Throughput (Bytes/sec)')
    plt.legend()
    plt.grid(True)

    # Save the plot
    plt.savefig('p3_fairness.png')

# Entry point for the script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process log files and plot throughput.')
    parser.add_argument('delay', type=str, help='The delay parameter to be included in the log filenames.')
    args = parser.parse_args()
    
    main(args.delay)
