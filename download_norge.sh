# TX: Daily_maximum_air_temperature (392 GB)
# TN: Daily_minimum_air_temperature (394 GB)
# TM: air_temperature (350 GB)
# SWE: snow_water_equivalent_amount (243 GB)
# SMD: soil_moisture_deficit_amount_per_day (513 GB)
# RUN: runoff_amount_per_day (346 GB)
# RR: precipitation_amount_per_day (263 GB)
# GRW: groundwater_amount (416 GB)
#
# GCM_RCM model:
#    CNRM_CCLM
#    CNRM_RCA
#    EC-EARTH_CCLM
#    EC-EARTH_HIRHAM
#    EC-EARTH_RACMO  // Snæ utfrodringer?
#    EC-EARTH_RCA
#    HADGEM_RCA
#    IPSL_RCA
#    MPI_CCLM
#    MPI_RCA
#
# Scenario: hist rcp45 rcp85
#
# The scenario hist covers the years 1971 to 2005.
# The scenarios rcp45 and rcp85 cover the years 2006 to 2100.

# Author: Tyge Løvset Aug, 2023
# https://thredds.met.no/thredds/catalog/KSS/Klima_i_Norge/utgave2015/catalog.html


ROOT=https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge/utgave2015
ALL_MODELS="CNRM_CCLM CNRM_RCA EC-EARTH_CCLM EC-EARTH_HIRHAM EC-EARTH_RACMO EC-EARTH_RCA HADGEM_RCA IPSL_RCA MPI_CCLM MPI_RCA"

if [ -z "$2" ]; then
    echo "Usage:  $0 TARGETDIR MODELS"
    echo "Examples:"
    echo "  $0 kin_norge HADGEM_RCA"
    echo "  $0 kin_norge all  # $ALL_MODELS" 
    exit
fi

TARGET=$1
shift

if [ "$1" == "all" ]; then
    MODELS=$ALL_MODELS
else
    MODELS=$*
fi

echo Models: $MODELS
echo Target: $TARGET

for VAR in RR TX TN TM # SWE SMD
do
    for SCEN in hist rcp85 # rcp45
    do
        if [ ${SCEN} == "hist" ]
        then
            start=1971
            end=2005
        else
            start=2006
            end=2100
        fi
        for MOD in ${MODELS}
        do
            for ((YEAR=$start; YEAR<=$end; YEAR++))
            do
                DIR=${TARGET}/${SCEN}/${MOD}/${VAR}
                FILE=${SCEN}_${MOD}_${VAR}_daily_${YEAR}_v4.nc
                if [ ! -f ${DIR}/${FILE} ]
                then
                    #echo wget -x -P ${DIR} ${ROOT}/${VAR}/${MOD}/${SCEN}/${FILE}
                    wget -P ${DIR} ${ROOT}/${VAR}/${MOD}/${SCEN}/${FILE}
                fi
            done
        done
    done
done
