# Source-to-parcel analysis

# Import necessary libraries
from matplotlib.animation import FuncAnimation
import seaborn as sns  # required for heatmap visualization
import networkx as nx
from scipy.stats import pearsonr
from mne.viz import circular_layout
from mne_connectivity.viz import plot_connectivity_circle
import matplotlib.pyplot as plt
import os
import glob
import numpy as np
import pandas as pd
import mne
from mne.datasets import fetch_fsaverage
from nilearn import datasets
from nilearn.image import get_data
from scipy.signal import hilbert
import matplotlib
matplotlib.use('Qt5Agg')  # Setting the backend BEFORE importing pyplot

# Set your output directory
output_dir = r'../data/out/'  # Replace with your desired output directory
subj = '101'  # Replace with your subject ID

# Fetch the Schaefer atlas with 100 parcels
schaefer_atlas = datasets.fetch_atlas_schaefer_2018(n_rois=100)

# Load the source space for both hemispheres
fs_dir = '../data/in/fsaverage'
fname = os.path.join(fs_dir, "bem", "fsaverage-ico-5-src.fif")
src = mne.read_source_spaces(fname, patch_stats=False, verbose=None)

# Load inverse solution file paths for both left and right hemispheres
inverse_solution_files_lh = []
inverse_solution_files_rh = []
for i in range(1,58):
    filename_lh = output_dir + f"{subj}_inversesolution_epoch"+ str(i)+".fif-lh.stc"
    filename_rh = output_dir + f"{subj}_inversesolution_epoch"+ str(i)+".fif-rh.stc"
    inverse_solution_files_lh.append(filename_lh)
    inverse_solution_files_rh.append(filename_rh)

#Error here !!!

# Calculate the total number of inverse solution files for both hemispheres
total_files_lh = len(inverse_solution_files_lh)
total_files_rh = len(inverse_solution_files_rh)

# Calculate the batch size for both hemispheres
# Change 10 to your desired batch size
batch_size_lh = total_files_lh // (total_files_lh // 10)

# Change 10 to your desired batch size
batch_size_rh = total_files_rh // (total_files_rh // 10)

# Ensure batch size is a multiple of 10 (or your desired batch size) for both hemispheres
while total_files_lh % batch_size_lh != 0:
    batch_size_lh -= 1

while total_files_rh % batch_size_rh != 0:
    batch_size_rh -= 1

# Initialize lists to store source estimates for both hemispheres
stcs_lh = []
stcs_rh = []

# Load data in batches for both hemispheres
for i in range(0, total_files_lh, batch_size_lh):
    batch_files_lh = inverse_solution_files_lh[i:i + batch_size_lh]
    batch_files_rh = inverse_solution_files_rh[i:i + batch_size_rh]

    for file_path_lh, file_path_rh in zip(batch_files_lh, batch_files_rh):
        try:
            print(file_path_lh, file_path_rh)
            stc_epoch_lh = mne.read_source_estimate(file_path_lh)
            stc_epoch_rh = mne.read_source_estimate(file_path_rh)
            stcs_lh.append(stc_epoch_lh)
            stcs_rh.append(stc_epoch_rh)
        except Exception as e:
            print(f"Error loading files {file_path_lh} or {file_path_rh}: {e}")

# Load labels from the atlas
labels = mne.read_labels_from_annot('fsaverage', parc='Schaefer2018_100Parcels_7Networks_order',
                                    subjects_dir=r'../data/in/')

# Extract label time courses for both hemispheres
label_time_courses = []  # Initialize a list to store label time courses
input('pause')
print(stcs_lh, stcs_rh)
for idx, (stc_lh, stc_rh) in enumerate(zip(stcs_lh, stcs_rh)):
    try:
        label_tc_lh = stc_lh.extract_label_time_course(
            labels, src=src, mode='mean_flip')
        label_tc_rh = stc_rh.extract_label_time_course(
            labels, src=src, mode='mean_flip')
        label_time_courses.extend([label_tc_lh, label_tc_rh])
        print(src)
    except Exception as e:
        print(f"Error extracting label time courses for iteration {idx}: {e}")
else:  # This block will execute if the for loop completes without encountering a break statement
    print("All time courses have been successfully extracted!")

# Convert label_time_courses to a NumPy array
label_time_courses_np = np.array(label_time_courses)

