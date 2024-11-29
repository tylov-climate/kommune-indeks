import sys
import re
import os
import glob
import sys

# Bug FIXES to be applied on the original downloaded KSS KIN2100 data.
# 1. Change "scale_factor" variable attribute from 0.1 => 0.01 for TM and RR (TX and TN have correct value: 0.01)
# 2. Change chunk sizes for TN and TX to the same as TM and RR variables. Without it, processing is extremely slow.

model = '*'
if len(sys.argv) > 2:
    model = sys.argv[2]

scen = '*'
if len(sys.argv) > 3:
    scen = sys.argv[3]

ok = False

if len(sys.argv) > 1 and (sys.argv[1] == 'scale' or sys.argv[1] == 'all'):
    ok = True
    for f in sorted(glob.glob(f'kin_norge/{scen}/{model}/TM/*.nc')):
        base = os.path.basename(f)
        # rcp45_CNRM_RCA_TM_daily_2100_v4.nc: air_temperature__map_rcp45_daily
        m = re.match(r'^([a-z0-9]+)_([-_A-Z0-9]+)_TM_daily_[0-9]+.+', base)
        if m:
            cmd = f'ncatted -a scale_factor,air_temperature__map_{m.group(1)}_daily,m,d,0.01 {f}'
            print(cmd)
            os.system(cmd)
        else:
            print('no match', f)

    for f in sorted(glob.glob(f'kin_norge/{scen}/{model}/RR/*.nc')):
        base = os.path.basename(f)
        # rcp45_CNRM_RCA_RR_daily_2100_v4.nc: precipitation__map_rcp45_daily
        m = re.match(r'^([a-z0-9]+)_([-_A-Z0-9]+)_RR_daily_[0-9]+.+', base)
        if m:
            cmd = f'ncatted -a scale_factor,precipitation__map_{m.group(1)}_daily,m,d,0.01 {f}'
            print(cmd)
            os.system(cmd)
        else:
            print('no match', f)


if len(sys.argv) > 1 and (sys.argv[1] == 'rechunk' or sys.argv[1] == 'all'):
    ok = True
    for f in sorted(glob.glob(f'kin_norge/{scen}/{model}/T[NX]/*.nc')):
        cmd = f'nccopy -c time/1,Yc/70,Xc/53 {f} {f}.temp.nc ; mv {f}.temp.nc {f}'
        print('rechunking', f)
        os.system(cmd)

if not ok:
    print('Bug FIXES to be applied on the original downloaded KSS KIN2100 data.')
    print('1. Change "scale_factor" variable attribute from 0.1 => 0.01 for TM and RR (TX and TN have correct value: 0.01)')
    print('2. Change chunk sizes for TN and TX to the same as TM and RR variables. Without it, processing is extremely slow.')
    print()
    print(f'Usage: {os.path.basename(sys.argv[0])} scale|rechunk|all [model [scenario]]')
    print()
