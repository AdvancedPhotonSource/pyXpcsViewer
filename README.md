# pyXPCSViewer
A python-based interactive visualization tool to view XPCS dataset.

To cite pyXpcsViewer: 
Chu et al., "pyXPCSviewer: an open-source interactive tool for X-ray photon correlation spectroscopy visualization and analysis", Journal of Synchrotron Radiation, (2022).29, 1122–1129


## Supported Format

Only the APS-8IDI's XPCS data format is supported, for both multi-tau and two-time correlation. The nexus file format for XPCS measurement, which is still under
discussion, is not supported yet.


## Install and Uninstall
 

It's highly recommended to setup a new [virtual environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to isolate pyXPCSViewer, so it doesn't mess up the dependencies of your existing applications.

0.  Install conda following the instructions at [link](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

1. It's highly recommended to setup a new [virtual environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to isolate pyXPCSViewer, so it doesn't mess up the dependencies of your existing applications. Create a brand-new environment with conda

	```
	conda create -n your_env_name python==3.9.7
	``` 
	Replace **your\_env\_name** with your choice of environment name. 

2.  Activate the new environment for your pyXPCSViewer

	```
	conda activate your_env_name
	```

3.  Install pyXPCSViewer
	
	```
	pip install xpcs-viewer
	```
	Please note, running conda and pip commands together is generally not recommended. pyXPCSViewer will only use pip or conda once its compatibility issues are resolved.
4.  Launch pyXPCSViewer

    1.  Activate your environment described in step 2 if you haven’t.
    2.  run
  
		``` bash
		run_viewer path_to_hdf_directory        # run the viewer from the hdf directory, or
		run_viewer                              # run in the current directory
		```
	3. On MacOS and Linux, you can create an alias in .bashrc (or .zshrc if you're using zsh) like 
	 
	 ``` bash
	 alias your_shortcut_name='conda activate your_env_name; run_viewer $@; conda deactivate'
	 ```
	 then source your rc file (```source .bashrc```) and you can run ```your_shortcut_name``` to launch pyXPCSViewer directly.
5.  To upgrade:
	 1.  Activate your environment described in step 2 if you haven’t.
	 2.  run

	``` bash
	pip install -U xpcs-viewer
	```
6.  To uninstall:
	 1.  Activate your environment described in step 2 if you haven’t.
	 2.  run
	 
	``` bash
	pip uninstall xpcs-viewer
	```
	 3. If you want to remove the environment all together, first deactivate the environment with ```conda deactivate```, if you're in the pyXPCSViewer environment, then run
	
	``` bash
	conda remove -n your_env_name --all
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
 
