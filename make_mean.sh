if [ "$1" == "-h" ]; then
    echo "Usage: sh $(basename $0) [municipality [cdo-fld operator]]"
    echo "       default municipality is Bergen, use "*" for all."
    exit
fi

M="Bergen"
op="mean"

if [ ! -z "$1" ]; then
  M="$1"
fi

# cdo fld<mean|avg|median|min|max|std|std1|var|var1>"
if [ ! -z "$2" ]; then
  op=$2
fi

for m in kin_index/$M; do
    mun=$(basename $m)
    if [ -e kin_mean/$mun ]; then
        continue
    fi

    for f in $m/*.nc; do
        echo $op $f
        mkdir -p kin_mean/$mun
        cdo fld$op $f kin_mean/$mun/${op}_$(basename $f)
    done
done
