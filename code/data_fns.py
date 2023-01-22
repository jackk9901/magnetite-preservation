# import packages
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


## Data Interpolation ##
# df is dataframe to interpolate in, cols is a list of columns (excluding sed rates) to interpolate
# assume that df contains depth column labeled "Depth [mbsf]", and is sorted by depth in ascending order (shallow->deep)
# if sed rate is set to true, we assume that a column labeled "Sedimentation Rate [m/Ma]" exists
# set sed rate to false if no sed rates in data
# fill_final_rates: do you want the lowest sed rate value to extend down for the rest of the data?
def interpolate(df, cols, sed_rates=True, fill_final_rates=True):
    # interpolate works by looking at the row indices, so set the row indices to be depth
    # using "both" for limit direction means that NaNs can get filled from above or below
    interpolated = df.set_index("Depth [mbsf]")  # returns new object, not directly editing input df
    interpolated[cols] = interpolated[cols].interpolate(method="values", limit_direction="both")

    # do sed rates if requested--use the bfill method of the fillna function
    # this doesn't handle any NaNs below the final sed rate point, will handle those below
    if sed_rates:
        interpolated["Sedimentation Rate [m/Ma]"] = interpolated["Sedimentation Rate [m/Ma]"].fillna(method="backfill")

    # we have been using the depth as an index, all done with that now.
    # reset index restores depth as one of the columns
    interpolated.reset_index(inplace=True)

    # last, fill in the final few sed rate rows if requested, using last_valid_index
    if sed_rates and fill_final_rates:
        last_ind = interpolated["Sedimentation Rate [m/Ma]"].last_valid_index()
        if last_ind < len(interpolated["Sedimentation Rate [m/Ma]"]) - 1:  # if we aren't at the end already
            interpolated["Sedimentation Rate [m/Ma]"].iloc[last_ind + 1:] = \
                interpolated["Sedimentation Rate [m/Ma]"][last_ind]

    return interpolated


## Calculating Sed Rate ##
# calculate sedimentation rate between 2 points, each with a date (in Ma) and a depth (in m)
# returns a list of rates that you can put into a df as a column
# will insert nan values where necessary so that length/spacing of values is correct
def sed_rates(age_col, depth_col):
    rates = []
    for i in range(len(age_col)):
        if pd.notna(age_col[i]) and pd.notna(depth_col[i]):  # don't try to do this if we have any NaNs
            if i == 0:  # edge case: doesn't work for first item
                # if top depth is zero, we essentially have no sed rate info for that point, so leave it alone
                if depth_col[i] == 0:
                    rates.append(np.nan)
                else:
                    # if not zero, calculate sed rate from top of core
                    rates.append(depth_col[i] / age_col[i])
            else:
                # rate is (depth - depth above) / (age - age above)
                rates.append((depth_col[i] - depth_col[i-1]) / (age_col[i] - age_col[i-1]))
        else:  # adding nans when necessary so that everything will line up in the end
            rates.append(np.nan)
    return rates


## Converting Sample Label to Depth ##
# helper function read in the summary data and mess with the columns for indexing purposes
# the other converting functions assume that we can lookup by core and section (as a MultiIndex)
# the formatting of this function may be invalid for some data (works for Brachfeld 2001)
def read_summaries(excel, sheet):
    initial = pd.read_excel(excel, sheet_name=sheet)
    # make a MultiIndex with core and then section numbers
    adjusted = initial.set_index("Core No ").set_index(" Sect", append=True)
    return adjusted


# helper function to set section index correctly
def set_section(summary, split_label):
    # Pad core number with a space on either end based on formatting of excel sheet
    # If CC sample, look up correct section index, which is the last item in indices list for the hole
    if split_label[3][0] == "C":
        sect_ind = summary.loc[" " + split_label[2] + " "][" Section Top Depth (mbsf) "].index[-1]
    else:  # convert to float
        sect_ind = float(split_label[3][0])

    sect_top = summary.loc[" " + split_label[2] + " "][" Section Top Depth (mbsf) "][sect_ind]
    return sect_top


