import pandas as pd
import matplotlib.pyplot as plt

# Assuming you've read the data into a DataFrame `df`
df = pd.read_csv('p2_fairness.csv')

# Group by 'DELAY' and calculate the average 'jfi'
df_avg = df.groupby('delay')['jfi'].mean()

# Plotting the average JFI against the delay
plt.figure(figsize=(10, 6))
plt.plot(df_avg.index, df_avg.values, label='Jain\'s Fairness Index', color='g', marker='o')

# Adding labels and title
plt.xlabel('Delay (in ms)')
plt.ylabel('Jain\'s Fairness Index')
plt.title('TCP Reno Fairness')
plt.legend()
plt.grid(True)
plt.savefig('p2_fairness.png')

# Load the data from a CSV file
data = pd.read_csv('throughput_loss.csv')

# Group by loss to calculate the average throughput for each loss value
avg_throughput = data.groupby('loss')['throughput'].mean()/1000

# Plot the data
plt.figure(figsize=(10, 6))

# Add a label to the plot
plt.plot(avg_throughput.index, avg_throughput.values, color='g', marker='o', label='Average Throughput')

# Customize the plot
plt.title('TCP Reno Throughput')
plt.xlabel('Loss (%)')
plt.ylabel('Throughput (in kBps)')
plt.legend()  # Now this will work since there is a labeled artist
plt.grid(True)

# Save the plot
plt.savefig("congcont_loss.png")

# Load the data from a CSV file
data = pd.read_csv('throughput_delay.csv')

# Group by loss to calculate the average throughput for each loss value
avg_throughput = data.groupby('delay')['throughput'].mean()/1000

# Plot the data
plt.figure(figsize=(10, 6))

# Add a label to the plot
plt.plot(avg_throughput.index, avg_throughput.values, color='g', marker='o', label='Average Throughput')

# Customize the plot
plt.title('TCP Reno Throughput')
plt.xlabel('Delay (in ms)')
plt.ylabel('Throughput (in kBps)')
plt.legend()  # Now this will work since there is a labeled artist
plt.grid(True)

# Save the plot
plt.savefig("congcont_delay.png")