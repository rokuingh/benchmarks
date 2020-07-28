import os

RUNDIR="/home/ryan/MBMeshPerformanceResults"
SRCDIR="/home/ryan/Dropbox/sandbox/profiling/ESMF_ProfileMBMesh"

procs=(1, 2, 4, 8)

esmf_env = dict(ESMF_OS = "Linux",
               ESMF_COMPILER = "gfortran",
               ESMF_COMM = "openmpi",
               ESMF_NETCDF = "split",
               ESMF_NETCDF_INCLUDE="/usr/local/include",
               ESMF_NETCDF_LIBPATH="/usr/local/lib",
               ESMF_BUILD_NP=6)

testcase_args = dict(
    create = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1deg.esmf.nc"),
                  GRID2 = os.path.join(SRCDIR,"data", "ll1deg.esmf.nc")),
    dual = dict(GRID1 = os.path.join(SRCDIR,"data", "ll4deg.esmf.nc"),
                GRID2 = os.path.join(SRCDIR,"data", "ll4deg.esmf.nc")),
    GRID2mesh = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1deg.scrip.nc"),
                     GRID2 = os.path.join(SRCDIR,"data", "ll1deg.scrip.nc")),
    redist = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                  GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")),
    regridbilinear = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                          GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")),
    regridconservative = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                              GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")),
    rendezvous = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                      GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"))
)
