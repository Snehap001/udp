import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np

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

# # Load the data from a CSV file
# data = pd.read_csv('throughput_loss.csv')

# # Group by loss to calculate the average throughput for each loss value
# avg_throughput = data.groupby('loss')['throughput'].mean() / 1000000

# avg_throughput = avg_throughput[avg_throughput.index != 0]

# # Calculate the square root of loss values
# sqrt_loss = np.sqrt(avg_throughput.index)

# # Define the hyperbolic function for fitting
# def hyperbola(x, a, b):
#     return a / (x + b)

# # Perform curve fitting
# popt, _ = curve_fit(hyperbola, sqrt_loss, avg_throughput.values)

# # Plot the data
# plt.figure(figsize=(10, 6))

# # Plot actual average throughput against square root of loss
# plt.plot(sqrt_loss, avg_throughput.values, color='g', marker='o', label='Average Throughput')

# # Plot the hyperbolic fit
# x_vals = np.linspace(min(sqrt_loss), max(sqrt_loss), 100)
# y_vals = hyperbola(x_vals, *popt)
# plt.plot(x_vals, y_vals, color='b', linestyle='--', label=f'Hyperbolic Fit: $y={popt[0]:.2f}/(x + {popt[1]:.2f})$')

# # Customize the plot
# plt.title('TCP Reno Throughput ')
# plt.xlabel('Square Root of Loss (%)')
# plt.ylabel('Throughput (in MBps)')
# plt.legend()  # Now this will work since there is a labeled artist
# plt.grid(True)

# # Save the plot
# plt.savefig("congcont_loss.png")

# # Load the data from a CSV file
# data = pd.read_csv('throughput_delay.csv')

# # Group by delay to calculate the average throughput for each delay value
# avg_throughput = data.groupby('delay')['throughput'].mean() / 1000000

# # Filter out the point where delay is 0
# avg_throughput = avg_throughput[avg_throughput.index != 0]

# # Define the hyperbolic function
# def hyperbola(x, a, b):
#     return a / (x + b)

# # Perform curve fitting
# popt, _ = curve_fit(hyperbola, avg_throughput.index, avg_throughput.values)

# # Plot the data
# plt.figure(figsize=(10, 6))
# plt.plot(avg_throughput.index, avg_throughput.values, color='g', marker='o', label='Average Throughput')

# # Plot the hyperbolic fit
# x_vals = np.linspace(min(avg_throughput.index), max(avg_throughput.index), 100)
# y_vals = hyperbola(x_vals, *popt)
# plt.plot(x_vals, y_vals, color='b', linestyle='--', label=f'Hyperbolic Fit: $a/(delay + b)$\n a={popt[0]:.2f}, b={popt[1]:.2f}')

# # Customize the plot
# plt.title('TCP Reno Throughput')
# plt.xlabel('Delay (in ms)')
# plt.ylabel('Throughput (in MBps)')
# plt.legend()
# plt.grid(True)

# # Save the plot
# plt.savefig("congcont_delay.png")
