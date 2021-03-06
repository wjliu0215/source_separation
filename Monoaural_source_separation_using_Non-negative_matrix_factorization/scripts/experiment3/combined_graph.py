"""Combines the plots of a large set of experiments

Reads in the data of the multiple experiments run. 
Averages the SNR for a given setting of alpha, beta, num_iter and window over the number of components obtaining one value per frame size
plots the average snr vs number frame size in seconds for different windows

"""


import argparse
import os
from os import listdir
from os.path import join
import pickle
import sys

import librosa
import librosa.display
from librosa.core import resample
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import scipy
from scipy.io.wavfile import write
from sklearn.decomposition import NMF

# relative imports as the directory structure is
# blah-blah/source_separation/examples,
# blah-blah/source_separation/nmf,
# TODO: (0) find a more scalable way for this
sys.path.insert(0,"../../../../source_separation/")
from sourcesep.sourcesep import *
from tools.basic_functions import *


def obtain_variables_from_pickle(path_pickle):
	"""read the stored variables from the pickle file

	Parameters:
		path_pickle (string): path to the pickle file
	Returns: 
		Y (list): list of plots for a given experiment
		labels (list ): labels for each graph
		R (list): range of epochs

		
	"""
	with open(path_pickle, "rb") as handle:
		results = pickle.load(handle)
	Y = results["Y"]
	labels = results["labels"]
	R = results["R"]
	print(type(R))
	if type(R) != np.ndarray:
		print("creating R due to original error")
		R = np.arange(R - len(Y[0]), R, 1)
	return Y, labels, R


def savefigure1(title, xlabel, ylabel, Y, labels, x, path_save_dir, type = "linear"):
    """
    Function to create and save plots

    Parameters:
        title (string): title of the plot
        xlabel (string): label of the x axis of the plot
        ylabel (string): label of the y axis of the plot
        Y (list): list of all the functions to be plotted on the Y axis
        labels (list): list of plot names for the legend
        x (array): array of the x axis values
        path_save_fig (string): folder where the plot must be saved

    """
    plt.figure(figsize = (10,8))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.ylim((0,16))
    if len(Y) != len(labels):
        print("Number of labels and plots don't match!")
        return

    for i in range(len(Y)):
        y = Y[i]
        if type == "linear":
            plt.plot(x, y, label = labels[i])
        elif type == "semilogx":
            plt.semilogx(x, y, label = labels[i])
    plt.legend()
    try:
        os.mkdir(path_save_dir)
        print("folder created at " + path_save_dir)
    except FileExistsError:
        print("folder already exists at " + path_save_dir)
    path_save_fig = join(path_save_dir, title + ".png")
    plt.savefig(path_save_fig)
    print(title + ".png saved at " + path_save_fig)
    plt.close()

    return

########################################### Parsing the arguments ###################################################

parser = argparse.ArgumentParser()
parser.add_argument("--path_expt_folder", default = "../../experiments/experiment3/largescale/orig4", help = "folder for SNR variation with window size")
parser.add_argument("--path_store", default = "../../experiments/experiment3/largescale/", help = "path where all the results of this script are stored")
args = parser.parse_args()



############################################ Setting up local variables ##############################################

path_experiment3_folder = args.path_expt_folder #"../../experiments/experiment3/largescale/" # folder for SNR variation with window size
path_store = args.path_store #"../../experiments/experiment3/largescale/" # path where all the results of this script are stored


expts = listdir(path_experiment3_folder)
expts_paths = [join(path_experiment3_folder, name) for name in expts if name.endswith("ms")]
audio_name = path_experiment3_folder.rsplit("/")[-1]
# the experiment3.py must store all the folders with alpha, beta and numcomp specified in the title and must end with 
# the framesize in ms: blah_blah_40ms



Y_final = [] # To draw combined plots
SNR_mean = [] # To draw plots of average SNR vs time
SNR_vars = [] # To draw pltos of average of SNR vs frame size
labels_final = [] 
times = [] # To store the frame size details for the X axis


############################################ Constructing final Y, labels and SNR means ################################

for path in expts_paths:
	print("path " + path)
	tag = path.rsplit("_", 1)[-1]
	print("tag " + tag)
	files_list = listdir(path)
	for file in files_list:
		if file.endswith("pickle"):
			filepath = join(path, file)
	Y, labels, R = obtain_variables_from_pickle(filepath)
	title = "Experiment3_SNR_windows" + "_" + tag


	savefigure1(title, "Number of components", "Average of SNR over all sources", Y, labels, R, path_store)
	
	Y_final.extend(Y)
	
	for i in range(len(Y)):
		SNR_mean.append(np.mean(Y[i]))
		SNR_vars.append(np.var(Y[i]))


	labels_temp = [label + "_" + tag for label in labels]
	labels_final.extend(labels_temp)


# Yfinal 
# m = num_frame_sizes x num_windows_tried
# n = range of components tried (say from 7 to 40 or so)
# shape(Yfinal) = m x n
# Yfinal is a list. It contains elements in the following sequence (list of snr with number of components is abbreviated as s, ti = ith framesize)
# [s_hann_t1, s_hamming_t1, s_blackmanharris_t1, s_some_other_windows_t1, s_hann_t2, s_hamming_t2, s_blackmanharris_t2, s_some_other_windows_t2,... ]

