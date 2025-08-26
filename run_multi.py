# --model_dir output/no_in_mlp_hp3/models --period 20060801,20080820 --discr_model 01022500 --n_sub 24
# !/bin/env python3

import multiprocessing as mp
from tqdm import tqdm
import os
import pickle
import queue
import time
from pathlib import Path
import pandas as pd
import psutil
from xtools.arg_utils import get_run_args
from xtools.run_scasma import run
from xtools.selectbv import select_bv_by_class, read_list_of_basins

SENTINEL = None


def do_work(pending_task, completed_task):
    """ use args and function and run as task while controling the flow"""
    # Get the current workers' name
    worker_name = mp.current_process().name
    time_cum, w_c = 0., 1
    while True:
        try:
            task = pending_task.get_nowait()
        except queue.Empty:
            time.sleep(0.01)
        else:
            try:
                if task == SENTINEL:
                    break
                time_start = time.perf_counter()
                work_func = pickle.loads(task["func"])
                result = work_func(**task["task"])
                completed_task.put({work_func.__name__: result})
                time_end = time.perf_counter() - time_start
                time_cum += time_end
                w_c +=1

            except Exception as e:
                print(f"{worker_name} task failed {str(e)}")
                completed_task.put({work_func.__name__: None})


def par_proc(job_list, num_cpus=None):
    """ Perform a parallel processing of running task using a list of task"""
    # Get the number of cores
    if not num_cpus:
        # num_cpus = mp.cpu_count() - 4
        num_cpus = psutil.cpu_count(logical=False)

    pending_task = mp.Queue()
    completed_task = mp.Queue()

    processes, results = [], []
    # task pointer
    num_tasks = 0
    for job in job_list:
        for task in job["tasks"]:
            exp_jobs = {}
            num_tasks += 1
            exp_jobs.update({'func': pickle.dumps(job['func'])})
            exp_jobs.update({'task': task})
            pending_task.put(exp_jobs)

    num_workers = num_cpus
    for c in range(num_workers):
        pending_task.put(SENTINEL)

    for c in range(num_workers):
        p = mp.Process(target=do_work, args=(pending_task, completed_task), daemon=True)
        p.name = f'worker{c}'
        processes.append(p)
        p.start()

    completed_task_counter = 0
    while completed_task_counter < num_tasks:
        results.append(completed_task.get())
        completed_task_counter += 1

    for p in processes:
        p.join(timeout=3)
        if p.is_alive():
            print(f"{p.name} still alive. Forced to terminate")
            p.terminate()
    return results


def bind_raw_seeds_dict(dict_seed: dict):
    dict_dx = {}
    for kdt in list(dict_seed):
        df_x = pd.DataFrame()
        for lst_y in list(dict_seed[kdt].keys()):
            nd_, nc_ = dict_seed[kdt][lst_y].shape
            ind_ = pd.date_range(start=kdt, periods=nd_)
            dfx = pd.DataFrame(dict_seed[kdt][lst_y], index=ind_, columns=[f"{lst_y}s{i + 1}" for i in range(nc_)])
            df_x = pd.concat([df_x, dfx], axis=1)
        dict_dx[kdt] = df_x
    return dict_dx


def run_parallel(func_=run, arg0=get_run_args()):
    """ Run func_ separately on dates. The dates are divided and ran separately on replicated config"""
    arg1 = arg0.copy()
    list_arg = []
    clim_default_p = str(Path(arg0["data_path"]).parent)+"climato_bm/sacsma/raw0"
    arg1.pop("sub_dates")
    arg1.update({"n_sub": 1})
    id_file = arg0["discr_model"]
    for period in arg0["sub_dates"]:  # this done only to ease parallel run based on dates splitted
        ge_ = arg1.copy()
        ge_.update({"period": period})
        list_arg.append(ge_)

    # List function and arguments pair
    list_task = [{"func": func_, "tasks": [dict(arg_run=cfgx) for cfgx in list_arg]}]
    results = par_proc(list_task)

    # get, bind and save results to specified path
    bv_run = list(set([results[i]['run'][-1] for i in range(len(results))]))[0]
    path_to = (clim_default_p if arg0["path_to"] is None else arg0["path_to"]) + f"/{bv_run.split('_')[-1]}"
    os.makedirs(path_to, exist_ok=True)
    proc_seed = pd.concat([results[i]['run'][0] for i in range(len(results))]).sort_values(by="Date")
    proc_seed.to_csv(rf"{path_to}/proc_seeds_{id_file}.csv", sep=";", index_label="Date")


def launch_all_basins():
    # Dispatch run on multiple basins
    inputs = get_run_args()
    if inputs["sample_basins"]:
        basins = select_bv_by_class(size=inputs["sample_basins"])
    elif inputs["basin_list"]:
        basins = inputs["basin_list"]
    elif inputs["discr_model"]:
        basins = [inputs["discr_model"]]
    else:
        basins = read_list_of_basins()
    basins.sort()

    n_run = 1 if not inputs["list_run"] else len(inputs["list_run"])
    n_bar = len(basins)* n_run
    print(f"\n *** Runs concerned by {len(basins)} basins and {n_run} cycles *** ")

    with tqdm(total=n_bar) as p_bar:
        for basin in basins:
            inputs["basin"] = basin
            if inputs["list_run"]:
                list_cfg = []
                for id_run_ in inputs["list_run"]:
                    temp_inp = inputs.copy()
                    temp_inp['id_run'] = id_run_
                    temp_inp.update({"discr_model": f"{basin}_{id_run_}"})
                    list_cfg.append(temp_inp)
                    del temp_inp
            else:
                list_cfg = [inputs]
            for inputs_ in list_cfg:
                try:
                    run_parallel(run, inputs_)
                    p_bar.update(1)
                except Exception as e:
                    print(f"{e}. See {e.__traceback__.tb_frame}")
                    continue

    # path_to = (f"../CLIMATOLOGY/sacsma" if inputs["path_to"] is None else inputs["path_to"]) + f"/hp{inputs['hp']}"
    # print(f"Results saved as {path_to}/*.csv")
    print("Done!")
    return


if __name__ == '__main__':
    # run_parallel()
    # run_parallel(run, get_run_args())
    launch_all_basins()
    # print("Done !")