# the main function
# assumes label intervals are in cm (probably a good assumption?)
# output is going to be a list (which you can put into a DF as a column)
def depth_convert(sample_labels, A_sum, B_sum, C_sum):
    depths = []
    for i in range(len(sample_labels)):
        # take the label string and split it by comma
        comma_split = sample_labels[i].split(",")
        # now we have the label and the interval

        # find the midpoint of the interval
        endpoints = comma_split[1].split("-")
        midpoint = ((float(endpoints[0]) + float(endpoints[1])) / 200)
        # divide by 200 instead of 2 b/c endpoints are in cm, not m

        # deal with the label
        label = comma_split[0].split("-")
        # now we have: [leg, hole number/letter, core number, section number]

        # what letter hole is this? tells us what summary sheet to use
        letter = label[1][-1]  # last char in the string

        if letter == "A":
            sect_top = set_section(A_sum, label)
        elif letter == "B":
            sect_top = set_section(B_sum, label)
        elif letter == "C":
            sect_top = set_section(C_sum, label)

        # the mbsf depth of the sample is the interval midpoint plus the depth of the section top
        sample_depth = midpoint + sect_top
        depths.append(sample_depth)  # put this depth in the list
    # return the list of depths
    return depths


## Plotting ##
# function for plotting downcore parameters
# assuming that depth is labeled as "Depth [mbsf]"
# just setting up the basic stuff, then returning the figure and axes
# that way you can mess with labels, limits, etc on your own
def plot_dc(param_names, df, colors, markers, markersize=2):
    # number of subplots determined by length of parameters
    fig, axs = plt.subplots(1, len(param_names), sharey="all")

    for i in range(len(axs)):
        axs[i].plot(df[param_names[i]], df["Depth [mbsf]"], color=colors[i],
                    marker=markers[i], markersize=markersize, linestyle="None")
        if i == 0:  # only do this for first subplot
            axs[i].set_ylabel("Depth [mbsf]")
            axs[i].invert_yaxis()
        axs[i].set_ylim(top=0)
        axs[i].set_xlabel(param_names[i])
        axs[i].set_xlim(xmin=0)

    return fig, axs


# function for doing comparison plots
# assuming that magnetite is labeled "Magnetite [ppm]"
# same as above, just setting up basic stuff then returning figure and axes
# function similar to above, but returns many figures and axes (one for each comparison)
# units (string) lets you choose what magnetite values to plot (assumes default of ppm)
def plot_comp(param_names, df, colors, markers, units="Magnetite [ppm]", markersize=2):
    figs = []
    axs = []
    for i in range(len(param_names)):
        fig, ax = plt.subplots()
        ax.plot(df[units], df[param_names[i]], color=colors[i],
                marker=markers[i], markersize=markersize, linestyle="None")
        figs.append(fig)
        axs.append(ax)
    return figs, axs


# function to plot sed rates
# average values within a rate and plot, setting marker size as number of values
# takes interpolated dataframe as input
def sed_avg_plot(df, scale=1):
    # not all sed rate intervals will have any magnetite points, so drop rows that are nan for magnetite
    # need to drop nans or else numpy will return nan for the mean
    dropped = df.dropna(subset=["Magnetite [ppm]"])
    grouped = dropped.groupby("Sedimentation Rate [m/Ma]")

    # now we have a grouped DF. Let's do some statistics
    # reset the index because it is currently sedimentation rate
    avgd = grouped.agg([np.mean, np.std, np.size]).reset_index()

    # now plot the averaged values
    fig, ax = plt.subplots()
    sc = ax.scatter(avgd["Magnetite [ppm]"]["mean"], avgd["Sedimentation Rate [m/Ma]"], c="g",
                    s=avgd["Magnetite [ppm]"]["size"]*scale)
    return fig, ax, sc


## Writing Output ##
# function to append data to a compilation excel sheet
# file is a string that locates the excel file to write to
# generally call this twice--once for the raw data and once for the interpolated data
def write_output(output, sheet_name, file):
    with pd.ExcelWriter(file, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        output.to_excel(writer, sheet_name=sheet_name, index=False)
