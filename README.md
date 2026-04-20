# Note on this FORKED version of SAC-SMA from Newman et al (2017)
The original SAC-SMA repository can be found [here](https://github.com/Upstream-Tech/SACSMA-SNOW17)

The present paper uses this model only to under evaluation mode. The original outputs and model parameters were collected 
  directly from the CAMELS(US) sources [here](https://ral.ucar.edu/solutions/products/camels)

# Key adaptation to our context study
The SAC-SMA model was forked first, then we performed the climatology mode proposed in the present paper, which consists
of evaluating the model on slices of data with 365 days of sequence length extended by the lead time. 
The used lead times range from 1 to 7 days. All the seeds (run_number 05, 11, ... ) provided was also used.


# Instructions for the runs we performed
First, make sure the fortran file are properly compiled in your system, by following the original README.txt instructions
Then, make sure the modules of the requirements.txt are installed
If you want to use UV, make sure it is installed on your system

The argument required to run the SAC-SMA model in our case are outlined below:
- run_mode: whether _climatology_, or _hindcast_, ... e.g ( --run_mode hindcast )
- hp: the lead time (integer), e.g. ( --hp 1 )
- period: the evaluation sub-period (19891001-19910930), e.g.  ( --period 19891001 19910930 )
- forcing source, it could be any from *maurer*, *daymet* and *nldas*, e.g. ( --forcing_src maurer )
- n_sub :  a parameter to split the period for faster parallel runs based on number of CPUs, e.g. ( --n_sub 8 )
- list_run: indicate which seed to use (omit this argument blank to run all)
- path_to: path to save the outputs (omit to save close to data_path)
- data_path: the camels_root where data will be grabbed, e.g. ( --data_path data/camels_us )
- basins_file: use a file for the list of basins to consider, e.g. ( --basins_file data/basins_56 )
- start_bv: start with basin #10 in the list ( --start_bv 9 )


### Example:
the command below apply the climatology run for the 19901001-19910930 on two basins and use the seeds (run) 05 and 11 only. 
Save the raw output into path/to/climatology_run, grab the camels_us data in path/to/CAMELS_US_DATA

Main cmd structures
````
python run_multi.py --run_mode xxxxxx --hp 1 --period yyyymmdd yyyymmdd --forcing_src maurer --n_sub 1 --data_path path/to/CAMELS_DATA --basins_file path/to/basins_list_file --start_bv 0 --path_to path/to/store
````
Where:
 - xxxxx should be replaced by climatology or hindcast
 - x by the lead time
 - start_bv, path_to, n_sub are all optional, if not needed, don't use them

#### 1. In powershell, type the following
````
uv run python run_multi.py --hp 2 --run_mode hindcast --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path data\camels_us --basins_file data\basins_56 --start_bv 0 --path_to theere
````

#### 2. In a pycharm terminal, try the following after managing virtual environment properly using the requirements.txt and a python 3.9

##### Hindcast run
````
python run_multi.py --hp 2 --run_mode hindcast --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path data\camels_us --basins_file data\basins_56 --path_to theere
````

##### Climatology run
````
python run_multi.py --hp 2 --run_mode climatology --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path data\camels_us --basins_file data\basins_56 --path_to theere
````

# Run as in this Paper
you will need to iterate of the lead time list *\[1..7]*. You may also need to relaunch as some crashs may occur during 
parallelization. If any relaunch, only failed runs are resumed. You may also need to clean the directory by removing 
incomplete runs as the files are expected to have almost the same size. For any complete reruns, choose another saving 
directory (--path_to new_dir) or clean the last parent directory manually.

Note: You may find a basins_2.txt file to perform quick test, consider also reducing the period to couple of days ( ~30)

--data_path path/to/camels_us
--basins_file path/to/basins_56
--period 19891001 19910930

## Post-process your runs
The raw outputs are stored in the directory you specified, as in following:
- Hindcast: *path_to/hindcast_bm/sacsma/raw/hpx/*
- Climatology : *path_to/climato_bm/sacsma/raw/hpx/*

Files are named as **proc_seeds_01052500_11.csv** for basin *01052500* and seed *11*

These outputs need to be reformatted from one-file-per-basin-per-seed-per-hp to ONE multi index dataframe. 
This multi-index should be (context, basin, hp, year, seed, Date) and the column will be (prediction).
Save it in a FILE.parquet.gzip for faster processing.
