import seaborn as sns
#import numpy as np
#import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import sys
import glob


def detrend_dim(da, dim, deg=1):
    # detrend along a single dimension
    p = da.polyfit(dim=dim, deg=deg)
    fit = xr.polyval(dim, p.polyfit_coefficients)
    return da - fit


if __name__ == "__main__":
    mun='Bergen'
    filter='rcp85'
    if len(sys.argv) > 1: mun=sys.argv[1]
    if len(sys.argv) > 2: filter=sys.argv[2]
    for f in glob.glob(f'./kin_mean/{mun}/*{filter}*.nc'):
        print(f)
        with xr.open_dataset(f) as xarr:
            for var in xarr.data_vars:
                if var == 'time_bnds':
                    continue
                print('   ', var)
                da = xarr[var]
                #print(dd)
                plt.figure(figsize=(19,6))
                da.plot(linestyle='dashed',color='g', linewidth=1, marker='o',markersize=5)

                #lreg = detrend_dim(da, da['time'])
                #lreg = da.polyfit(dim='time', deg=1)
                #print(type(lreg))
                #print(df)
                #sns.regplot(data=df, ci=None)
                #df.plot()
                plt.show()

        #ta_CBR.sel(time=slice('1950-01-01','1950-01-31'), plev=85000).plot(linestyle='dashed',color='g', linewidth=2, marker='o',markersize=10)
    
    # plot using lineplot
    #sns.set(style='darkgrid')
    #sns.lineplot(x='num', y='sqr', data=pdnumsqr)
