# Note on this FORKED version of SAC-SMA from Newman et al (2017)
The original SAC-SMA repository can be found [here](https://github.com/Upstream-Tech/SACSMA-SNOW17)

The present paper uses this model only to under evaluation mode. The original outputs and model parameters were collected directly from the CAMELS(US) sources [here](https://ral.ucar.edu/solutions/products/camels)

# Key adaptation to our context study
The SAC-SMA model was forked first, after a successful re-run, we performed the climatology mode proposed in the present paper.
This approach consist of evaluating (apply the data only) the model on slices of data with 365 days of sequence length, and an extension in respect of lead time. 
The used lead times are 1-, 3- and 7 days. All the seeds (run_number) provided was also used. 
The median output of all these seeds was used in one of the strategies tested in the said study.


# Instructions for the runs we performed
The argument required to run the SAC-SMA model in our case are outlined below:
- hp: the lead time (integer)
- period: the evaluation period. It is generally taken as the last year of the available data. But we took the 2 last years for a larger overview
- forcing source, it could be any from *maurer*, *daymet* and *nldas*
- n_sub :  a parameter to splut the period on the available CPU of the used machine
- list_run: indicate which seed to use
- path_to: path to save the climatology output
- data_path: the camels_root where data will be grabbed
- sample_basins: useful for testing, but in the paper it is 56


### Example:
the command below apply the climatology run for the 20080801-20080820 on two basins and use the seeds (run) 05 and 11 only. 
Save the raw output into path/to/climatology_run, grab the camels_us data in path/to/CAMELS_US_DATA

````
python run_multi.py --hp 1 --period "20080801,20080820" --forcing_src maurer --n_sub 5 --sample_basins 2 --list_run 05 11 --path_to path/to/save/climatology_run --data_path path/to/CAMELS_US_DATA
````

# Run like we did in our paper
you will need to iterate of the lead time list *\[1, 3, 7]* or use a jupyter notebook for more convenience, set your paths accordingly

````
python run_multi.py --hp 1 --period "20060720,20080820" --forcing_src maurer --n_sub 5 --sample_basins 56 --path_to path/to/save/climatology_run --data_path path/to/CAMELS_US_DATA
````

### Local example (only for our machine)
````
python run_multi.py --hp 1 --period "20080801,20080810" --forcing_src maurer --n_sub 5 --sample_basins 2 --path_to Y:\repo_egu24\outputs\test_sacsma_runs --data_path Y:\repo_egu24\data\camels_us
````


## Post-process your runs
The raw climatology outputs are stored in the directory you specified, but extended with an extra *hpx/* sub-directory. You may need to use one of the notebook we provided for the post process, but the idea is simple.
These outputs need to be reformatted from one-file-per-basin-per-seed-per-hp to ONE multi index dataframe. This multi-index should be (context, basin, hp, year, seed, Date) and the column will be (prediction).
Save it in a FILE.parquet.gzip for faster processing.
