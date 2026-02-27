from typing import Dict
from tqdm import tqdm
import pandas as pd
from datetime import datetime, timedelta

RENAME_C = {"P_CM":'PRCP(mm/day)', "RAD_CM":'SRAD(W/m2)', "SWI_CM_swe":'SWE(mm)', "T_CM_max":'Tmax(C)',
               "T_CM_min":'Tmin(C)', "VP_CM":'Vp(Pa)', "ETP_CM":'PET(mm/day)'}

def get_pred_range_date(ref_date: str, hp_: int) -> pd.DatetimeIndex:
    """
    Get the forecasting date for a given reference date and hp lead time. the reference date will not be included
    :param ref_date: the reference date with the format "yyyymmdd"
    :param hp_: integer standing for the lead time
    :return: pd.DatetimeIndex
    """
    start_date = datetime.strptime(ref_date, "%Y%m%d")
    end_date = start_date + timedelta(days=hp_)
    range_ = pd.date_range(start_date, end_date, inclusive="right")
    for i, dt in enumerate(range_):
        if (dt.month == 2) & (dt.day == 29):
            range_ = range_.delete([i])
            range_ = range_.union([end_date + timedelta(days=1)])
    return range_


def get_hist_range_date(ref_date: str, look_back: int = 365) -> pd.DatetimeIndex:
    """
    Get the historical datetime index for a given reference date and look back period.
    :param ref_date: reference date with the format "yyyymmdd" for the now time
    :param look_back: limit in the past to include
    :return: pd.DatetimeIndex
    """
    start_ = datetime.strptime(ref_date, "%Y%m%d")
    range_ = pd.date_range(start_, periods=look_back, freq="-1D")
    range_ = range_.sort_values()
    return range_


def make_list_ref_date(period: tuple[str, str], exclude_feb29: bool = True) -> list:
    """
    Get the list of reference dates for a given period. The dates will inherit the yyyymmdd format. Feb29 may be dropped
    :param period: period with start and end dates
    :param exclude_feb29: indicate if feb29 should be excluded
    :return: list of string date
    """
    range_ = pd.date_range(period[0], period[1], freq="D", inclusive="both")
    if exclude_feb29 is True:
        range_ = [f"{str(a.year)}{str(a.month).zfill(2)}{str(a.day).zfill(2)}" for a in range_
                  if f"{a.month}-{a.day}" != "2-29"]
    else:
        range_ = [f"{str(a.year)}{str(a.month).zfill(2)}{str(a.day).zfill(2)}" for a in range_]
    return range_


def get_hist_data(data: pd.DataFrame, now_date: str, look_back: int = 365) -> pd.DataFrame:
    """ Get the historical data using a ref date and a sequence size"""
    hist_date = get_hist_range_date(now_date, look_back)
    return data.loc[hist_date]


def get_pred_list(data: pd.DataFrame, ref_date: str, hp_: int, list_year: list = None) -> Dict:
    """
    Get list of predictions members

    :param data: dataframe wher climatology members are from
    :param ref_date: the actual data to be considered (liske t0)
    :param hp_: the lead time
    :param list_year: list of year to consider
    :return: dict of (ref_date: sub_data)
    """
    month, day = pd.to_datetime(ref_date, yearfirst=True).month, pd.to_datetime(ref_date, yearfirst=True).day
    chck_yr = list(set(list(data.index.year)))[1:]
    if list_year is not None:
        chck_yr = [a for a in list_year if a in chck_yr]
    chck_yr.sort()
    upper_ = get_pred_range_date(f"{chck_yr[-1]}{month}{day}", hp_)
    if upper_[-1] not in data.index:
        chck_yr = chck_yr[:-1]
    member_ = {}
    for yr_ in chck_yr:
        ref_ = f"{yr_}{str(month).zfill(2)}{str(day).zfill(2)}"
        pred_date = get_pred_range_date(ref_, hp_)
        member_[f"yr_{yr_}"] = data.loc[pred_date].copy()
    return member_


def get_hindcast_members(hindcast_path, basin:str, period, hp:int):
    hcst = pd.read_csv(str(hindcast_path)+f"/{basin}.csv", sep=";", index_col=["member", "time", "step", "Date"],
                       parse_dates=["time", "Date"])
    hcst = hcst.rename(columns=RENAME_C)
    try:
        period_ = pd.date_range(*period, freq="D")
    except:
        period_ = period
    period_ = hcst.index.get_level_values("time").intersection(period_)
    steps = hcst.index.get_level_values("step").unique()[:hp]
    by_date = {}
    for dte in tqdm(period_, leave=False):
        sub_ = hcst.xs(dte, level="time")
        sub_ = sub_[sub_.index.get_level_values("step").isin(steps)].droplevel("step")
        by_date[dte.strftime("%Y%m%d")] = {f"yr_{m}":a.droplevel("member") for m,a in sub_.groupby("member")}
    return by_date
