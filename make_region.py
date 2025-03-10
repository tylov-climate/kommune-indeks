#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: tylo, 2023, 2024, 2025 for KSS Norway KIN2100 dataset
"""

import sys
import os
import zipfile
import numpy as np
import glob
import argparse
import re
import json
import pyproj
import xarray
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from shapely import union_all
from shapely.geometry import Point
from shapely.geometry import Polygon


# New 2024 kommune-grense files. Has different structure than the previous.
NORGE_KOMMUNER_SHP = 'Basisdata_0000_Norge_25833_Kommuner_GeoJSON.geojson'
NORGE_FYLKER_SHP = 'Basisdata_0000_Norge_25833_Fylker_GeoJSON.geojson'

varmap = {
    'RR': 'precipitation',
    'SMD': 'soil_moisture_deficit',
    'SWE': 'snow_water_equivalent',
    'TM': 'air_temperature',
    'TN': 'min_air_temperature',
    'TX': 'max_air_temperature',
}

pilotlist = (
    'Bergen',
    'Voss',
    'Tromsø',
    'Vestvågøy',
    'Ås',
    'Nord-Fron',
    'Kristiansand',
    'Grimstad',
)


def parse_args():
    parser = argparse.ArgumentParser()
    print('Crop and mask Norway KSS climate data into municipality or county')
    print('')

    parser.add_argument(
        '-k', '--kommune', default=None,
        help='Select kommune (all, pilots, ...)'
    )
    parser.add_argument(
        '-f', '--fylke', default=None,
        help='Select fylke (all, ...)'
    )
    parser.add_argument(
        '-w', '--write', action='store_true',
        help='Write the cropped+masked output to file instead of plotting'
    )
    parser.add_argument(
        '-s', '--scenario', default='hist_rcp85',
        help='Select scenario (all, hist_rcp85=default, hist, rcp45, rcp85)'
    )
    parser.add_argument(
        '-m', '--model', default='CNRM_RCA',
        help='Select model (CNRM_RCA=default)'
    )
    parser.add_argument(
        '-v', '--variable', default='precip_temp',
        help='Select variable (all, precip_temp=default, ' +  ', '.join([k for k in varmap.keys()]) + ')'
    )
    parser.add_argument(
        '--indir', default='kin_norge',
        help='Input file directory (kin_norge=default)'
    )
    parser.add_argument(
        '--outdir', default=None,
        help='Output file directory (kin_kommuner=default)'
    )
    parser.add_argument(
        '-y', '--year', default=None,
        help='Select year(s) (may contain wildcards)'
    )
    parser.add_argument(
        '-d', '--day', default='0',
        help='Plot a specific year-day number (0=default)'
    )
    return parser.parse_args()



def read_shapefile(shapefile):
    indexmap = {}

    #with open(shapefile) as f:
    #    shp = json.load(f)
    with zipfile.ZipFile(shapefile.replace('.geojson', '.zip'), 'r') as f:
        shp = json.loads(f.read(shapefile).decode('utf-8'))
    print('shapefile loaded')

    # Old shapefile format:
    #feat = shp['administrative_enheter.kommune']['features']
    #for regidx in range(len(feat)):
    #    name = feat[regidx]['properties']['navn'][0]['navn']
    try:
        feat = shp['Kommune']['features']
        regkey = 'kommunenavn'
    except:
        feat = shp['Fylke']['features']
        regkey = 'fylkesnavn'

    for regidx in range(len(feat)):
        name = feat[regidx]['properties'][regkey].replace(' ', '-')
        indexmap[name] = regidx

    print(regkey, ':', len(indexmap))
    return shp, indexmap



class Grid:
    def __init__(self, datasetname):
        with xarray.open_dataset(datasetname) as ds:
            print('filename:', datasetname)
            # rcp45_CNRM_RCA_RR_daily_2100_v4.nc: precipitation__map_rcp45_daily
            m = re.match(r'^([a-z0-9]+)[-_A-Z0-9]+_([A-Z]+)_([a-z]+).+', os.path.basename(datasetname))
            varname = '%s__map_%s_%s' % (varmap[m.group(2)], m.group(1), m.group(3))
            ds = ds.rename({varname: m.group(2)})
            self.varname = m.group(2)
            self.datasetname = datasetname

            self.ds = ds
            self.extent = (ds.attrs['geospatial_lon_min'], ds.attrs['geospatial_lon_max'], 
                           ds.attrs['geospatial_lat_min'], ds.attrs['geospatial_lat_max'])
            self.dim = (ds.sizes['Xc'],  ds.sizes['Yc'])
            self.steps = ds.sizes['time']
            #print('variable:', self.varname, 'shape:', ds[self.varname].shape)
            #self.box_utm = ((ds.Xc.values[0], ds.Yc.values[-1]), (ds.Xc.values[-1], ds.Yc.values[0]))
            #print('grid.extent', self.extent)



class Region:
    def __init__(self, name, shp, indexmap, grid):
        self.name = name
        self.type = 'Kommune' if 'Kommune' in shp else 'Fylke'
        self.extent = None
        self.regidx = None
        self.polys = []
        self.bounds = None
        self.mask = None

        if name in indexmap:
            self.regidx = indexmap[name]
        else:
            print(f'Feil: {name} er ukjent')
            exit(-1)

        print(name)
        #coords = shp['administrative_enheter.kommune']['features'][i]['geometry']['coordinates']
        #myProj = pyproj.Proj(shp['administrative_enheter.kommune']['crs']['properties']['name'])  #"EPSG:25833"
        
        coords = shp[self.type]['features'][self.regidx]['geometry']['coordinates'][0]
        #print(f'adding 1 of {len(coords)} polygon(s)')
        polygon = coords[0]
        x_utm, y_utm = np.array(polygon).transpose()

        myProj = pyproj.Proj(shp[self.type]['crs']['properties']['name'])  #"EPSG:25833"
        st_lon, st_lat = myProj(x_utm, y_utm, inverse=True)
        poly = Polygon(zip(st_lon, st_lat))
        self.polys.append( poly )

        bx, by = 0.02, 0.01
        self.extent = (poly.bounds[0]-bx, poly.bounds[2]+bx, poly.bounds[1]-by, poly.bounds[3]+by)

        poly_utm = Polygon(zip(x_utm, y_utm))
        self.bounds = poly_utm.bounds
        #print('   .extent', self.extent)
        #print('    bnd', poly_utm.bounds)

        # Crop the initial dataset to use Xc and Yc
        cropped = grid.ds.sel(Xc=slice(self.bounds[0], self.bounds[2]),
                              Yc=slice(self.bounds[3], self.bounds[1])) #, drop=True)
        # Create the region-mask
        self.mask = mask_area(poly_utm, cropped.Xc, cropped.Yc)
        print('cropped cover', np.count_nonzero(self.mask == True), 'out of', self.mask.shape[0]*self.mask.shape[1])
        print('cropped shape', cropped[grid.varname].shape)
        self.plot_mask()


    def crop(self, ds, varname):
        ''' crop the grid '''
        cropped = ds.sel(Xc=slice(self.bounds[0], self.bounds[2]),
                         Yc=slice(self.bounds[3], self.bounds[1])) #, drop=True)
        # Apply the region-mask
        cropped[varname] = cropped[varname].where(self.mask == True)
        return cropped


    def plot_mask(self):
        ''' Print and plot the mask '''
        y, x = np.argwhere(self.mask == 1).T
        plt.scatter(x, -y)


    def plot(self, ds, varname, label):
        ''' plot kommune '''
        minmax = [0, 350]
        proj = ccrs.EuroPP() # ccrs.PlateCarree()
        
        #stamen_terrain = cimgt.Stamen('terrain-background')
        #proj = stamen_terrain.crs
        fig = plt.figure(figsize=(10, 8))
        
        ax = fig.add_subplot(1, 1, 1, projection=proj)
        ax.set_title(self.name)
        print('days?', len(ds[varname].values))
        if varname in ('TM', 'TN', 'TX'):
            values = ds[varname].values[int(args.day)] - 273.15
        else:
            values = ds[varname].values[int(args.day)]
        
        d = ax.pcolormesh(ds.lon.values, ds.lat.values, values,
                          #vmin=minmax[0], vmax=minmax[1],
                          cmap='YlGnBu', transform=ccrs.PlateCarree(), zorder=11)
        #ax.set_extent(self.extent, crs=ccrs.PlateCarree())
        ax.add_geometries(self.polys, crs=ccrs.PlateCarree(), facecolor='b', edgecolor='red', alpha=0.2, zorder=10)

        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=.5, color='k', alpha=0.5, linestyle='-')
        gl.top_labels = False
        gl.right_labels = False
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        plt.colorbar(d, orientation='vertical', label=label + f', day {args.day}', aspect=40, pad = .1)
        plt.ioff()
        plt.show()


    def save(self, ds, varname, datasetname):
        folder = f'kin_kommuner/{name}'
        os.makedirs(folder, exist_ok=True)
        fname = f'{folder}/{name}_{os.path.basename(datasetname)}'
        print('saving', fname)
        ds.to_netcdf(path=fname, encoding={varname: {'zlib': True, 'complevel': 2}})

        #var_data = ds[varname].sum(dim='time')
        #return var_data


def mask_area(poly, Xc, Yc):
    msk = np.array([Point(x, y).intersects(poly) for y in Yc for x in Xc], dtype=bool)
    mask = msk.reshape((len(Yc), len(Xc)))
    return mask
 

if __name__ == "__main__":
    args = parse_args()
        
    # read the geojson shape file inside zip file
    if args.kommune:
        shapefile = NORGE_KOMMUNER_SHP
        if args.outdir is None: 
            args.outdir = 'kin_kommune'
    else:
        shapefile = NORGE_FYLKER_SHP
        if args.outdir is None: 
            args.outdir = 'kin_fylker'
        
    shp, region_indexmap = read_shapefile(shapefile)
    
    if args.kommune is None and args.fylke is None:
        print("Error: No kommune or fylke given, --help for usage")
        exit()
    elif args.kommune == 'all' or args.fylke == 'all':
        regions = region_indexmap.keys()
    elif args.kommune == 'pilots':
        regions = pilotlist
    elif args.kommune:
        regions = (args.kommune,)
    else:
        regions = (args.fylke,)

    if args.scenario == 'hist_rcp85':
        scenarios = ('hist', 'rcp85')
    elif args.scenario == 'all':
        scenarios = ('hist', 'rcp45', 'rcp85')
    else:
        scenarios = (args.scenario,)

    if args.model == 'all':
        exit()
    else:
        models = (args.model,)

    if args.variable == 'precip_temp':
        variables = ('RR', 'TM', 'TN', 'TX')
    elif args.variable == 'all':
        variables = varmap.keys()
    else:
        variables = (args.variable,)

    regionmap = {}

    for scenario in scenarios:
        for model in models:
            for var in variables:
                fmt = f'{args.indir}/{scenario}/{model}/{var}/{scenario}_{model}_{var}_daily'
                files = []
                if args.year:
                    files += sorted(glob.glob(fmt + f'_{args.year}_*'))
                else:
                    for decade in range(197, 210):
                        files += sorted(glob.glob(fmt + f'_{decade}*'))
                    files += glob.glob(fmt + '_2100*')

                for f in files:
                    grid = Grid(f)
                    for name in regions:
                        if name in regionmap:
                            region = regionmap[name]
                        else:
                            region = Region(name, shp, region_indexmap, grid)
                            regionmap[name] = region
                        
                        cropped = region.crop(grid.ds, grid.varname)
                        if args.write:
                            region.save(cropped, grid.varname, f)
                        else:
                            region.plot(cropped, grid.varname, os.path.basename(f))
