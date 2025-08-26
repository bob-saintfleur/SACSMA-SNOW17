from glob import glob
from datetime import timedelta
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


flow_n_forcing_head = fr"basin_timeseries_v1p2_metForcing_obsFlow\basin_dataset_public_v1p2"

def load_all_sacsma_parameters(forcing_type: str = None, data_path:str = None) -> pd.DataFrame:
    """
    Load all sacsma parameters according to runs on a forcing type
    :param forcing_type: specify one of maurer, daymet or nldas
    :return:
    """
    if forcing_type is None: forcing_type = "maurer"
    # output_pathway = fr"basin_timeseries_v1p2_modelOutput_{forcing_type}\model_output_{forcing_type}\model_output\flow_timeseries\{forcing_type}"
    # filenames = glob(f'{data_path}/{output_pathway}/**/*_model_parameters.txt')
    filenames = glob(f'{data_path}/sacsma_output/{forcing_type}/**/*_model_parameters.txt')
    basins = list(set([Path(c).name.split("_")[0] for c in filenames]))
    par_all_bv={}
    for basin in basins:
        files_par = [filename for filename in filenames if basin in filename]
        parameters = {}
        for i, filename in enumerate(files_par):
            temp_df = pd.read_csv(filename, sep="\s+", header=None, index_col=0, names=["val"])
            temp_df.index.name = "params"
            parameters[f"run{i+1}"] = temp_df.values.reshape(-1,)
        par_df = pd.DataFrame().from_dict(parameters, orient="columns")
        par_df.index = temp_df.index
        par_all_bv[basin] = par_df.mean(axis=1)
    par_all_bv = pd.DataFrame().from_dict(par_all_bv, orient="columns")
    return par_all_bv


def load_sacsma_parameters(file_param: str) -> pd.Series:
    """
    Load the parameters for a gauge according to runs on a forcing type, return an aggregated dataframe according to
    pd.aggregate() methods available (mean, median,..)
    :return: required series
    """
    temp_df = pd.read_csv(file_param, sep="\s+", header=None, index_col=0, names=["val"])["val"]
    return temp_df


def load_basin_attributes(gauge_id: str, data_path:str = None):
    """
    Load attributes for a particular gauge
    :param gauge_id: the basin id to get attributes from
    :return:
    """
    # attributes_dir = Path(DATA_DIR) / 'camels_attributes_v2.0'
    attributes_dir = Path(data_path) / 'camels_attributes_v2.0'
    if not attributes_dir.exists():
        raise RuntimeError(f"Attribute folder not found at {attributes_dir}")
    txt_files = attributes_dir.glob('camels_*.txt')
    dfs = []
    for txt_file in txt_files:
        df_temp = pd.read_csv(txt_file, sep=';', header=0, dtype={'gauge_id': str})
        df_temp = df_temp.set_index('gauge_id')
        dfs.append(df_temp)
    df = pd.concat(dfs, axis=1)
    df['huc'] = df['huc_02'].apply(lambda x: str(x).zfill(2))
    df = df.drop('huc_02', axis=1)
    attributes = df.loc[gauge_id]
    return attributes


def load_forcings(gauge_id: str, forcing_type: str = None, forcing_root:str = None, data_path:str = None) -> pd.DataFrame:
    """
    Load forcing for gauge_id according to a forcing type

    :param gauge_id: the gauge id, or the basin id
    :param forcing_type: any of maurer, daymet or nldas
    :param forcing_root: path leading directly to the 2-digit regions

    :return: the forcing dataframe and the area
    """
    if forcing_type is None: forcing_type = "maurer"
    # forcing_pathway = f"{data_path}/{flow_n_forcing_head}/basin_mean_forcing/{forcing_type}"
    forcing_pathway = f"{data_path}/basin_mean_forcing/{forcing_type}"

    if forcing_root is None:
        # forcing_files = glob(f'{data_path}/basin_mean_forcing/{forcing_type}/**/{gauge_id}_*_forcing_leap.txt')
        forcing_files = glob(forcing_pathway + f"/*/{gauge_id}_*_forcing_leap.txt")
    else:
        forcing_files = glob(f'{forcing_root}/**/{gauge_id}_*_forcing_leap.txt')
    # assert len(forcing_files) == 1
    forcing_file = forcing_files[0]
    with open(forcing_file, 'r') as fp:
        content = fp.readlines()
        area = int(content[2])
    forcing = pd.read_csv(forcing_file, sep='\s+', header=3)
    forcing['Date'] = pd.to_datetime(
        forcing['Year'] * 10000 + forcing['Mnth'] * 100 + forcing['Day'], format='%Y%m%d')
    forcing.set_index('Date', inplace=True)
    return forcing, area


def load_discharge(gauge_id: str, forcing_type: str = None, data_path:str = None):
    """
    Load the discharge from the models output file

    :param gauge_id: the gauge id, or the basin id
    :return:
    """
    if forcing_type is None: forcing_type = "maurer"
    # filename = glob(f'{DATA_DIR}/models_output/{forcing_type}/**/{gauge_id}_*_model_output.txt')[0]
    filename = glob(f'{data_path}/sacsma_output/{forcing_type}/**/{gauge_id}_*_model_output.txt')[0]

    # output_pathway = fr"basin_timeseries_v1p2_modelOutput_{forcing_type}\model_output_{forcing_type}\model_output\flow_timeseries\{forcing_type}"
    # filename = glob(f'{data_path}/{output_pathway}/**/{gauge_id}_*_model_output.txt')[0]
    output = pd.read_csv(filename, sep='\s+')
    output['Date'] = pd.to_datetime(output['YR'] * 10000 + output['MNTH'] * 100 + output['DY'], format='%Y%m%d')
    output = output.set_index('Date')
    return output


def load_usgs(gauge_id: str, area: int, data_path:str = None):
    """
    Load the observed discharge data from the usgs streamflow database for a particular gauge_id
    :param gauge_id: the gauge id, or the basin id
    :param area: area of the basin, useful to convert flow from cfs to mm/day
    :return:
    """
    # Grab the correct forcing file
    # filename = glob(f'{DATA_DIR}/basin_dataset_public_v1p2/usgs_streamflow/**/{gauge_id}_streamflow_qc.txt')[0]
    filename = glob(f'{data_path}/usgs_streamflow/**/{gauge_id}_streamflow_qc.txt')[0]

    # flow_pathway = f"{data_path}/{flow_n_forcing_head}/usgs_streamflow"
    # filename = glob(f'{flow_pathway}/**/{gauge_id}_streamflow_qc.txt')[0]
    col_names = ['basin', 'Year', 'Mnth', 'Day', 'QObs', 'flag']
    obs = pd.read_csv(filename, sep='\s+', header=None, names=col_names)

    # unit conversion cfs --> mm/day
    obs.QObs = 28316846.592 * obs.QObs * 86400 / (area * 10 ** 6)
    obs['Date'] = pd.to_datetime(obs.Year.map(str) + "/" + obs.Mnth.map(str) + "/" + obs.Day.map(str))
    obs.set_index('Date', inplace=True, drop=True)
    return obs
