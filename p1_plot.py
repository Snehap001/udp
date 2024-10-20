import pandas as pd
import matplotlib.pyplot as plt

# Load the data from a CSV file
data = pd.read_csv('reliability_loss.csv')

# Convert the 'fast_recovery' column to a categorical type for easy filtering
data['fast_recovery'] = data['fast_recovery'].astype(int)

# Filter data for fast recovery (1) and without fast recovery (0)
data_fast_recovery = data[data['fast_recovery'] == 1]
data_no_fast_recovery = data[data['fast_recovery'] == 0]

# Group by loss to calculate the average transmission time for each loss value
avg_ttc_fast_recovery = data_fast_recovery.groupby('loss')['ttc'].mean()
avg_ttc_no_fast_recovery = data_no_fast_recovery.groupby('loss')['ttc'].mean()

# Plot the data
plt.figure(figsize=(10, 6))

plt.plot(avg_ttc_fast_recovery.index, avg_ttc_fast_recovery.values, label='With Fast Recovery', marker='o')
plt.plot(avg_ttc_no_fast_recovery.index, avg_ttc_no_fast_recovery.values, label='Without Fast Recovery', marker='x')

# Customize the plot
plt.title('File Transmission Time vs Loss (With and Without Fast Recovery)')
plt.xlabel('Loss (%)')
plt.ylabel('Average Transmission Time (TTC)')
plt.legend()
plt.grid(True)

# Show the plot
plt.savefig("reliability_loss.png")




# Load the data from a CSV file
data = pd.read_csv('reliability_delay.csv')

# Convert the 'fast_recovery' column to a categorical type for easy filtering
data['fast_recovery'] = data['fast_recovery'].astype(int)

# Filter data for fast recovery (1) and without fast recovery (0)
data_fast_recovery = data[data['fast_recovery'] == 1]
data_no_fast_recovery = data[data['fast_recovery'] == 0]

# Group by loss to calculate the average transmission time for each loss value
avg_ttc_fast_recovery = data_fast_recovery.groupby('delay')['ttc'].mean()
avg_ttc_no_fast_recovery = data_no_fast_recovery.groupby('delay')['ttc'].mean()

# Plot the data
plt.figure(figsize=(10, 6))

plt.plot(avg_ttc_fast_recovery.index, avg_ttc_fast_recovery.values, label='With Fast Recovery', marker='o')
plt.plot(avg_ttc_no_fast_recovery.index, avg_ttc_no_fast_recovery.values, label='Without Fast Recovery', marker='x')

# Customize the plot
plt.title('File Transmission Time vs Loss (With and Without Fast Recovery)')
plt.xlabel('delay (%)')
plt.ylabel('Average Transmission Time (TTC)')
plt.legend()
plt.grid(True)

# Show the plot

plt.savefig("reliability_delay.png")
