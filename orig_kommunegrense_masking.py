#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 15:41:43 2021
 
@author: mpo100
"""
 
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import xarray as xr
import json
from pyproj import Proj
from shapely.ops import cascaded_union
from shapely.geometry import Point
from shapely.geometry import Polygon
 
with open('/Users/mapo/Library/CloudStorage/OneDrive-NORCE/Python/Basisdata_0000_Norge_25833_Kommuner_GeoJSON.geojson') as f:
    shp = json.load(f)
# for ii in range(len(shp['administrative_enheter.kommune']['features'])):
#     if shp['administrative_enheter.kommune']['features'][ii]['properties']['navn'][0]['navn']=='Sunnfjord':
#         print('Sunnfjord %s' %ii)
#     elif shp['administrative_enheter.kommune']['features'][ii]['properties']['navn'][0]['navn']=='Kinn':
#         print('Kinn %s' %ii)
#     elif shp['administrative_enheter.kommune']['features'][ii]['properties']['navn'][0]['navn']=='Osteroy':
#         print('Osteroy %s' %ii)
#     elif shp['administrative_enheter.kommune']['features'][ii]['properties']['navn'][0]['navn']=='Osterøy':
#         print('Osterøy %s' %ii)
# Osterøy 42
# Kinn 95
# Sunnfjord 181
# Kinn 249
 
 
wrf_geo = xr.open_dataset('/Users/mapo/Library/CloudStorage/OneDrive-NORCE/Projects/Medvirkningsmetoder/WRF/geo_em.d01.nc')
wrf_data = xr.open_dataset('/Users/mapo/Library/CloudStorage/OneDrive-NORCE/Projects/Medvirkningsmetoder/WRF/precip_2km.nc')
wrf_data['precip'] = wrf_data.PREC_ACC_NC + wrf_data.PREC_ACC_C
wrf_data = wrf_data.rename({'south_north':'lat','west_east':'lon','XTIME':'time'})
wrf_data.coords['lat'] = wrf_data.XLAT[:,150].values
wrf_data.coords['lon'] = wrf_data.XLONG[150,:].values
#
#%%
def inpolygon(polygon, xp, yp):
    return np.array([Point(x,y).intersects(polygon) for x, y in zip(xp, yp)],
                    dtype=np.bool)
 
def mask_area(poly,lat,lon):
   boundary = cascaded_union(poly)
   msk = inpolygon(boundary, lon.ravel(), lat.ravel())
   mask = msk.reshape(lon.shape)
   return mask
 
#%%
minmax=[0,350]
 
# Osterøy 42
# Kinn 95
# Sunnfjord 181
# Kinn 249
kommune = 'Osterøy'# 'Kinn' #'Osterøy'# 'Sunnfjord'
if kommune=='Sunnfjord':
    ii = 181
    box = [4.5,7, 62,61]
elif kommune == 'Osterøy':
    ii = 42
    box = [4.9,6.0, 60.8,60.3]   
elif kommune == 'Kinn':
    ii = 95
    box = [3.8,6.5, 62.5,61.0]   
    x1_lon = np.zeros(len(shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0]))
    y1_lat = np.zeros(len(shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0]))
    for ip in range(len(shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0])):
        x1_lon[ip] = shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0][ip][0]
        y1_lat[ip] = shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0][ip][1]
    myProj = Proj(shp['administrative_enheter.kommune']['crs']['properties']['name'])  #"EPSG:25833"
    st_lon, st_lat = myProj(x1_lon, y1_lat, inverse=True)
    poly2 = Polygon(zip(st_lon,st_lat))
    ii = 249
   
    
x1_lon = np.zeros(len(shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0]))
y1_lat = np.zeros(len(shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0]))
for ip in range(len(shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0])):
    x1_lon[ip] = shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0][ip][0]
    y1_lat[ip] = shp['administrative_enheter.kommune']['features'][ii]['geometry']['coordinates'][0][ip][1]
myProj = Proj(shp['administrative_enheter.kommune']['crs']['properties']['name'])  #"EPSG:25833"
st_lon, st_lat = myProj(x1_lon, y1_lat, inverse=True)
poly = Polygon(zip(st_lon,st_lat))
 
mask_wrf = np.empty(wrf_data.precip.shape,dtype=bool)
msk = mask_area(poly,wrf_data.XLAT.values,wrf_data.XLONG.values)
for t in range(np.size(wrf_data.precip,0)):
    mask_wrf[t,:,:] = msk
 
plotwrf = wrf_data.precip.sum(dim='time').where(mask_wrf[-1,:,:]==1)
 
 
proj = ccrs.EuroPP()# ccrs.PlateCarree()
stamen_terrain = cimgt.Stamen('terrain-background')
proj = stamen_terrain.crs
fig = plt.figure(figsize=(10,8))
 
ax = fig.add_subplot(1,1,1, projection=proj)
ax.set_title('NetAtmo stasjoner')
d = ax.pcolormesh(wrf_geo.XLONG_C[0,:-1,:-1].values,wrf_geo.XLAT_C[0,:-1,:-1].values,plotwrf,
              vmin = minmax[0],vmax = minmax[1],cmap='YlGnBu',transform=ccrs.PlateCarree(), zorder=11)
ax.set_extent(box, crs=ccrs.PlateCarree())
#ax.add_image(stamen_terrain, 8)
ax.add_geometries([poly], crs=ccrs.PlateCarree(), facecolor='b', edgecolor='red', alpha=0.2,zorder=10)
if kommune=='Kinn':
    ax.add_geometries([poly2], crs=ccrs.PlateCarree(), facecolor='b', edgecolor='red', alpha=0.2,zorder=10)  
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,linewidth=.5, color='k', alpha=0.5, linestyle='-')
gl.top_labels = False
gl.right_labels = False
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER
plt.colorbar(d,orientation='horizontal',label='Akkumulert nedbør case 9.-12.11.2022 [mm]',aspect=40, pad = .1)

