#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 Pi-Yueh Chuang <pychuang@gwu.edu>
#
# Distributed under terms of the BSD 3-Clause license.

"""The main script of this reproducibility package.
"""
import multiprocessing
import functools
import pathlib
import shutil
import re
import gmsh


def create_mesh(ncells, filename):
    """Creates a mesh w/ a given number of cells on circular edge and saves to a given file path.

    Arguments
    ---------
    ncells : int
        The number of cells on a circular edge of the pipe.
    filename : os.PathLike
        The path to the output mesh file.

    Returns
    -------
    radius, length, dr : float
    ncells, nz, ntotal3d : int
    """

    # initialize gmsh and configure behaviors
    gmsh.initialize()
    gmsh.option.setNumber("General.NumThreads", 0)
    gmsh.option.setNumber("General.ExpertMode", 1)
    gmsh.option.setNumber("Geometry.OCCParallel", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Format", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)

    # pipe dimensions and meshing parameters
    radius = 0.00227
    length = 0.14
    dr = 2.0 * 3.141592653589793 * radius / ncells
    nz = int(length/dr+0.5)

    # pipe geometry
    gmsh.model.occ.addPoint(0., 0., 0., dr, 1)  # center
    gmsh.model.occ.addPoint(radius, 0., 0., dr, 2)  # point at degree 0
    gmsh.model.occ.addPoint(0., radius, 0., dr, 3)  # point at degree 90
    gmsh.model.occ.addPoint(-radius, 0., 0., dr, 4)  # point at degree 180
    gmsh.model.occ.addPoint(0., -radius, 0., dr, 5)  # point at degree 270
    gmsh.model.occ.addCircleArc(2, 1, 3, 1)  # arc connecting point 2 and 3, centered at 1
    gmsh.model.occ.addCircleArc(3, 1, 4, 2)  # arc connecting point 3 and 4, centered at 1
    gmsh.model.occ.addCircleArc(4, 1, 5, 3)  # arc connecting point 4 and 5, centered at 1
    gmsh.model.occ.addCircleArc(5, 1, 2, 4)  # arc connecting point 5 and 2, centered at 1
    gmsh.model.occ.addCurveLoop([1, 2, 3, 4], 1)  # the closed loop edge
    gmsh.model.occ.addPlaneSurface([1], 1)  # the surface enclosed by the closed loop
    gmsh.model.occ.extrude([(2, 1)], 0., 0., length, [nz], recombine=True)  # extrude both geometry and mesh
    gmsh.model.occ.synchronize()  # make the geometry ready for other operations

    # define inlet, outlet, walls, and flow region
    gmsh.model.addPhysicalGroup(2, [1], 1)
    gmsh.model.setPhysicalName(2, 1, "inlet")
    gmsh.model.addPhysicalGroup(2, [6], 2)
    gmsh.model.setPhysicalName(2, 2, "outlet")
    gmsh.model.addPhysicalGroup(2, [2, 3, 4, 5], 3)
    gmsh.model.setPhysicalName(2, 3, "walls")
    gmsh.model.addPhysicalGroup(3, [1], 999)
    gmsh.model.setPhysicalName(2, 999, "internal")

    # meshing in action
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.optimize("Laplace2D")
    gmsh.model.mesh.generate(3)
    gmsh.write(str(filename))  # output (gmsh doesn't like pathlib.Path object...)

    # get the number of 3D cells
    _, elems, _ = gmsh.model.mesh.getElements(3, 1)
    ntotal3d = len(elems[0])  # in our case we only have one type of 3D cells

    # shut down gmsh engine
    gmsh.finalize()

    return radius, length, dr, ncells, nz, ntotal3d


def create_case(ncells, args):
    """Create a case folder for a given number of cells on the circular edge.

    Arguments
    ---------
    ncells : int
        The number of cells on a circular edge of the pipe.
    args : argparse.Namespace
        The cmd arguments specifying the Slurm resource configuration.

    Returns
    -------
    Number of 3D cells of this case.
    """
    # root path of this repo and the path to the case
    root = pathlib.Path(__file__).resolve().parent
    casedir = root.joinpath("cases", f"airflow-pipe-{ncells}")

    # copy the base case files (will overwrite exist files if existing)
    shutil.copytree(root.joinpath("misc", "case.template"), casedir, dirs_exist_ok=True)

    # create a trivial OpenFOAM file
    casedir.joinpath(f"{casedir.name}.foam").touch()

    # create the mesh file in the case folder
    meshinfo = create_mesh(ncells, casedir.joinpath("mesh.msh"))

    # add the slurm script
    slurm = root.joinpath("misc", "job.sh.template").read_text("utf-8")
    slurm = re.sub("<jobname>", casedir.name, slurm)
    slurm = re.sub("<partition>", args.partition, slurm)
    slurm = re.sub("<nodes>", str(args.nodes), slurm)
    slurm = re.sub("<ntasks>", str(args.ntasks), slurm)
    slurm = re.sub("<time>", args.time, slurm)
    casedir.joinpath("job.sh").write_text(slurm, "utf-8")

    # returning number of 3D cells
    return meshinfo[-1]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        allow_abbrev=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--partition", "-p", action="store", type=str, metavar="PARTITION", default="debug-cpu",
        help="The name of partition to use in a cluster managed by Slurm."
    )
    parser.add_argument(
        "--nodes", "-N", action="store", type=int, metavar="NODES", default=1,
        help="The number of nodes to use in the specified partition."
    )
    parser.add_argument(
        "--ntasks", "-n", action="store", type=int, metavar="NTASKS", default=40,
        help="The total number of tasks to use."
    )
    parser.add_argument(
        "--time", "-t", action="store", type=str, metavar="TIME", default="0-04:00:00",
        help="The time limit of this job. Format: {days}-{hours}:{minutes}:{seconds}."
    )
    args = parser.parse_args()

    # generating case folders
    nccs = [16, 32, 64, 128, 256]  # hard code the cases we are generating
    with multiprocessing.Pool(multiprocessing.cpu_count()//2) as pool:
        pool.map(functools.partial(create_case, args=args), nccs, 1)
