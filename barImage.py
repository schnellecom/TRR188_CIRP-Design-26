import matplotlib.pyplot as plt
import numpy as np

# --- Data ---
S = np.array([0.798, 0.023])   # First-order indices
ST = np.array([0.978, 0.204])  # Total-order indices
labels = ['Angle', 'Indent']

# --- Plotting Setup ---
x = np.arange(len(labels))
width = 0.35
# Professional color scheme
colors = {'first_order': '#56B4E9', 'total_order': '#0072B2'}

# --- Create the Figure ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# --- Plot Bars ---
rects1 = ax.bar(x - width/2, S, width, label='First-order ($S_i$)',
                color=colors['first_order'])
rects2 = ax.bar(x + width/2, ST, width, label='Total-order ($S_{Ti}$)',
                color=colors['total_order'])

# --- Add Labels and Titles ---
ax.set_ylabel('Sobol Index', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylim([0, 1.1])

# --- Add Direct Bar Labels ---
ax.bar_label(rects1, padding=3, fmt='%.3f')
ax.bar_label(rects2, padding=3, fmt='%.3f')

# --- Professional Polish ---
ax.legend(fontsize=10)
ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# This is the sensible option to ensure everything fits!
plt.tight_layout()

# --- Save in High-Quality Formats ---
# plt.savefig('sobol_indices.pdf')
plt.savefig('sobol_indices.png')