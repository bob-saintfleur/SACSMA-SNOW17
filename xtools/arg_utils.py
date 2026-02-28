#!/bin/env python3

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from xtools.selectbv import select_bv_by_class


def subdiv_date(period, n_sub=1):
    dd_ = pd.date_range(start=pd.to_datetime(period[0], format="%Y%m%d"), end=pd.to_datetime(period[1],format="%Y%m%d"),
                        freq="D")
    n_sub = min(n_sub, dd_.shape[0]//2)
    by_sub = dd_[::len(dd_)//n_sub]
    dd_f = [(by_sub[i - 1], by_sub[i] + timedelta(days=-1)) for i in range(1, len(by_sub))]
    if by_sub[-1] != dd_f[-1]:
        dd_f = dd_f + [(by_sub[-1], dd_[-1])]
    dd_f = [(c[0].strftime("%Y%m%d"), c[1].strftime("%Y%m%d")) for c in dd_f]
    return dd_f


def tupling_arg(arg):
    try:
        # Parse the input string as a tuple
        return tuple(map(int, arg.split(',')))
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid tuple format: {arg}")


class StoreDictKeyPair(argparse.Action):
    """ Adapt command inputs to dict[key: value] format"""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for kv in values:
            k, v = kv.split("=")
            try:
                getattr(namespace, self.dest)[k] = int(v)
            except (TypeError, ValueError):
                getattr(namespace,
                        self.dest)[k] = False if v.lower() == "false" else (True if v.lower() == "true" else v)


class StoreGridDictKeyPair(argparse.Action):
    """ Adapt command inputs to dict[key: list] format"""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for kv in values:
            k, v = kv.split("=")
            try:
                getattr(namespace, self.dest)[k] = [int(i) for i in v.split(",")]
            except (TypeError, ValueError):
                getattr(namespace, self.dest)[k] = \
                    [False if x.lower() == "false" else (True if x.lower() == "true" else x) for x in v.split(",")]


def get_run_args():
    """Parse input arguments

        Returns
        -------
        dict
            Dictionary containing the run config.
        """
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_to', type=str, help="Path to save outputs")
    parser.add_argument('--run_mode', choices=["climatology", "hindcast"], help="Path to save outputs")
    parser.add_argument('--data_path', type=str, help="Data folder path. Subfolders of "
                                                      "basin_mean_forcing/, usgs_streamflow/, model_output/, etc. "
                                                      "and related files are expected INN ")
    parser.add_argument('--period', type=tupling_arg, help="Period to run climatology", metavar="yyyymmdd,yyyymmdd")
    parser.add_argument('--n_sub', type=int, default=1, help="Split the period into n_sub parts")
    parser.add_argument('--hp', type=int, default=1, help="forecasting lead time")
    parser.add_argument('--id_run', type=str, default="05", help="seed run")
    parser.add_argument('--list_run', nargs="*", help="List of pre-run seeds", metavar='05 11 .. ')
    parser.add_argument('--forcing_src', type=str, default="maurer", help="The forcing source")
    parser.add_argument('--basin_list', nargs="*", help="list of basins to run on with space-separated")
    parser.add_argument('--basins_file', type=str, help="File for list of basins to run")
    parser.add_argument('--discr_model', type=str, help="A string to filter the model to use")
    parser.add_argument('--start_bv', type=int, default=0, help="Start number bv")
    parser.add_argument('--sample_basins', type=int, help="Basins subset, like in Kratzert et al. 2019")
    args = parser.parse_args()

    sub_dates = [args.period]
    if args.basins_file is not None:
        l_bv = [a.split()[0] for a in open(args.basins_file).readlines()]
        l_bv.sort()
        args.basin_list = l_bv[args.start_bv:]
    elif args.sample_basins:
        args.basin_list = select_bv_by_class(size=args.sample_basins)
    args_ = vars(args)
    if args_["n_sub"] > 1:
        sub_dates = subdiv_date(args_["period"], args_["n_sub"])
    args_["sub_dates"] = sub_dates

    if not args_["list_run"]:
        args_["list_run"] = ["05", "11", "27", "48", "59", "66", "72", "80", "94", "33"]
    return args_

