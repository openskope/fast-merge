# Fast Merge
This is the code (written in panic mode) to manipulate the spatially
tiled, temporally banded netCDF files and turn them into a GeoTiff
data cubes for the timeseries service or single band GeoTiffs for
geoserver.

## Usage
```bash
# merge into data cube
python merge.py --timedim 'Year AD' --varname 'PPT Uncertainty' -o /projects/skope/datasets/paleocar_2/annual_precipitation/u2.tif /projects/skope/paleocar/*_PPT_UNCERTAINTY.nc

# merge into one geotiff per timestep
python merge.py --separate --timedim 'Year AD' --varname 'Niche' -o /projects/skope/datasets/paleocar_2/maize_farming_niche/geoserver/niche.tif /projects/skope/paleocar/*_NICHE.nc
```

In `separate` mode the timedim value will be inserted into the output
filename immediately prior to the extensions.



__Most likely this is a temporary repository and the tool will be merged
with another repository.__


