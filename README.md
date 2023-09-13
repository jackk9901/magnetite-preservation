# Magnetite Preservation and Diagenesis in Marine Sediments
This GitHub repo contains data and code related to "Magnetite Preservation and Diagenesis in Marine Sediments," Dartmouth College Department of Earth Sciences Senior Thesis by Jack Kreisler (advised by Sarah Slotznick).
## Data
The data presented in the thesis are all provided in the `data` folder. There is one Excel file per site. If multiple sites are close together or their data was originally published together, they are grouped together in a subfolder. The most relevant files include:
- `comp_inter`: All data compiled into one file, one site per sheet. This is the *interpolated* data--sulfate, sedimentation rate, total organic carbon, and any other diagenetic parameters have been interpolated (see Supplemental Text for more details) to allow for comparison with magnetite abundance data.
- `comp_raw`: All data compiled into one file, one site per sheet. This is the *raw* data, with no interpolation.
- `kreisler-m0063`: Data from analysis of sediment samples from IODP Expedition 347 Site M0063 Hole D. All other data presented in the thesis have been previously published, but this data is new and first published here.

## Code
The code used to analyze the data and generate the figures in the main text and supplement is all in the `code` folder. All analysis and plotting was done in Jupyter Notebooks using a Python kernel. There is (in general) one file per site. Main text figures were produced using the `histograms` and `compilation_plots` files. Since many of the tasks are repetitive from site to site (import and clean data, synchronize depth scales, interpolate, plot), we created and also provide here a small library of functions for convenience (see `data_fns`).

### Software Versions
Written in PyCharm 2022.2.3 using Python 3.8, pandas 1.3.5, matplotlib 3.5.0, numpy 1.20.3, cartopy 0.18.0, and jupyter 1.0.0