# labels_final
# length = num_frame_sizes x num_windows_tried
# labels_final = list
# following sequence (every element is a string, quotes omitted)
# [hannt1, hammingt1, blackman harrist1, hannt2, hammingt2, blackman harrist2, ... ]

# SNR_mean
# length = num_frame_sizes x num_windows_tried
# SNR_mean is a list. Every element is an average of the SNRS produced with a given window, with a given framesize over the number of components
# following sequence (every element is an average)
# [snrmean_hannt1, snrmean_hammingt1, snrmean_blackmanharrist1, snrmeant_windowst1, snrmean_hannt2, snrmean_hammingt2,
# snrmean_blackmanharrist2, snrmeant_windowst2, ... ]

# SNR_vars = variances instead of means

print(np.shape(Y_final), "Y_final")
print(np.shape(labels_final), "labels_final")
print(np.shape(SNR_mean), "SNR_mean")
print(np.shape(SNR_vars), "SNR_vars")
# print(labels_final)
# print(SNR_mean)


# Determining windows used

windows = []
for i in range(len(labels_final)):
	label = labels_final[i].rsplit("_", 1)[0]
	if not(label in windows):
		windows.append(label)

print(windows)

# windows
# list of length number of windows used
# list containing the names of all the windows used in experiment3


# Creating the dictionaries of SNR_means
# SNR_averages
# dictionary with num_keys = num_windows_used
# key - window used
# value - [list of frame sizes used, list of average snr values]
SNR_averages = {}
SNR_variances = {}
for window in windows:
	SNR_averages_window = []
	SNR_variances_window = []
	frame_size_window = []
	for i in range(len(labels_final)):
		if labels_final[i].startswith(window):
			SNR_averages_window.append(SNR_mean[i])
			SNR_variances_window.append(SNR_vars[i])
			tag = labels_final[i].rsplit("_",1)[-1]
			time = float(tag[:-2])
			frame_size_window.append(time)
	
	# sorting the frame sizes from the smallest to the largest
	frame_size_window_sorted, SNR_averages_window_sorted = zip(*sorted(zip(frame_size_window, SNR_averages_window)))
	window_info = [frame_size_window_sorted, SNR_averages_window_sorted]
	window_info_vars = [frame_size_window, SNR_variances_window]
	SNR_averages[window] = window_info
	SNR_variances[window] = window_info_vars

# print(SNR_averages)


# write this averages data to a folder for later use.
# idea being:
# Write the SNR averages file to one folder with the audio name in the pickle file name
# EG. audioname_snraverages.pickle
# reload this pickle file and multiply by the number of components from the text file 

# audio_averages_folder = "averages" + audio_name + "_" + "SNR_averages.pickle"
# # path is "blahblah/experiment3/largescale/"
# path_audio_averages = join(path_store, audio_averages_folder)

# with open(path_audio_averages, "wb") as handle:
# 	pickle.dump(SNR_averages, handle, protocol = pickle.HIGHEST_PROTOCOL)




################################################## Plotting #######################################
# Creating a plot of SNR averages
labels = []
Y = []
R = []
for key in SNR_averages:
	if key != "Chebyshev": # introduced because large scale experiment not conducted for chebyshev windows 
		print(key)
		labels.append(key)
		average = SNR_averages[key][1]
		r = SNR_averages[key][0]
		r_sorted, average_sorted = zip(*sorted(zip(r,average)))
		r_sorted, average_sorted = r, average
		Y.append(average_sorted)
		
		if len(r_sorted) > len(R):
			R = r_sorted

# print(R)
# print(np.shape(Y))
# print(labels)

savefigure1("Variation_of_SNR_with_windows", "frame size" , "average snr over sources and components", Y, labels, R, path_store)





# Creating a plot of SNR variances
labels = []
Y = []
R = []
for key in SNR_variances:
	print(key)
	labels.append(key)
	var = SNR_variances[key][1]
	r = SNR_variances[key][0]
	r_sorted, var_sorted = zip(*sorted(zip(r,var)))
	Y.append(var_sorted)
	
	if len(r_sorted) > len(R):
		R = r_sorted
# savefigure("Variance_of_SNR_with_windows", "frame size" , "average snr over sources and components", Y, labels, R, path_store)










# path_experiment3_40ms = "../../experiments/experiment3/alpha_10_beta_0.1_numcomp_40_40ms/Experiment3_10_1_0.04.pickle"
# # path_experiment3_40ms = "../experiments/experiment3/temp/Experiment3_10_1_0.04.pickle"


# with open(path_experiment3_40ms, "rb") as handle:
# 	results = pickle.load(handle)


# Y = results["Y"]
# labels = results["labels"]
# R = results["R"]
# if type(R) != list:
# 	print("creating R due to original error")
# 	R = np.arange(R - len(Y[0]), R, 1)

# savefigure("Experiment3_SNR_windows", "Number of components", "Average SNR over all sources", Y, labels, R,"../../experiments/experiment3/combined_stuff")