# If you prefer to save as a .csv file
# Convert to DataFrame and save as .csv
# label_time_courses_df = pd.DataFrame(label_time_courses_np)
# label_time_courses_df.to_csv(os.path.join(output_dir, f"{subj}_label_time_courses.csv"), index=False)

# Save the label time courses as a .npy file
# Replace with your desired output directory
output_dir = r'../data/out'
label_time_courses_file = output_dir + f"{subj}_label_time_courses.npy"
print(label_time_courses)
np.save(label_time_courses_file, label_time_courses_np)

########################################################################################################################

# Plotting Time Courses
random_idx = np.random.randint(len(label_time_courses))
random_time_course = label_time_courses[random_idx]

plt.figure(figsize=(10, 6))
plt.plot(random_time_course)
plt.title(f'Time Course for Randomly Selected Region: {random_idx}')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.show()

# Connectivity Visualization for left hemisphere
num_regions = len(label_time_courses[0])
connectivity_matrix = np.zeros((num_regions, num_regions))

for i in range(num_regions):
    for j in range(num_regions):
        connectivity_matrix[i, j], _ = pearsonr(
            label_time_courses[0][i], label_time_courses[0][j])

plt.figure(figsize=(10, 10))
plt.imshow(connectivity_matrix, cmap='viridis', origin='lower')
plt.title('Connectivity Matrix')
plt.xlabel('Region')
plt.ylabel('Region')
plt.colorbar(label='Pearson Correlation')
plt.show()

# Average connectivity matrix across all epochs and hemispheres
# Initialize connectivity matrix
num_epochs_hemispheres = len(label_time_courses)
num_regions = label_time_courses[0].shape[0]
all_connectivity_matrices = np.zeros(
    (num_epochs_hemispheres, num_regions, num_regions))

# Compute connectivity for each epoch and hemisphere
for k in range(num_epochs_hemispheres):
    for i in range(num_regions):
        for j in range(num_regions):
            all_connectivity_matrices[k, i, j], _ = pearsonr(
                label_time_courses[k][i], label_time_courses[k][j])

# Average across all epochs and hemispheres
avg_connectivity_matrix = np.mean(all_connectivity_matrices, axis=0)

# Visualization
plt.figure(figsize=(10, 10))
plt.imshow(avg_connectivity_matrix, cmap='viridis', origin='lower')
plt.title('Average Connectivity Matrix')
plt.xlabel('Region')
plt.ylabel('Region')
plt.colorbar(label='Pearson Correlation')
plt.show()

########################################################################################################################
# All-to-all connectivity analysis

# Set your output directory
# Replace with your desired output directory
output_dir = r'../data/out'
subj = '101'  # Replace with your subject ID

# Load the label time courses
label_time_courses_file = os.path.join(
    output_dir, f"{subj}_label_time_courses.npy")

label_time_courses = np.load(label_time_courses_file)

# Load labels from the atlas
labels = mne.read_labels_from_annot('fsaverage', parc='Schaefer2018_100Parcels_7Networks_order',
                                    subjects_dir=r'../data/in/')

# Group labels by network
networks = {}
for label in labels:
    # Extract network name from label name (assuming format: 'NetworkName_RegionName')
    network_name = label.name.split('_')[0]
    if network_name not in networks:
        networks[network_name] = []
    networks[network_name].append(label)

# Organize regions by their network affiliations and extract the desired naming convention
ordered_regions = []
network_labels = []  # This will store the network each region belongs to

for label in labels:
    # Extract the desired naming convention "PFCl_1-lh" from the full label name
    parts = label.name.split('_')
    region_name = '_'.join(parts[2:])
    ordered_regions.append(region_name)

    # Extract the network name and store it in network_labels
    network_name = parts[2]
    network_labels.append(network_name)

# Compute cross-correlation between all pairs of regions across windows


def compute_cross_correlation(data_window):
    """Compute cross-correlation for given data window."""
    # Reshape the data to be 2D
    data_2D = data_window.reshape(data_window.shape[0], -1)
    correlation_matrix = np.corrcoef(data_2D, rowvar=True)
    return correlation_matrix

# Compute dPLI at the level of regions


