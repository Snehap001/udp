import pandas as pd
import matplotlib.pyplot as plt

# Load the data from CSV
data = pd.read_csv('throughput_delay_3.csv')

# Optionally, calculate the mean throughput for each unique delay value
data_grouped = data.groupby('delay')['throughput'].mean().reset_index()

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(data_grouped['delay'], data_grouped['throughput'], marker='o', linestyle='-')
plt.xlabel("Delay (ms)")
plt.ylabel("Throughput")
plt.title("Throughput vs. Delay")
plt.grid(True)
plt.savefig("throughput_delay_3.png")

data = pd.read_csv('throughput_loss_3.csv')

# Optionally, calculate the mean throughput for each unique loss value
data_grouped = data.groupby('loss')['throughput'].mean().reset_index()

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(data_grouped['loss'], data_grouped['throughput'], marker='o', linestyle='-')
plt.xlabel("loss (ms)")
plt.ylabel("Throughput")
plt.title("Throughput vs. loss")
plt.grid(True)
plt.savefig("throughput_loss_3.png")