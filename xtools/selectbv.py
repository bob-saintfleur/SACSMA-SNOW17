import pickle
import pandas as pd
import numpy as np
from typing import Any

with open("all_metrics.p", "rb") as fp:
    metr_lstm = pickle.load(fp)
lstm_nse = metr_lstm["NSE"]["lstm_NSE"]
ser_mod_ = pd.DataFrame().from_dict(lstm_nse, orient="columns")["ensemble"]


def select_bv_by_class(ser_mod: pd.Series = ser_mod_, size: int = 10, how: Any = "last"):
    """
    Select a sub-sample of basin using the pandas.cut() method to make classes. One basin is selected on each class
    by specifying whether it must be the last, the first or a randomly chosen.

    :param ser_mod: Series holding the features to selected, preferred as key indexed object
    :param size: how many classes to have (equivalent to number of desired basins)
    :param how: either of first (leftmost), last (rightmost), or randomly
    :return: list of selected basins
    """
    df_mod = ser_mod.to_frame()
    df_mod.index.name = "index"
    df_mod["rank"] = df_mod.rank(ascending=False, axis=0, method="first").astype(int)
    df_mod["class_rank"] = pd.cut(df_mod["rank"].values, bins=size, precision=0)
    grp = df_mod.reset_index().sort_values(by=ser_mod.name)[["index", "class_rank"]].groupby("class_rank")
    grp.index = range(1, size + 1)
    selected = list(grp.agg(how).values[:, 0])
    return selected


def read_list_of_basins(path_or_list: str or list = None):
    """Read the list of the 531 basins used like in this study"""
    if path_or_list is None: path_or_list = "camels/camels_basin_id_list.txt"
    if isinstance(path_or_list, str):
        with open(path_or_list, "r") as list_bv:
            bs_l = list_bv.readlines()
        basins = [c.split()[0] for c in bs_l]
    elif isinstance(path_or_list, list):
        basins = path_or_list
    else:
        raise AttributeError
    return basins