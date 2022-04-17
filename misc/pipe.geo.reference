SetFactory("OpenCASCADE");

// general gmsh behaviors
General.NumThreads = 0;

// meshing behaviors
Mesh.Algorithm = 6;
Mesh.Algorithm3D = 1;
Mesh.Format = 1;
Mesh.MshFileVersion = 2.2;

// pipe dimensions
radius = 0.00227;
length = 0.14;

// meshing parameters
nr = DefineNumber[16, Name "nr"];
dr = 2.0 * Pi * radius / nr;
nz = length / dr;

// print info
Printf("cylinder radius = %g", radius);
Printf("cylinder length = %g", length);
Printf("cell size on a cylinder edge = %g", dr);
Printf("number of cells on a cylinder edge = %g", nr);
Printf("number of cells in z = %g", nz);

// circle center
Point(1) = {0, 0, 0, dr};

// points for defining a circle
Point(2) = {radius, 0, 0, dr};
Point(3) = {0, radius, 0, dr};
Point(4) = {-radius, 0, 0, dr};
Point(5) = {0, -radius, 0, dr};

// circle segments
Circle(1) = {2, 1, 3};
Circle(2) = {3, 1, 4};
Circle(3) = {4, 1, 5};
Circle(4) = {5, 1, 2};

// circle
Curve Loop(1) = {1, 2, 3, 4};

// the surfac enclosed by the circle
Plane Surface(1) = {1};

// extrude the surface to a cylinder with meshing parameter
Extrude {0, 0, length} {Surface{1}; Layers{nz}; Recombine;}

// physical group for inlet
Physical Surface("inlet") = {1};

// physical group for outlet
Physical Surface("outlet") = {6};

// physical group fro no-slip walls
Physical Surface("walls") = {2, 3, 4, 5};

// physical group for the flow region
Physical Volume("internal") = {1};

// meshing actions
Mesh 1;
Mesh 2;
OptimizeMesh "Laplace2D";
Mesh 3;
Save Sprintf("pipe-%g.msh", nr);
