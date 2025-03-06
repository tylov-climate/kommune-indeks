KOS klima kommune index
=======================

## KSS KIN2100 Data

Genererer klimaindekser per kommune, basert på KIN2100 data.

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
- Scenario hist gjelder årene 1971 to 2005.
- Scenario rcp45 og rcp85 gjelder 2006 to 2100.


### Spørsmål

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

## Avhengigheter

Python pakker: cartopy, dateutil, pyproj, shapely, gzip, seaborn, netCDF4, xarray
Netcdf verktøy: CDO, NCO (ncatted)

## Skript

Noen av de nedlastede KSS/Klima_i_Norge/utgave2015 dataene har to metadata skaleringsfeil i tillegg til
feil "chunking" som gjør det ekstremt sakte å hente ut små gridrektangler som kommuner. Man må derfor kjøre
`fix_data_errors.py` etter nedlasting. En må også laste ned selve kommunegrenser-filen og gzippe den.

Lag kommunedata, f.eks:

`python make_region.py --model HADGEM_RCA --write -k Bergen`

CNRM_RCA er brukt som "standard" modell i skriptene, men man kan spesifisere en annen. Kommunedata
kan genereres for valgte kommuner (vil vise kart som standard hvis ikke --write opsjon er brukt).
Videre kan en spesifisere forskjellige scenarioer og klima-indekser for de ulike kommunene:

    - cdd: TM
    - hdd: TM
    - dzc: TN + TX
    - fd: TN
    - su: TX
    - tas: TM
    - tasx: TX
    - tasn: TN
    - pr: RR
    - pr1mm: RR
    - pr20mm: RR
    - pr95p: RR
    - prx5day: RR


### Kataloger:

- kin_norge/
    - Nedlastede, rechunket og korrigerte 'scale_factor' attributter i RR og TM
    - https://thredds.met.no/thredds/catalog/KSS/Klima_i_Norge/utgave2015/catalog.html 
    - https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge/utgave2015
    - Nedlastet med `download_norge.sh` skript.
    - Korrigert med `fix_data_errors.py` python skript.

- kin_kommuner/
- kin_fylke/
    - Filene over er organisert i "bounding box" per kommune/fylke og maskerer data utenfor grensen.
    - Bruker: Basisdata_0000_Norge_25833_Kommuner_GeoJSON.geojson.gz
    - Eller: Basisdata_0000_Norge_25833_Fylker_GeoJSON.geojson.gz
    - Nedlast fra: https://testnedlasting.geonorge.no/geonorge/Basisdata/Kommuner/GeoJSON/
    - Generert med `make_region.py` python skript.

- kin_index/
    - Inneholder klimaindekser for hver kommune, bruker filene i kin_kommune katalogen. Merk at
    disse er basert på tidsperiodene fra scenarioene (hist=1971-2005, rcpXX=2006-2100), og
    beregner indekser for hvert gridpunkt.
    - Generert med `make_index.py` python skript.

- kin_mean/
    - Gjennomsnitt av alle gridpunkt i kin_index filene, og lager en enkeltverdi per år, per klimaindeks.
    - Generert med `make_mean.sh` bash skript.
