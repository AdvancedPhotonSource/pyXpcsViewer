# xpcs viewer
A python-based interactive visualization tool to view XPCS dataset.


## Supported Format

Only the APS-8IDI's XPCS data format is supported, for both multi-tau and two-time correlation. The nexus file format for XPCS measurement, which is still under
discussion, is not supported yet.

 ## Install and Uninstall

If your python environment is outdated or if you don’t have python3 installed, it highly recommends installing the newest version of [anaconda3](https://www.anaconda.com/products/individual). 

 If you have critical python applications installed and you don't want xpcs-viewer to break their dependencies, it's recommended to setup a [virtual environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to isolate xpcs-viewer. 

To install, open a terminal (or _"Anaconda Prompt"_ on windows) and run

```bash
pip install xpcs-viewer
```

Alternatively, you may just clone/download this repository.

To run the viewer, open a terminal (or _"Anaconda Prompt"_ on windows) and run

``` bash
run_viewer path_to_hdf_directory		# run the viewer from the hdf directory, or
run_viewer										      # run in the current directory
```

To uninstall:

``` bash
pip uninstall xpcs-viewer
```

## Gallery
1. The integrated scattering pattern over the whole time series.
  ![saxs2d](/docs/images/saxs2d.png)

2. The reduced one-dimensional small-angle scattering data.
  ![saxs1d](/docs/images/saxs1d.png)
  
3. The sample's stability against X-ray beam damage. The time series is divided into 10 sections. The SAXS-1D curve is plotted for each section.
  ![stability](/docs/images/stability.png)
  
4. Intensity fluctuation vs Time.
  ![intt](/docs/images/intt.png)

5. Average Tool box
  ![average](/docs/images/average.png)
  
6. g2 plot for multitau analysis. User can fit the time scale using the single exponential function, with the option to specify the fitting range and fitting flags (fix or fit).
  ![g2](/docs/images/g2mod.png)

7. Diffusion analysis. g2 fitting in the previous panel is required to plot $\tau \mbox{vs.} q$.
  ![diffusion](/docs/images/diffusion.png)

8. Twotime correlation. User can select two q indexes either on the qmap or on the SAXS2D image.
  ![diffusion](/docs/images/twotime.png)

9. Experiment condition viewer. It reads the file structure and string entries of the HDF file selected.
  ![hdf-info](/docs/images/hdf_info.png)
 
