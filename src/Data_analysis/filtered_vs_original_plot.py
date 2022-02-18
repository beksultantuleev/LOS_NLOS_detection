from turtle import color
import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv('comparison_data_100.csv', names=['x1', 'y1', 'x2', 'y2'])
# print(data)

plt.plot(data['x2'], data['y2'], color = 'r', label='original', linestyle="--", alpha=0.5)
plt.plot(data['x1'], data['y1'], color = 'g', label='filtered', linestyle="-", alpha=0.5)
plt.xlabel("X")
plt.ylabel("Y")
plt.legend()
plt.tight_layout()
plt.show()