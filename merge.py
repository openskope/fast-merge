import sys
import math
from netCDF4 import Dataset
import numpy as np
import rasterio
from rasterio.transform import Affine, rowcol

import logging
log = logging.getLogger('mergeNC4')
logging.basicConfig(level=logging.WARN)

outfile = '/projects/skope/merge.tif'
precision=7

def main():

    sources = []
    for fname in sys.argv[1:]:
        sources.append(rasterio.open(fname))

    first = sources[0]
    dtype = first.dtypes[0]


    ds = Dataset(sys.argv[1])
    import pdb; pdb.set_trace()

    lat, lng = [], []
    for src in sources:
        left, bottom, right, top = src.bounds
        lng.extend([left, right])
        lat.extend([bottom, top])
        if src.dtypes[0] != sources[0].dtypes[0]:
            log.error('datasets must have the same type')
            sys.exit(1)
        #if src.res != sources[0].res:
        #    log.error('datasets must have the same resolution')
        #    sys.exit(1)
        if src.count != sources[0].count:
            log.error('datasets must have the number of bands')
            sys.exit(1)

    dst_w, dst_s, dst_e, dst_n = min(lng), min(lat), max(lng), max(lat)

    log.debug("Output bounds: %r", (dst_w, dst_s, dst_e, dst_n))
    output_transform = Affine.translation(dst_w, dst_n)
    log.debug("Output transform, before scaling: %r", output_transform)
    output_transform *= Affine.scale(sources[0].res[0], -sources[0].res[1])
    log.debug("Output transform, after scaling: %r", output_transform)

    output_width = int(math.ceil((dst_e - dst_w) / sources[0].res[0]))
    output_height = int(math.ceil((dst_n - dst_s) / sources[0].res[1]))

    # Adjust bounds to fit.
    dst_e, dst_s = output_transform * (output_width, output_height)
    log.debug("Output width: %d, height: %d", output_width, output_height)
    log.debug("Adjusted bounds: %r", (dst_w, dst_s, dst_e, dst_n))

    profile = sources[0].profile
    profile['driver'] = 'GTiff'
    profile['transform'] = output_transform
    profile['height'] = output_height
    profile['width'] = output_width

    profile['nodata'] = None  # rely on alpha mask

    band = np.zeros((profile['height'], profile['width']))
    with rasterio.open(outfile, 'w', **profile) as dstrast:
        import pdb; pdb.set_trace()
        for src in sources:
            b = src.read(1)
            off_y, off_x = [int(i) for i in dstrast.index(*src.xy(0,0))]
            print src.bounds
            print off_y, b.shape[0], off_x, b.shape[1]
            band[off_y:off_y+b.shape[0], off_x:off_x+b.shape[1]] = b
        sys.exit(1)

        for idx, dst_window in dstrast.block_windows():
            left, bottom, right, top = dstrast.window_bounds(dst_window)

            blocksize = dst_window.width
            dst_rows, dst_cols = (dst_window.height, dst_window.width)

            # initialize array destined for the block
            dst_count = first.count
            dst_shape = (dst_count, dst_rows, dst_cols)
            print dst_shape
            log.debug("Temp shape: %r", dst_shape)
            dstarr = np.zeros(dst_shape, dtype=dtype)

            for src in sources:
               window_start = rowcol(src.transform, left, top, 
                       op=round, precision=precision)
               window_stop = rowcol(src.transform, right, bottom, 
                       op=round, precision=precision)
               print src.name, window_start, window_stop
               src_window = tuple(zip(window_start, window_stop))
    
               temp = np.zeros(dst_shape, dtype=dtype)
               print src_window
               temp = src.read(out=temp, window=src_window,
                       boundless=True, masked=False)
    
               # pixels without data yet are available to write
               write_region = np.logical_and((dstarr[3] == 0), (temp[3] != 0))
               np.copyto(dstarr, temp, where=write_region)
    
               # check if dest has any nodata pixels available
               if np.count_nonzero(dstarr[3]) == blocksize:
                   break
    
               dstrast.write(dstarr, window=dst_window)
    
              


if __name__ == '__main__':
    main()
