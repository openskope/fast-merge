import os
import sys
import argparse
import math
from netCDF4 import Dataset
import numpy as np
import rasterio
from rasterio.transform import Affine, rowcol
from rasterio.crs import CRS

import logging
log = logging.getLogger('mergeNC4')
logging.basicConfig(level=logging.WARN)


def add_local_args(parser):

    parser.add_argument('--output', '-o', metavar='FILE', required=True,
        help='name of the output file')
    parser.add_argument('--varname', metavar='VAR', required=True, default='',
        help='the variable name to merged.')
    parser.add_argument('inputs', metavar='FILE', nargs='+',
        help='one or more input files')
    parser.add_argument('--timedim', '-t', default='Year',
        help='Name of the temporal dimension (default=Year)')
    parser.add_argument('--output-format', metavar='FORMAT', default='GTiff', 
        help='Output file format (default=GTiff)')
    parser.add_argument('--quiet', '-q', default=False, action='store_true',
        help='no output')
    parser.add_argument('--separate', default=False, action='store_true',
        help='write each band to a separate file')


def main():

    parser = argparse.ArgumentParser()
    add_local_args(parser)
    args = parser.parse_args()

    # TODO we can probably get rid of this
    first = rasterio.open(args.inputs[0])
    
    sources = []
    for fname in args.inputs:
        sources.append(Dataset(fname))

    lat, lng = [], []
    for src in sources:
        lng.extend(src.variables['longitude'][:].tolist())
        lat.extend(src.variables['latitude'][:].tolist())
    lng = list(sorted(set(lng)))
    lat = list(sorted(set(lat)))

    dst_w, dst_s, dst_e, dst_n = min(lng), min(lat), max(lng), max(lat)

    # TODO is this safe?
    #  creating a set from floats seems dangerous
    output_width = len(lng)
    output_height = len(lat)
    # frequent off-by-one errors
    #output_width = int(math.ceil((dst_e - dst_w) / first.res[0])+1)
    #output_height = int(math.ceil((dst_n - dst_s) / first.res[1])+1)

    log.debug("Output bounds: %r", (dst_w, dst_s, dst_e, dst_n))
    output_transform = Affine.translation(dst_w, dst_n)
    log.debug("Output transform, before scaling: %r", output_transform)
    output_transform *= Affine.scale(first.res[0], -first.res[1])
    # TODO the following line is close. check parameter order
    #output_transform *= Affine.scale(lat[1]-lat[0], lng[1]-lng[0])
    log.debug("Output transform, after scaling: %r", output_transform)

    # Seems close 
    #output_width = int(math.ceil((dst_e - dst_w) / first.res[0])+1)
    #output_height = int(math.ceil((dst_n - dst_s) / first.res[1])+1)
    

    # Adjust bounds to fit.
    dst_e, dst_s = output_transform * (output_width, output_height)
    log.debug("Output width: %d, height: %d", output_width, output_height)
    log.debug("Adjusted bounds: %r", (dst_w, dst_s, dst_e, dst_n))

    profile = first.profile
    profile['driver'] = 'GTiff'
    profile['transform'] = output_transform
    profile['height'] = output_height
    profile['width'] = output_width
    profile['crs'] = CRS().from_string(sources[0].crs)

    profile['nodata'] = first.nodata

    band = np.zeros((profile['height'], profile['width']), 
                    dtype=first.dtypes[0])

    if not args.separate:
        with rasterio.open(args.output, 'w', **profile) as dstrast:
            for i in range(dstrast.count):
                if not args.quiet and i % 10 == 0:
                    sys.stderr.write('.')
                for src in sources:
                    b = src.variables[args.varname][i,:,:]
                    off_y = src.variables['latitude'][:].max()
                    off_x = src.variables['longitude'][:].min()
                    rowcol = dstrast.index(off_x, off_y)
                    row, col = int(rowcol[0]), int(rowcol[1])
                    log.debug('upper-left: lat=%3.6f (%d), long=%3.6f (%d)', 
                              off_y, row, off_x, col)
                    band[row:row+b.shape[0], col:col+b.shape[1]] = b
                    dstrast.write(band, i+1)
    
    if args.separate:
        timedim = sources[0].variables[args.timedim]
        #nodata=sources[0].variables[args.varname].missing_value)
        profile.update(count=1, blockxsize=256, blockysize=256, tiled='yes')
        del profile['crs']
        for i in range(len(timedim)):
            if not args.quiet and i % 10 == 0:
                sys.stderr.write('.')
            filename, ext = os.path.splitext(args.output)
            output = '%s_%04d%s' % (filename, int(timedim[i]), ext)
            with rasterio.open(output, 'w', **profile) as dstrast:
                for src in sources:
                    b = src.variables[args.varname][i,:,:]
                    off_y = src.variables['latitude'][:].max()
                    off_x = src.variables['longitude'][:].min()
                    rowcol = dstrast.index(off_x, off_y)
                    row, col = int(rowcol[0]), int(rowcol[1])
                    log.debug('upper-left: lat=%3.6f (%d), long=%3.6f (%d)', 
                              off_y, row, off_x, col)
                    band[row:row+b.shape[0], col:col+b.shape[1]] = b
                    dstrast.write(band, 1)
        
    sys.stderr.write('done\n')
if __name__ == '__main__':
    main()
