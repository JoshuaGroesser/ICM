import xarray as xr
import glob
import core as c
import os
import argparse
from dask.distributed import Client
import time

def main(year, client):
    path="/home/yannickh00/LEHRE/msc-intro-comp-met-ex-w2024/data/era5/"
    wdir = "/home/yannickh00/ICM/Europe_Task/"
    all_files = glob.glob(path+"*")
    all_files = [f for f in all_files if f"{year}" in f]
    print(f"Importing {len(all_files)} files")
    ds=xr.open_mfdataset(all_files,
                         engine="netcdf4",
                         chunks={"valid_time":1e5} )

    # Drop all data which is outside of europe
    ds = c.clip_to_europe(ds, wdir + "europe_10km.shx")
    # calculate the windspeed
    ds["wspd"] = c.calc_windspeed(ds)
    # compute an xarray with the monthly mean of pvpot
    pvpot = c.calc_pv_pot(ds).groupby(ds.valid_time.dt.month).mean("valid_time").compute()
    # Write results for easier analysis later
    if not os.path.exists(wdir + "Results"): # check if the directory exists
        os.makedirs(wdir + "Results") 
    pvpot.to_netcdf(wdir + f"/Results/pvpot_{year}.nc") # save as .nc file
    client.shutdown()
    return pvpot

if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=str, help="year to compute the mean for")
    args = parser.parse_args()
    
    # Create a client
    client = Client(n_workers=20, threads_per_worker=5, local_directory='~/tmp')

    # Call the main function with the provided path
    mean_data = main(args.year, client)
    end = time.time()
    print(f"Program took {end-start:.4f} seconds")
