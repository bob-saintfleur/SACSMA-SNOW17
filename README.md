# 1. Note on this FORKED version of SAC-SMA from Newman et al (2017)
The original SAC-SMA repository can be found [here](https://github.com/Upstream-Tech/SACSMA-SNOW17)

The present paper uses this model only to under evaluation mode. The original outputs and model parameters were collected 
  directly from the CAMELS(US) sources [here](https://ral.ucar.edu/solutions/products/camels)

# 2. Key adaptation to our context study
The SAC-SMA model was forked first, then we performed the climatology mode proposed in the present paper, which consists
of evaluating the model on slices of data with 365 days of sequence length extended by the lead time. 
The used lead times range from 1 to 7 days. All the seeds (run_number 05, 11, ... ) provided was also used.


# 3. Instructions for the runs we performed
## 3.1. Clone the adapted version
```` 
git clone https://github.com/bob-saintfleur/SACSMA-SNOW17.git -b hydro_uge
````

Mmake sure the fortran file are properly compiled in your system, by following the original README.txt instructions
Then, make sure the modules of the requirements.txt are installed
If you want to use UV, make sure it is installed on your system

## 3.2. The argument required to run the SAC-SMA model in our case are outlined below:
- `run_mode`: whether `climatology`, or `hindcast`, ... e.g ( `--run_mode hindcast` )
- hp: the lead time (integer), e.g. ( `--hp 1` )
- period: the evaluation sub-period (19891001-19910930), e.g.  ( `--period 19891001 19910930 `)
- forcing source, it could be any from *maurer*, *daymet* and *nldas*, e.g. (` --forcing_src maurer` )
- n_sub :  a parameter to split the period for faster parallel runs based on number of CPUs, e.g. ( `--n_sub 8` )
- `list_run`: indicate which seed to use (omit this argument blank to run all)
- `path_to`: path to save the outputs (omit to save close to data_path)
- data_path: the camels_root where data will be grabbed, e.g. ( `--data_path data_paper/data/camels_us` )
- basins_file: use a file for the list of basins to consider, e.g. ( `--basins_file data_paper/data/basins_56 `)
- start_bv: start with basin #10 in the list ( `--start_bv 1 `)


# 4 Examples
the command below applies the climatology run for the 19901001-19910930 on two basins and use the seeds (run) 05 and 11 only. 
Save the raw output into **path/to/climatology_run**, grab the camels_us data in **path/to/CAMELS_US_DATA**

## 4.1. Main cmd structures
````
python run_multi.py --run_mode climatology --hp 1 --period yyyymmdd yyyymmdd --forcing_src maurer --n_sub 1 --data_path path/to/CAMELS_DATA --basins_file path/to/basins_list_file --start_bv 0 --path_to path/to/store
````
Where:
 - start_bv, path_to, n_sub are all optional, if not needed, don't use them

#### 4.1.1. In powershell, type the following
````
uv run python run_multi.py --hp 2 --run_mode hindcast --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path data\camels_us --basins_file data\basins_56 --start_bv 0 --path_to theere
````

#### 4.1.2. In a pycharm terminal, try the following after managing virtual environment properly using the requirements.txt and a python 3.9

##### Hindcast run
````
python run_multi.py --hp 2 --run_mode hindcast --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path data\camels_us --basins_file data\basins_56 --path_to theere
````

##### Climatology run
````
python run_multi.py --hp 2 --run_mode climatology --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path data\camels_us --basins_file data\basins_56 --path_to theere
````

##### Hindcast run
```
python run_multi.py --hp 2 --run_mode hindcast --period 19901001 19901030 --forcing_src maurer --n_sub 3 --data_path Y:\repo_egu24\data_paper\data\camelsus\camels_us --basins_file Y:\repo_egu24\data_paper\data\camelsus\basins_2.txt --path_to theere
```


# 5. Run as in this Paper
you will need to iterate of the lead time list *\[1..7]*. You may also need to relaunch as some crashs may occur during 
parallelization. If any relaunch, only failed runs are resumed. You may also need to clean the directory by removing 
incomplete runs as the files are expected to have almost the same size. For any complete reruns, choose another saving 
directory (--path_to new_dir) or clean the last parent directory manually.

Note: You may find a `basins_2.txt` file to perform quick test, consider also reducing the period to couple of days ( ~30)

`--data_path path/to/camels_us`
`--basins_file path/to/basins_56`
`--period 19891001 19910930`

# 6. Post-process
The raw outputs are stored in the directory you specified, as in following:
- Hindcast: `path_to/hindcast_bm/sacsma/raw/hp[1-7]/`
- Climatology : `path_to/climato_bm/sacsma/raw/hp[1-7]/`

Files are named as `proc_seeds_01052500_11.csv `for basin `01052500` and seed `11`

These outputs need to be reformatted from one-file-per-basin-per-seed-per-hp to:
 - 1. A Date indexed one-file-per-basin-per-hp with mean on seed. Save in `data/hindcast_bm/sacsma/hp[1-7]/basin.csv`, 
   or `data/climato_bm/sacsma/hp[1-7]/basin.csv`.
 - 2. A multi index dataframe with One-file-per-hp for all basin, where multi-index should be `(context, basin, hp, year, seed, Date)` and the column will be `(prediction)`.
  Save it in a `FILE.parquet.gzip` for faster processing, with:
   - context="sacsma"
   - basin: 8-digit string ID of basin
   - hp: integer of lead time
   - seed: integer of the number of the seeds [1 to N]
   - year: Number of the member [1 to M], and -1 in the case of the deterministic (perfect) case
   - Date: yyyy-mm-dd date format
   - FILE: 
     - climatology : `sacsma_hp[1-7]_CLIM56.parquet.gzip`
     - hindcast: `sacsma_hp[1-7]_HIND56.parquet.gzip`
     - perfect or deterministic: `sacsma_hp[1-7]_PERF531.parquet.gzip`
   - save like in : `~/data_paper/processed/us/FILE.parquet.gzip `


[Note] The MLP runs use the `hindcast_bm/scasma/hp[1-7]/basin.csv` to perform the DA2 and the DA3 strategies


# 7. Plots
To explore the graphics, you should refer to the [MLP_UGE](https://gitlab.univ-eiffel.fr/bob.saint-fleur/ai_operational_hydroforecast.git) code and its readme.