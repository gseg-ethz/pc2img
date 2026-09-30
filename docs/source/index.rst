======
pc2img
======

``pc2img`` is a scientific Python library from the ETH Zurich Geosensors and
Engineering Geodesy (GSEG) group that converts 3D point clouds into 2D raster
images. It projects points into image space (spherical, orthographic, or
perspective), interpolates the scattered values onto a pixel grid, and
computes named "features" (range, scalar fields, gradients, hillshade, RRIM,
multiscale gradient, and more) as rasters, held in a lazy disk-backed cache.
A tiled orchestrator fans the same pipeline across many point-cloud tiles in
parallel.

See the project `README <https://github.com/gseg-ethz/pc2img#readme>`_ for
installation and a quickstart example.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api