def compute_dPLI(data):
    n_regions = data.shape[1]  # Compute for regions
    dPLI_matrix = np.zeros((n_regions, n_regions))
    analytic_signal = hilbert(data)
    phase_data = np.angle(analytic_signal)
    for i in range(n_regions):
        for j in range(n_regions):
            if i != j:
                phase_diff = phase_data[:, i] - phase_data[:, j]
                dPLI_matrix[i, j] = np.abs(
                    np.mean(np.exp(complex(0, 1) * phase_diff)))
    return dPLI_matrix

# dPLI_matrix = compute_dPLI(label_time_courses) --> computing static, fc for the entire dataset


def disparity_filter(G, alpha=0.01):
    disparities = {}
    for i, j, data in G.edges(data=True):
        weight_sum_square = sum(
            [d['weight']**2 for _, _, d in G.edges(i, data=True)])
        disparities[(i, j)] = data['weight']**2 / weight_sum_square

    G_filtered = G.copy()
    for (i, j), disparity in disparities.items():
        if disparity < alpha:
            G_filtered.remove_edge(i, j)
    return G_filtered


# Time-resolved dPLI computation
sampling_rate = 512  # in Hz
window_length_seconds = 1
step_size_seconds = 0.5

# Total duration in samples
# Assuming the structure is the same as label_time_courses in Code 2
num_epochs_per_hemisphere = label_time_courses.shape[0] / 2
duration_per_epoch = label_time_courses.shape[2] / sampling_rate
total_duration_samples = int(
    num_epochs_per_hemisphere * duration_per_epoch * sampling_rate)

window_length_samples = int(window_length_seconds * sampling_rate)
step_size_samples = int(step_size_seconds * sampling_rate)

num_windows = int(
    (total_duration_samples - window_length_samples) / step_size_samples) + 1
windowed_dpli_matrices = []
windowed_cross_correlation_matrices = []

for win_idx in range(num_windows):
    start_sample = win_idx * step_size_samples
    end_sample = start_sample + window_length_samples

    # Check if end_sample exceeds the total number of samples
    if end_sample > total_duration_samples:
        break

    # Calculate epoch and sample indices
    start_epoch = start_sample // label_time_courses.shape[2]
    start_sample_in_epoch = start_sample % label_time_courses.shape[2]
    end_epoch = end_sample // label_time_courses.shape[2]
    end_sample_in_epoch = end_sample % label_time_courses.shape[2]

    # Extract data across epochs
    if start_epoch == end_epoch:
        windowed_data = label_time_courses[start_epoch,
                                           :, start_sample_in_epoch:end_sample_in_epoch]
    else:
        first_part = label_time_courses[start_epoch, :, start_sample_in_epoch:]
        samples_needed_from_second_epoch = window_length_samples - \
            first_part.shape[1]
        second_part = label_time_courses[end_epoch,
                                         :, :samples_needed_from_second_epoch]
        windowed_data = np.concatenate((first_part, second_part), axis=1)

    # dPLI computation
    dpli_result = compute_dPLI(windowed_data)
    windowed_dpli_matrices.append(dpli_result)

    # Cross-correlation computation
    cross_corr_result = compute_cross_correlation(windowed_data)
    windowed_cross_correlation_matrices.append(cross_corr_result)

# Check the number of windows in the list
num_of_windows = len(windowed_dpli_matrices)
print(f"Total number of windows: {num_of_windows}")

# For visualization, select one of the windows
chosen_window = 3
dPLI_matrix = windowed_dpli_matrices[chosen_window]
CrossCorr_matrix = windowed_cross_correlation_matrices[chosen_window]

G_dPLI = nx.convert_matrix.from_numpy_array(dPLI_matrix)
G_dPLI_thresholded = disparity_filter(G_dPLI)

G_CrossCorr = nx.convert_matrix.from_numpy_array(CrossCorr_matrix)
G_CrossCorr_thresholded = disparity_filter(G_CrossCorr)

# Visualization using dPLI
node_angles = np.linspace(0, 360, len(ordered_regions), endpoint=False)
# Initialize a matrix of zeros with the same shape as dPLI_matrix
dPLI_matrix_thresholded = np.zeros_like(dPLI_matrix)
# Iterate through the edges of the thresholded graph
for i, j, data in G_dPLI_thresholded.edges(data=True):
    dPLI_matrix_thresholded[i, j] = data['weight']
    dPLI_matrix_thresholded[j, i] = data['weight']

fig, ax = plt.subplots(figsize=(8, 8), facecolor='black',
                       subplot_kw=dict(polar=True))
