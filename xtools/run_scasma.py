import glob
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tqdm import tqdm
from xtools.selectbv import select_bv_by_class

# import model.camels_utilities as camels
import model.camels_utils_uge as camels
from model.sacsma_utils_uge import run_sacsma
from model.forecast_utils import get_hist_data, get_pred_list, make_list_ref_date, get_pred_range_date


period_data = ("19890101", "20080830")  # the full period to be considered, rather linked to benchmarking the study
date_T = pd.date_range(period_data[0], period_data[1], freq='D')


def run_bv_hp_period(forcing_src, basin_, hp_, id_run, period_, data_path):
    """
    Apply the parameter of a model to a data sampled from the past records (climatology ensemble mode)

    :param forcing_src: which forcing source, maurer or else
    :param basin_: the basin to be considered
    :param hp_: the target lead time
    :param id_run: the ID of the run (refer to the random initialization)
    :param period_: the considered period (date_start, date_end). NB, the process is repeated for every single day in
    :param data_path: the path where data is stored
    :return: The prediction and a descriptive string as its name
    """
    forcings, area = camels.load_forcings(gauge_id=basin_, forcing_type=forcing_src,data_path=data_path)
    forcings = forcings.loc[date_T]
    model_pre_run = f"{data_path}/sacsma_output"
    param_x = glob.glob(rf"{model_pre_run}/{forcing_src}/*/{basin_}*{id_run}*_model_parameters.txt")[0]
    soil_file = glob.glob(f"{model_pre_run}/{forcing_src}/*/*{basin_}*{id_run}*_soil_state_output*")[0]
    # forcing_type = forcing_src
    # model_pre_run = fr"{data_path}/basin_timeseries_v1p2_modelOutput_{forcing_type}\model_output_{forcing_type}\model_output\flow_timeseries\{forcing_type}"
    #
    # param_x = glob.glob(rf"{model_pre_run}/*/{basin_}*{id_run}*_model_parameters.txt")[0]
    # soil_file = glob.glob(f"{model_pre_run}/*/*{basin_}*{id_run}*_soil_state_output*")[0]

    parameters = camels.load_sacsma_parameters(param_x)
    attributes = camels.load_basin_attributes(basin_, data_path=data_path)
    list_ref_date = make_list_ref_date(period_)
    list_pred=[]
    for ref_ in list_ref_date:
        yref=ref_[:4]
        list_member = get_pred_list(forcings, ref_date=ref_, hp_=hp_)
        pred_ind = get_pred_range_date(ref_date=ref_, hp_=hp_)
        hist_ = get_hist_data(forcings, ref_)
        pred_i = {}
        for i, (key, member) in enumerate(list_member.items()):
            member.index = pred_ind
            k_name = f"yr"+f"{i+1}".zfill(2) if not key.endswith(yref) else "yref"
            forcings_ = pd.concat([hist_, member], axis=0)
            sac_fluxes, sac_states = run_sacsma(forcings=forcings_,
                                                parameters=parameters,
                                                soil_file=soil_file,
                                                latitude=attributes['gauge_lat'],
                                                elevation=attributes['elev_mean'])
            pred_i[k_name] = sac_fluxes.loc[forcings_.index[-1], "sacsma_uh_qq"]
        temp_pred = pd.DataFrame().from_dict(pred_i, orient="index").T
        temp_pred.index = [pred_ind[-1]]
        list_pred.append(temp_pred)
        del temp_pred
    pred_f = pd.concat(list_pred, axis=0)
    pred_f.index.name = "Date"
    return pred_f, f"{basin_}_{id_run}_hp{hp_}"


def run(arg_run):
    out = run_bv_hp_period(forcing_src=arg_run["forcing_src"],
                           basin_=arg_run["basin"],
                           hp_=arg_run["hp"],
                           id_run=arg_run["id_run"],
                           period_=arg_run["period"],
                           data_path=arg_run["data_path"])
    return out


if __name__ == '__main__':
    print("Hello SAC-SMA")
