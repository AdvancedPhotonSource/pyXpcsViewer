============
pyXPCSViewer
============

A python-based interactive visualization tool to view XPCS dataset.

To cite pyXPCSViewer:  

Chu et al., *"pyXPCSviewer: an open-source interactive tool for X-ray photon correlation spectroscopy visualization and analysis"*, 
`Journal of Synchrotron Radiation, (2022) 29, 1122–1129 <https://onlinelibrary.wiley.com/doi/epdf/10.1107/S1600577522004830>`_.

Supported Format
----------------

This tools supports the customized nexus fileformat developed at APS-8IDI's XPCS data format for both multi-tau and two-time correlation. 

Install and Uninstall
---------------------
Updated 03/11/2025

It is highly recommended to set up a new `virtual environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_
to isolate pyXPCSViewer, so it does not interfere with dependencies of your existing applications.

0. Install conda following the instructions at `link <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`_.

1. Create a brand-new environment with conda:

   .. code-block:: bash

      conda create -n your_env_name python==3.10.16

   Replace **your_env_name** with your preferred environment name.

2. Activate the new environment:

   .. code-block:: bash

      conda activate your_env_name

3. Install pyXPCSViewer:

   .. code-block:: bash

      pip install xpcs-viewer

   **Note:** Running conda and pip commands together is generally not recommended. pyXPCSViewer will only use pip or conda once compatibility issues are resolved.

4. Launch pyXPCSViewer:

   1. Activate your environment if you have not already.
   2. Run:

      .. code-block:: bash

         pyxpcsviewer path_to_hdf_directory   # Run the viewer from the hdf directory
         pyxpcsviewer                         # Run in the current directory

    run_viewer, an alias to pyxpcsviewer, can also be used to luanch the viewer.

5. To upgrade:

   1. Activate your environment if you have not already.
   2. Run:

      .. code-block:: bash

         pip install -U xpcs-viewer

6. To uninstall:

   1. Activate your environment if you have not already.
   2. Run:

      .. code-block:: bash

         pip uninstall xpcs-viewer

   3. If you want to remove the environment altogether, first deactivate it:

      .. code-block:: bash

         conda deactivate

      Then remove it:

      .. code-block:: bash

         conda remove -n your_env_name --all

Gallery
-------

1. The integrated scattering pattern over the whole time series.

   .. image:: docs/images/saxs2d.png

2. The reduced one-dimensional small-angle scattering data.

   .. image:: docs/images/saxs1d.png

3. The sample's stability against X-ray beam damage. The time series is divided into 10 sections. The SAXS-1D curve is plotted for each section.

   .. image:: docs/images/stability.png

4. Intensity fluctuation vs. Time.

   .. image:: docs/images/intt.png

5. Average Tool box.

   .. image:: docs/images/average.png

6. g2 plot for multitau analysis. Users can fit the time scale using a single exponential function, with options to specify the fitting range and fitting flags (fix or fit).

   .. image:: docs/images/g2mod.png

7. Diffusion analysis. g2 fitting in the previous panel is required to plot :math:`\tau \mbox{vs.} q`.

   .. image:: docs/images/diffusion.png

8. Two-time correlation. Users can select two q indexes either on the q-map or on the SAXS-2D image.

   .. image:: docs/images/twotime.png

9. Experiment condition viewer. It reads the file structure and string entries of the selected HDF file.

   .. image:: docs/images/hdf_info.png