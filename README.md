# kommune-indeks

KOS climate fairness kommune index
===================================

### KSS KIN2100 Data

https://thredds.met.no/thredds/catalog/KSS/Klima_i_Norge_2100/utgave2015/catalog.html 
https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge_2100/utgave2015

```
 TX: Daily_maximum_air_temperature (392 GB)
 TN: Daily_minimum_air_temperature (394 GB)
 TM: air_temperature (350 GB)                       * Bergen
 SWE: snow_water_equivalent_amount (243 GB)
 SMD: soil_moisture_deficit_amount_per_day (513 GB)
 RUN: runoff_amount_per_day (346 GB)
 RR: precipitation_amount_per_day (263 GB)
 GRW: groundwater_amount (416 GB) 

 GCM_RCM model:
    CNRM_CCLM
    CNRM_RCA
    EC-EARTH_CCLM
    EC-EARTH_HIRHAM
    EC-EARTH_RACMO  // Snow challenges?
    EC-EARTH_RCA
    HADGEM_RCA
    IPSL_RCA
    MPI_CCLM
    MPI_RCA
```

Scenarios: hist rcp45 rcp85
- The scenario hist covers the years 1971 to 2005.
- The scenarios rcp45 and rcp85 cover the years 2006 to 2100.


#### Questions (Norwegain)

Per kommune, index over: -> Bergen, Voss, Tromsø

1. Gjennomsnitt av alle modellene (10 stk) -> 1 modell: CNRM_RCA
2. hist, rcp45, og rcp85 per år, eller kun en rcp?? -> hist + rcp45
3. Skal vi ha med per årstid?                       -> ja
4. Hvordan beregne gjennomsnitt av ekstremverdier?
    - gjennomsnitt av modeller
    - median modell?
5. Beregne forskjellige percentiler? Hvilke i såfall?  10% 50%=median 90%
6. For å gjøre det effektivt, har jeg laget skript for å hente ut
   et sett av rektangler før bruk av kommunemasker for å redusere data
   som brukes for beregning av maske.
7. Har vi et bedre kommunemasker enn ks.no kart?
    ks.no - lime inn i norges maske.


### Scripts

Make kommune data, e.g.

`python make_kommune.py --model HADGEM_RCA --write -k Bergen`

The folders and scripts:

- kin_norge/
    - The downloaded and fixed 'scale_factor' attribute in RR and TM
    - from https://thredds.met.no/thredds/catalog/KSS/Klima_i_Norge_2100/utgave2015/catalog.html 
    - See: https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge_2100/utgave2015
    - Downloaded with `download_norge.sh` script.

- kin_kommuner/
    - The files above split into each kommune bounding box (municipality), and masked the data
    inside the kommune-borders.
    - File: Basisdata_0000_Norge_25833_Kommuner2024_GeoJSON.geojson.gz
    - Download from: https://testnedlasting.geonorge.no/geonorge/Basisdata/Kommuner/GeoJSON/
    - Created with `make_kommune.py` python script.

- kin_index/
    - Contains climate indices for each kommune using files in the kin_kommune. Note that these
    are based on the time periods of the scenarions (hist=1971-2005 and rcpXX=2006-2100), and
    computes indices for each of the grid points.
    - Created with `make_index.py` python script.

- kin_mean/
    - Files simply averaging over all the grid points in the kin_index files to make a single
    value for each year, per climate index.
    - Created with `make_mean.sh` bash script.
