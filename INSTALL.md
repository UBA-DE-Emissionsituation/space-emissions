#  Requirements and Installation

</br>

In order to use the spaceborne-emission calculator efficiently also on your platform we would recommend the usage of the "Fast Cross-Platform Package Manager" [Mamba](https://github.com/mamba-org/mamba), which will handle all the necessary dependencies for the spaceborne-emmission calculator following the setup procedure described here from scratch:

</br>



* Get the necessary python version and a packagemanager for handling virtual python environments, if you do not already have a tool for managing these environments. This is a an important step as we strongly advise you to not alter your operating systems own python environment as there is the potential to break dependencies and render other programs non-functional when installing additional packages or changing your systems python version.</br>
We would like to reccommend to use the binary python _3.X_ installers if you start from scratch using these [Binaries](https://github.com/conda-forge/miniforge#mambaforge), which are available for most computing platforms. 

</br>


* After the installation process of the binaries you might need to close and reopen your terminal window. Windows users: please look/search for "miniforge" in your start menu and launch it to follow the next steps.

</br>


* - Create your new python environment with: [`mamba create -n py39spaceborne python=3.9`] </br>   
For the space-emissions tool you need to use Python>=3.9.</br>
   - Activate your new environment: [`conda activate py39spaceborne`] </br>
   - Install your dependencies: [`mamba install jupyterlab gdal geopandas shapely numpy rtree pyproj contextily pytest sentinelsat cdsapi requests h5py netcdf4 -c conda-forge`] 
</br>


 * The shorthand version for the three steps outlined above would be: [`mamba create -n py39spaceborne python=3.9 jupyterlab gdal geopandas shapely numpy rtree pyproj contextily pytest sentinelsat cdsapi requests h5py netcdf4 -c conda-forge`]
</br>

</br>


* Now you should be able to run the Jupyter notebooks from the spaceborne-emission calculator given that you have activated your new environment with [`conda activate py39spaceborne`] and you are seeing `py39spaceborne` in your shell before your command prompt. To start up Jupyter Notebook just type and execute [`jupyter-notebook`] in your shell.