plot_connectivity_circle(dPLI_matrix_thresholded, ordered_regions, n_lines=300, node_angles=node_angles,
                         title='Thresholded Regional Connectivity using dPLI', ax=ax)
fig.tight_layout()
plt.show()

# Visualization using Cross-Correlation for a chosen window

# Convert the graph to a matrix function


def graph_to_matrix(graph, size):
    matrix = np.zeros((size, size))
    for i, j, data in graph.edges(data=True):
        matrix[i, j] = data['weight']
        matrix[j, i] = data['weight']  # Ensure symmetry
    return matrix


# Using the above function, convert thresholded graph to matrix
CrossCorr_thresholded_matrix = graph_to_matrix(
    G_CrossCorr_thresholded, CrossCorr_matrix.shape[0])

# Visualization


def plot_matrix(matrix, title, labels, cmap='viridis'):
    plt.figure(figsize=(10, 10))
    sns.heatmap(matrix, cmap=cmap, xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.show()


# Using the provided plot_matrix function
plot_matrix(CrossCorr_thresholded_matrix,
            f'Thresholded Cross-Correlation Matrix for Window {chosen_window}', ordered_regions)

# Dynamic representation (animation) across all windows for heatmat

fig, ax = plt.subplots(figsize=(10, 10))
sns.heatmap(graph_to_matrix(G_CrossCorr_thresholded,
            CrossCorr_matrix.shape[0]), cmap='viridis', xticklabels=ordered_regions, yticklabels=ordered_regions, ax=ax)
title = ax.set_title(f'Thresholded Cross-Correlation Matrix for Window 0')


def update(window_number):
    ax.clear()
    current_matrix = graph_to_matrix(nx.convert_matrix.from_numpy_array(
        windowed_cross_correlation_matrices[window_number]), windowed_cross_correlation_matrices[window_number].shape[0])
    sns.heatmap(current_matrix, cmap='viridis',
                xticklabels=ordered_regions, yticklabels=ordered_regions, ax=ax)
    title.set_text(
        f'Thresholded Cross-Correlation Matrix for Window {window_number}')
    return ax,


ani = FuncAnimation(fig, update, frames=num_of_windows, blit=True)
plt.show()

# Dynamics representation (animation) across all windows from circular graph

node_angles = np.linspace(0, 360, len(ordered_regions), endpoint=False)


def threshold_matrix(matrix):
    G_temp = nx.convert_matrix.from_numpy_array(matrix)
    G_temp_thresholded = disparity_filter(G_temp)

    matrix_thresholded = np.zeros_like(matrix)
    for i, j, data in G_temp_thresholded.edges(data=True):
        matrix_thresholded[i, j] = data['weight']
        matrix_thresholded[j, i] = data['weight']
    return matrix_thresholded


fig, ax = plt.subplots(figsize=(8, 8), facecolor='black',
                       subplot_kw=dict(polar=True))
plot_connectivity_circle(threshold_matrix(windowed_dpli_matrices[0]), ordered_regions, n_lines=300,
                         node_angles=node_angles,
                         title='Thresholded Regional Connectivity using dPLI for Window 0', ax=ax)


def update(window_number):
    ax.clear()
    current_matrix = threshold_matrix(windowed_dpli_matrices[window_number])
    plot_connectivity_circle(current_matrix, ordered_regions, n_lines=300, node_angles=node_angles,
                             title=f'Thresholded Regional Connectivity using dPLI for Window {window_number}', ax=ax)
    return ax,


ani = FuncAnimation(fig, update, frames=num_of_windows, blit=True)
plt.show()


# Histogram of Connectivity Values for the chosen window using dPLI
plt.hist(dPLI_matrix.flatten(), bins=50, color='blue', alpha=0.7)
plt.title('Distribution of dPLI Connectivity Values')
plt.xlabel('Connectivity Value')
plt.ylabel('Frequency')
plt.show()

# Histogram of Connectivity Values for the chosen window using Cross-Correlation
plt.hist(CrossCorr_matrix.flatten(), bins=50, color='red', alpha=0.7)
plt.title('Distribution of Cross-Correlation Connectivity Values')
plt.xlabel('Connectivity Value')
plt.ylabel('Frequency')
plt.show()
########################################################################################################################

# Next --> fc between groups and minimum spanning tree to examine nature of the fc difference between groups
