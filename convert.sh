#!/bin/bash
# usage: bash convert.sh <variable> <DIM> file [file [file]]
#
# use 'ncks <filename>' to inspect the netcdf file, the name of
# the variable should be self evident (ie GDD) as is the time dimension
# (ie Year or "Year AD"). 

var=$1
shift
dim=$1
shift

for y in {214..2000}; do
  year=`printf '%04d' $y`
  for i in $@; do 
    fname=$(basename "$i")
    ext="${fname##*.}"
    fname="${fname%.*}"

    ncks -v "$var" -d "$dim",$y $i -O ${fname}_${year}.nc4
    gdal_translate -a_srs EPSG:4326 -of GTiff -ot Int16 ${fname}_${year}.nc4 ${fname}_${year}.tif
    rm ${fname}_${year}.nc4
  done

  gdal_merge.py -o ${fname#*_}_${year}.tif *${year}.tif
done
