#!/bin/env python3

# Ex. python run_multi.py --hp 1 --run_mode hindcast --period 19891001 19910930 --forcing_src maurer --n_sub 12 \
# --data_path path/to/data/camels_us --basins_file path/to/basins_56 --start_bv 0

import os
from pathlib import Path
from glob import glob
from xtools.arg_utils import get_run_args
from xtools.run_scasma import run
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp


def par_proc(func, tasks, num_cpus=None):
    """
    Broadcast tasks on a function through n_cpus.

    :param
        - func: function that accepts a task
        - tasks: list of tasks
        - num_cpus: number of tasks in a round, limited by num_cpus
    :return:
        - list of results
    """
    if num_cpus is None:
        num_cpus = mp.cpu_count()
    num_cpus = min(num_cpus, len(tasks))
    results = []
    with ProcessPoolExecutor(max_workers=num_cpus) as executor:
        futures = [executor.submit(func, **task) for task in tasks]
        for f in as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                # print(e)
                results.append(None)
    return results


def run_parallel(func_, arg0):
    """
    Ru function in parallel by unfolding arguments.

    :param
        - func_: function that accepts an arg(dict)
        - arg0: the master arguments to be unfolded in n args
    """
    x_mode = "climato_bm" if arg0["run_mode"].startswith("clim") else arg0["run_mode"] + "_bm"
    x_mode = x_mode + "/sacsma"
    id_file = arg0["discr_model"]
    if arg0["path_to"] is None:
        path_to = str(Path(arg0["data_path"]).parent)
    else:
        path_to = arg0["path_to"]
    sub_dates = arg0["sub_dates"]
    base_cfg = {k: v for k, v in arg0.items() if k != "sub_dates"}
    base_cfg["n_sub"] = 1
    tasks = [{"arg_run": {**base_cfg, "period": p}} for p in sub_dates]
    results = par_proc(func_, tasks)
    results = [r for r in results if r is not None]
    if len(results) != 0:
        proc_seed = pd.concat([a[0] for a in results], axis=0).sort_values(by="Date")
        bv_run = results[0][1]
        path_to_ = path_to + f"/{x_mode}/raw/{bv_run.split('_')[-1]}"
        os.makedirs(path_to_, exist_ok=True)
        proc_seed.to_csv(rf"{path_to_}/proc_seeds_{id_file}.csv", sep=";", index_label="Date")


def launch():
    """
    Launch evaluation on passed arguments
    """
    inputs = get_run_args()
    inputs["path_to"] = str(inputs.get("path_to", Path(inputs["data_path"]).parent))
    basins = sorted(inputs.get("basin_list", []))
    configs = ()
    for basin in basins:
        cfg = inputs.copy()
        cfg["basin"] = basin
        cfg.pop("basin_list")
        for id_run_ in cfg["list_run"]:
            temp_inp = cfg.copy()
            temp_inp['id_run'] = id_run_
            temp_inp.update({"discr_model": f"{basin}_{id_run_}"})
            configs += (temp_inp,)
    dict_path_to = {"climatology": f"climato_bm/sacsma/raw/hp{inputs['hp']}",
                    "hindcast": f"hindcast_bm/sacsma/raw/hp{inputs['hp']}"}
    run_path = inputs["path_to"] + "/" + dict_path_to.get(inputs["run_mode"])

    # Filter on pre-runs
    configs = [a for a in configs if a["discr_model"] not in [Path(b).stem.split('proc_seeds_')[1] for b \
                                                              in glob(str(run_path) + f"/*{a['basin']}*.csv")]]
    if len(configs) == 0:
        print("Nothing left to run. All passed basins and seed are already implemented")
        return
    print(f"\n *********** RUN concerns {len(configs)} jobs for HP :{configs[0]['hp']}  *********************")
    for cfg in tqdm(configs):
        run_parallel(run, cfg)


if __name__ == '__main__':
    launch()
