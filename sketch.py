import matplotlib

# Set a non-interactive backend to prevent IDE-specific display errors
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset
import numpy as np
import math

# --- 1. Define Geometry and Variation Parameters ---
# Parameters from the cadquery script and PDF drawing for a complete picture
total_height = 95.0
bottom_dia_outer = 25.8
top_dia_outer = 30.0
chamfer_start_height = 70.0
chamfer_angle_deg = 15.0  # This is the outer chamfer alpha

# Variations as described in the paper
angle_variation_deg = 0.25
indentation_mm = 1.0


# --- 2. Function to draw the static outer body ---
def plot_outer_body(ax):
    """Calculates and draws the outer profile of the part on a given axes."""
    r_bottom = bottom_dia_outer / 2.0
    r_top = top_dia_outer / 2.0
    radius_change = r_top - r_bottom
    chamfer_height = radius_change / math.tan(math.radians(chamfer_angle_deg))
    chamfer_end_height = chamfer_start_height + chamfer_height

    # Right side
    x_coords_right = [r_bottom, r_bottom, r_top, r_top]
    y_coords_right = [0, chamfer_start_height, chamfer_end_height, total_height]
    # Left side
    x_coords_left = [-x for x in x_coords_right]

    # Changed color to 'black' for better visibility
    ax.plot(x_coords_right, y_coords_right, color='black', linestyle='solid', linewidth=1.5)
    ax.plot(x_coords_left, y_coords_right, color='black', linestyle='solid', linewidth=1.5)


# --- 3. Function to draw the inner profile based on the new geometry ---
def plot_inner_profile(ax, indentation, angle_deg, color, linestyle, label, linewidth=2):
    """
    Calculates and draws the inner profile on a given axes.
    Slants the entire inner cylinder as a single rigid body.
    """
    # --- Define base geometry parameters ---
    h_total_inner = 72.0
    dia_B = 23.2
    dia_C_new = 10.0
    chamfer_angle_from_horizontal = 7.0
    inner_fillet_radius = 1.0

    # --- Radii are constant ---
    r_B = dia_B / 2.0
    r_C = dia_C_new / 2.0

    # --- Calculate profile dimensions ---
    delta_r_total = r_B - r_C
    h_chamfer_total = delta_r_total * math.tan(math.radians(chamfer_angle_from_horizontal))
    h_straight_total = h_total_inner - h_chamfer_total

    if h_straight_total < 0:
        print(f"Warning: Invalid base geometry. Skipping plot.")
        return

    # --- Calculate fillet geometry for the right side ---
    R = inner_fillet_radius
    angle_rad = math.radians(chamfer_angle_from_horizontal)
    z_sharp_corner = -h_straight_total
    z_center_offset = R * ((1 - math.sin(angle_rad)) / math.cos(angle_rad))
    x_center = r_B - R
    z_center = z_sharp_corner + z_center_offset
    start_angle_rad = 0
    end_angle_rad = -math.radians(90 - chamfer_angle_from_horizontal)
    arc_angles = np.linspace(start_angle_rad, end_angle_rad, 20)
    arc_x = x_center + R * np.cos(arc_angles)
    arc_z = z_center + R * np.sin(arc_angles)

    # --- Generate profile points for the right side ---
    z_top = 0
    z_bottom = -h_total_inner
    x_points_right = [r_B, arc_x[0]]
    z_points_right = [z_top, arc_z[0]]
    x_points_right.extend(arc_x[1:])
    z_points_right.extend(arc_z[1:])
    x_points_right.append(r_C)
    z_points_right.append(z_bottom)
    x_points_right.append(0)
    z_points_right.append(z_bottom)

    profile_x_right_raw = np.array(x_points_right)
    profile_z_right_raw = np.array(z_points_right)

    # --- Create the left side profile by mirroring the right side ---
    profile_x_left_raw = -profile_x_right_raw

    # --- Function to apply rotation and final positioning ---
    def transform_profile(x_in, z_in, angle_deg, vertical_shift):
        angle_rad = math.radians(angle_deg)
        pivot_z_abs = total_height

        # Rotate the entire profile as a single body
        x_rot = x_in * math.cos(angle_rad) - z_in * math.sin(angle_rad)
        z_rot = x_in * math.sin(angle_rad) + z_in * math.cos(angle_rad)

        # Translate to final position and apply indentation
        x_final = x_rot
        z_final = z_rot + pivot_z_abs - vertical_shift

        return x_final, z_final

    # --- Transform and plot the left and right profiles separately ---
    x_right_transformed, z_right_transformed = transform_profile(profile_x_right_raw, profile_z_right_raw, angle_deg,
                                                                 indentation)
    x_left_transformed, z_left_transformed = transform_profile(profile_x_left_raw, profile_z_right_raw, angle_deg,
                                                               indentation)

    ax.plot(x_right_transformed, z_right_transformed, color=color, linestyle=linestyle, label=label,
            linewidth=linewidth)
    ax.plot(x_left_transformed, z_left_transformed, color=color, linestyle=linestyle, linewidth=linewidth)


# --- 4. Create the Plot ---
fig, ax = plt.subplots(figsize=(10, 12))  # Increased figure width for inset
plt.subplots_adjust(right=0.7)  # Make space on the right for the inset

# --- Plot all geometries on the main axes ---
plot_outer_body(ax)
ax.axvline(0, color='grey', linestyle=':', label='Centerline')

# 1. Base Geometry (Symmetric)
plot_inner_profile(ax, 0, 0, 'black', 'solid', 'Original Geometry', linewidth=2.5)
# 2. Angle of Attack Variation
plot_inner_profile(ax, 0, angle_variation_deg, 'red', 'dashed', f'+{angle_variation_deg}° Angle of Attack')
# 3. Additional Indentation Variation
plot_inner_profile(ax, indentation_mm, 0, 'blue', 'dashed', f'{indentation_mm}mm Additional Indentation')
# 4. Combined Variation
plot_inner_profile(ax, indentation_mm, angle_variation_deg, 'green', 'dashed', 'Combined Variation')

# --- 5. Create and populate the zoomed-in inset ---
# Position the inset outside the main plot area on the right
axins = zoomed_inset_axes(ax, zoom=6, loc='upper left', bbox_to_anchor=(1.05, 1.0), bbox_transform=ax.transAxes)

# Plot all geometries again on the inset axes
plot_outer_body(axins)
plot_inner_profile(axins, 0, 0, 'black', 'solid', None, linewidth=2.5)
plot_inner_profile(axins, 0, angle_variation_deg, 'red', 'dashed', None)
plot_inner_profile(axins, indentation_mm, 0, 'blue', 'dashed', None)
plot_inner_profile(axins, indentation_mm, angle_variation_deg, 'green', 'dashed', None)

# Set the zoom area - expanded for more context and to include outer wall
x1, x2, y1, y2 = 9.5, 13.5, 22.0, 26.0
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)
axins.grid(True, linestyle='--', alpha=0.6)

# Hide the tick labels of the inset
axins.set_xticklabels('')
axins.set_yticklabels('')

# Draw lines connecting the inset to the main plot
mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")

# --- 6. Final Formatting ---
ax.set_aspect('equal', adjustable='box')
# ax.set_title('Schematic of Geometric Variations')
ax.set_xlabel('Position (mm)')
ax.set_ylabel('Height (mm)')
ax.legend()
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlim(-16, 16)
ax.set_ylim(bottom=0, top=96)

# Use bbox_inches='tight' to minimize whitespace
plt.savefig('geometry_variation_sketch_full.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
