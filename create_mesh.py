#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 Pi-Yueh Chuang <pychuang@gwu.edu>
#
# Distributed under terms of the BSD 3-Clause license.

"""Create a mesh w/ a given number of cells on edge.
"""
import argparse
import pathlib
import gmsh

# parsing command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "nr", action="store", type=int, metavar="NCELLS",
    help="Number of cells on the circle edge.")
parser.add_argument(
    "--prefix", action="store", type=pathlib.Path, metavar="PATH", default=pathlib.Path.cwd(),
    help="Saving the mesh file to under thie folder (default: current folder).")
args = parser.parse_args()

# initialize gmsh
gmsh.initialize()

# general gmsh behaviors
gmsh.option.setNumber("General.NumThreads", 0)

# meshing behaviors
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.Format", 1)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)

# pipe dimensions
radius = 0.00227
length = 0.14

# meshing parameters
nr = args.nr
dr = 2.0 * 3.141592653589793 * radius / nr
nz = int(length/dr+0.5)

# print info
print(f"cylinder radius {radius}");
print(f"cylinder length {length}");
print(f"cell size on a cylinder edge {dr}");
print(f"number of cells on a cylinder edge = {nr}");
print(f"number of cells in z = {nz}");

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

# define inlet
gmsh.model.addPhysicalGroup(2, [1], 1)
gmsh.model.setPhysicalName(2, 1, "inlet")

# define outlet
gmsh.model.addPhysicalGroup(2, [6], 2)
gmsh.model.setPhysicalName(2, 2, "outlet")

# define walls
gmsh.model.addPhysicalGroup(2, [2, 3, 4, 5], 3)
gmsh.model.setPhysicalName(2, 3, "walls")

# define internal flow region
gmsh.model.addPhysicalGroup(3, [1], 999)
gmsh.model.setPhysicalName(2, 999, "internal")

# meshing actions
gmsh.model.mesh.generate(1)
gmsh.model.mesh.generate(2)
gmsh.model.mesh.optimize("Laplace2D")
gmsh.model.mesh.generate(3)

# output the mesh
gmsh.write(str(args.prefix.joinpath(f"pipe-{nr}.msh")))
