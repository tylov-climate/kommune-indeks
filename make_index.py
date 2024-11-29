#!/usr/bin/env python
# make_kindex.py
# Developed by Tyge Løvset, Nov 2023

import os
import sys
import glob
import datetime as dt
from dateutil.relativedelta import relativedelta
import netCDF4 as nc4
import uuid
import shutil
import argparse

# hist => 2005
# rcp4.5 start 2006

indexmap = {
    'cdd': 'TM',
    'hdd': 'TM',
    'dzc': 'TN', # needs 'TX' as well
    'fd': 'TN',
    'su': 'TX',
    'tas': 'TM',
    'tasx': 'TX',
    'tasn': 'TN',
    'pr': 'RR',
    'pr1mm': 'RR',
    'pr20mm': 'RR',
    'pr95p': 'RR',
    'prx5day': 'RR',
}


def parse_args():
    parser = argparse.ArgumentParser()
    print('make_kindex.py - make climate indexes for KSS municipalities data')
    print('')

    parser.add_argument(
        '-i', '--index', required=True,
        help='Climate index (all, ' + ', '.join([k for k in indexmap.keys()]) + ')'
    )
    parser.add_argument(
        '-k', '--kommune', default='pilots',
        help='Select kommune (pilots=default, ...)'
    )
    parser.add_argument(
        '-s', '--scenario', default='all',
        help='Select scenario (all=default, hist, rcp45, rcp85)'
    )
    parser.add_argument(
        '-m', '--model', default='CNRM_RCA',
        help='Select model (CNRM_RCA=default, ...)'
    )
    parser.add_argument(
        '-y', '--years', default='*',
        help="Select year range ('*'=default)"
    )
    parser.add_argument(
        '--indir', default='kin_kommuner',
        help='Input file directory (kin_kommuner=default)'
    )
    parser.add_argument(
        '--outdir', default='kin_index',
        help='Output file directory (kin_index=default)'
    )
    return parser.parse_args()



def idx_cdd(var, tm_inputs, output, tc):
    ''' annual cooling degree days '''
    # No CDO built-in cdd operator; compute self
    tk = tc + 273.15
    cmd = f"cdo -yearsum -mergetime -apply,-expr,cooling_degree_days_per_time_period='(({var}>={tk})*({var}-{tk}))' [ {tm_inputs} ] {output}"
    ret = os.system(cmd)
    cmd = f"ncatted -a long_name,cooling_degree_days_per_time_period,o,c,'Mean annual cooling degree-days (tas >= {tc}°C)' {output}"
    ret = os.system(cmd)


def idx_hdd(var, tm_inputs, output, tc):
    ''' annual heating degree days '''
    # Use CDO built-in hdd operator. Creates "heating_degree_days_per_time_period" index.
    cmd = f"cdo -mergetime -apply,eca_hd,{tc} [ {tm_inputs} ] {output}"
    #tk = tc + 273.15
    #cmd = f"cdo -yearsum -mergetime -apply,-expr,heating_degree_days_per_time_period='(({var}<={tk})*({tk}-{var}))' [ {inputs} ] {output}"
    #ret = os.system(cmd)
    #cmd = f"ncatted -a long_name,heating_degree_days_per_time_period,o,c,'Mean annual heating degree-days (tas <= {tc}°C)' {output}"
    ret = os.system(cmd)


def idx_dzc(var, tn_inputs, output):
    ''' annual days with zero-crossings '''
    if os.path.exists(output):
        os.remove(output)
    for tn in sorted(glob.glob(tn_inputs)):
        tx = tn.replace('_TN_', '_TX_')
        cmd = f"cdo -cat -yearsum [ -expr,days_with_zero_crossings='((TN<=273.15)&&(TX>273.15))' -merge [ {tn} {tx} ] ] {output}"
        ret = os.system(cmd)


def idx_fd(var, tn_inputs, output):
    ''' annual frost days '''
    cmd = f"cdo -mergetime -apply,eca_fd [ {tn_inputs} ] {output}"
    ret = os.system(cmd)


def idx_su(var, tx_inputs, output, tc):
    ''' annual summerdays (>= 20°C) '''
    cmd = f"cdo -mergetime -apply,eca_su,{tc} [ {tx_inputs} ] {output}"
    ret = os.system(cmd)


