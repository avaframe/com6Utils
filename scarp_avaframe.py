import rasterio
import numpy as np
import math
from rasterio.transform import rowcol

def main(elevation, perimeter, elevscarp, hrelease, features, method='plane', cellsize=None):
    # Read the input rasters
    with rasterio.open(elevation) as elev_src:
        elev_data = elev_src.read(1)  # Reading the first (and only) band
        elev_transform = elev_src.transform
        n, m = elev_data.shape  # Rows and columns (height and width)
        res = elev_transform[0]  # Pixel resolution

    with rasterio.open(perimeter) as peri_src:
        peri_data = peri_src.read(1)  # Reading the first (and only) band

    # Prepare the output rasters with the same dimensions as the input rasters
    scarp_data = np.zeros_like(elev_data, dtype=np.float32)
    hrel_data = np.zeros_like(elev_data, dtype=np.float32)

    # Calculate scarp and release height based on the selected method
    if method == 'plane':
        scarp_data = calculate_scarp_with_planes(elev_data, peri_data, elev_transform, features)
    elif method == 'ellipsoid':
        scarp_data = calculate_scarp_with_ellipsoids(elev_data, peri_data, elev_transform, features)
    else:
        raise ValueError("Unsupported method. Choose 'plane' or 'ellipsoid'.")

    # Calculate release height
    hrel_data = elev_data - scarp_data

    # Save the scarp and release height rasters
    save_raster(elevscarp, scarp_data, elev_src)
    save_raster(hrelease, hrel_data, elev_src)

def calculate_scarp_with_planes(elev_data, peri_data, elev_transform, planes):
    """Calculate the scarp using sliding planes."""
    n, m = elev_data.shape  # Rows and columns (height and width)
    scarp_data = np.zeros_like(elev_data, dtype=np.float32)

    # Parse the sliding planes parameters
    planes = list(map(float, planes.split(',')))
    nplanes = int(len(planes) / 5)

    xseed = [planes[0]]
    yseed = [planes[1]]
    zseed = [planes[2]]
    dip = [planes[3]]
    slope = [planes[4]]

    betax = [math.tan(slope[0] * math.pi / 180) * math.cos(dip[0] * math.pi / 180)]
    betay = [math.tan(slope[0] * math.pi / 180) * math.sin(dip[0] * math.pi / 180)]

    for i in range(1, nplanes):
        xseed.append(planes[5 * i])
        yseed.append(planes[5 * i + 1])
        zseed.append(planes[5 * i + 2])
        dip.append(planes[5 * i + 3])
        slope.append(planes[5 * i + 4])
        betax.append(math.tan(slope[i] * math.pi / 180) * math.cos(dip[i] * math.pi / 180))
        betay.append(math.tan(slope[i] * math.pi / 180) * math.sin(dip[i] * math.pi / 180))

    # Calculate scarp using planes
    for i in range(n):  # Loop through rows (north-south direction)
        for j in range(m):  # Loop through columns (east-west direction)
            west, north = rasterio.transform.xy(elev_transform, i, j, offset='center')

            # Calculate scarp value using sliding planes
            scarp_val = zseed[0] + (north - yseed[0]) * betay[0] - (west - xseed[0]) * betax[0]
            for k in range(1, nplanes):
                scarp_val = max(scarp_val, zseed[k] + (north - yseed[k]) * betay[k] - (west - xseed[k]) * betax[k])

            if peri_data[i, j] > 0:
                scarp_data[i, j] = min(elev_data[i, j], scarp_val)
            else:
                scarp_data[i, j] = elev_data[i, j]

    return scarp_data

def calculate_scarp_with_ellipsoids(elev_data, peri_data, elev_transform, ellipsoids):
    """Calculate the scarp using sliding circles (rotational ellipsoids)."""
    n, m = elev_data.shape
    scarp_data = np.zeros_like(elev_data, dtype=np.float32)

    # Parse the ellipsoid parameters
    ellipsoids = list(map(float, ellipsoids.split(',')))
    nellipsoids = int(len(ellipsoids) / 5)

    xcenter = [ellipsoids[0]]
    ycenter = [ellipsoids[1]]
    max_depth = [ellipsoids[2]]
    semi_major = [ellipsoids[3]]
    semi_minor = [ellipsoids[4]]

    for i in range(1, nellipsoids):
        xcenter.append(ellipsoids[5 * i])
        ycenter.append(ellipsoids[5 * i + 1])
        max_depth.append(ellipsoids[5 * i + 2])
        semi_major.append(ellipsoids[5 * i + 3])
        semi_minor.append(ellipsoids[5 * i + 4])

    # Calculate scarp using ellipsoids
    for i in range(n):  # Loop through rows (north-south direction)
        for j in range(m):  # Loop through columns (east-west direction)
            west, north = rasterio.transform.xy(elev_transform, i, j, offset='center')

            # Initialize scarp value to current elevation
            scarp_val = elev_data[i, j]

            # Calculate scarp value using ellipsoids
            for k in range(nellipsoids):
                # Calculate the distance from the ellipsoid center
                distance = np.sqrt(((west - xcenter[k]) / semi_major[k])**2 + ((north - ycenter[k]) / semi_minor[k])**2)

                # Check if the point lies within the ellipsoid base
                if distance <= 1:
                    # Calculate the depth within the ellipsoid
                    ellipsoid_depth = max_depth[k] * (1 - distance**2)
                    scarp_val = min(scarp_val, elev_data[i, j] - ellipsoid_depth)

            if peri_data[i, j] > 0:
                scarp_data[i, j] = scarp_val
            else:
                scarp_data[i, j] = elev_data[i, j]

    return scarp_data

def save_raster(output_path, data, reference_src):
    """ Save raster data to a specified format based on file extension """
    driver = 'GTiff' if output_path.endswith('.tif') else 'AAIGrid'
    with rasterio.open(
        output_path, 'w',
        driver=driver,
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=np.float32,
        crs=reference_src.crs,
        transform=reference_src.transform
    ) as dst:
        dst.write(data, 1)

if __name__ == '__main__':
    elevation = 'Molln.asc' #DGM Input raster 
    perimeter = 'Molln_release.asc' #raster that defines maximum extent of scarp
    elevscarp = 'Molln_scarp_output_1.asc' #scarp output
    hrelease = 'Molln_release_output_1.asc' #release output

    # Choose 'plane' or 'ellipsoid' method
    method = 'plane'  # or 'plane'
    
    if method == 'plane':
        features = '68247,299770,920,0,0,68111,299832,850,90,50,68340,299799,850,270,50'  # Example input for planes,x,y,z,dip angle, slope angle, in this case three planes seperated by commas
    elif method == 'ellipsoid':
        features = '68270,299807,80,50,50'  #x_center, y_center, max_depth, semi_major_axis, semi_minor_axis

    main(elevation, perimeter, elevscarp, hrelease, features, method)