def idx_pr(var, rr_inputs, output):
    ''' annual precipitation in mm '''
    cmd = f"cdo -yearsum -mergetime [ {rr_inputs} ] {output}"
    ret = os.system(cmd)


def idx_tas(var, tt_inputs, output):
    ''' annual mean temperature in C '''
    cmd = f"cdo -yearmean -mergetime -apply,expr,{var}='({var}-273.15)' [ {tt_inputs} ] {output}"
    ret = os.system(cmd)
    cmd = f"ncatted -a units,{var},o,c,'celsius' {output}"
    ret = os.system(cmd)


def idx_prmm(var, rr_inputs, output, mm):
    ''' annual days with >= mm precipitation '''
    cmd = f"cdo -mergetime -apply,-eca_rr1,{mm} [ {rr_inputs} ] {output}"
    ret = os.system(cmd)


def idx_prp(var, rr_inputs, output, p):
    ''' annual days with > p percentile precipitation '''
    # precipitation_percent_due_to_R95p days
    if os.path.exists(output):
        os.remove(output)
    cmd = f"cdo  -ydaymin -mergetime {rr_inputs} {output}.min.nc"
    ret = os.system(cmd)
    cmd = f"cdo  -ydaymax -mergetime {rr_inputs} {output}.max.nc"
    ret = os.system(cmd)
    for rr in sorted(glob.glob(rr_inputs)):
        cmd = f"cdo -cat -yearsum -expr,days_with_rr_above_{p}th_percentile='({var}>{p})' -ydaypctl,{p} {rr} {output}.min.nc {output}.max.nc {output}"
        ret = os.system(cmd)
    os.remove(f'{output}.min.nc')
    os.remove(f'{output}.max.nc')


def idx_prx5day(var, rr_inputs, output, mm):
    # Highest 5-day precipitation amount per time period
    if os.path.exists(output):
        os.remove(output)
    for rr in sorted(glob.glob(rr_inputs)):
        os.system(f"cdo -cat -eca_rx5day {rr} {output}")



def make_index(args):
    if args.kommune == 'pilots':
        kommuner = ('Bergen', 'Voss', 'Tromsø') # , 'Vestvågøy', 'Ås', 'Nord-Fron', 'Kristiansand', 'Grimstad')
    else:
        kommuner = (args.kommune,)

    if args.scenario == 'all':
        scenarios = ('hist', 'rcp45', 'rcp85')
    else:
        scenarios = (args.scenario,)

    if args.index == 'all':
        indexes = indexmap.keys()
    else:
        indexes = (args.index,)

    for kname in kommuner:
        for idx in indexes:
            var = indexmap[idx]
            for scen in scenarios:
                inputs = os.path.join(args.indir, kname, '%s_%s_%s_%s_daily_%s_v*.nc' % (kname, scen, args.model, var, args.years))
                outbase = f'{kname}_{idx}_{scen}_{args.model}_{var}.nc'
                outfile = os.path.join(args.outdir, f'{kname}', outbase)
                os.makedirs(os.path.dirname(outfile), exist_ok=True)

                if idx == 'cdd':
                    idx_cdd(var, inputs, outfile, 22)
                elif idx == 'hdd':
                    idx_hdd(var, inputs, outfile, 17)
                elif idx == 'dzc':
                    idx_dzc(var, inputs, outfile)
                elif idx == 'su':
                    idx_su(var, inputs, outfile, 20)
                elif idx == 'fd':
                    idx_fd(var, inputs, outfile)
                elif idx == 'pr':
                    idx_pr(var, inputs, outfile)
                elif idx in ('tas', 'tasn', 'tasx'):
                    idx_tas(var, inputs, outfile)
                elif idx == 'pr1mm':
                    idx_prmm(var, inputs, outfile, 1)
                elif idx == 'pr20mm':
                    idx_prmm(var, inputs, outfile, 20)
                elif idx == 'pr95p': # 75, 90, 95, 99 supported
                    idx_prp(var, inputs, outfile, 95)
                elif idx == 'prx5day':
                    idx_prx5day(var, inputs, outfile, 1)

                print(f'Success: created index "{idx}" from files "{inputs}"')



# main: create various climate indexes

if __name__ == '__main__':
    args = parse_args()
    make_index(args)
