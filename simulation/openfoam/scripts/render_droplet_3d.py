#!/usr/bin/env python3
"""Render the alpha.water = 0.5 interface as a 3D surface, over one cycle.

Every other figure in this project shows the droplet as a 2D field, which
is exactly the representation the 3D fidelity check exists to question. This
renders the actual interface: marching cubes on alpha.water, lit and shaded,
inside a translucent shell of the channel walls.

Two details matter for correctness:

  * The 3D case models HALF the depth with a symmetry plane at z = w/2, so
    the raw data is a half channel. It is mirrored back (vtkReflectionFilter
    about Z-max) before contouring; skipping that would show a droplet
    sitting on a phantom floor at mid-depth.
  * interFoam writes alpha as CELL data. vtkContourFilter interpolates
    between POINT values, so cell->point conversion has to happen first;
    contouring cell data directly yields a blocky voxel surface rather than
    an interface.

Outputs a filmstrip PNG and, with --gif, an animation over one droplet
period.

Usage:
    python3 render_droplet_3d.py CASE --w-main-um 800 \
        --t-start 0.35 --period 0.110 --out droplet_3d.png --gif
"""
import argparse
from pathlib import Path

import numpy as np
import vtk
from vtk.util import numpy_support  # noqa: F401  (kept for parity with siblings)

WATER = (0.16, 0.44, 0.78)
WALL = (0.60, 0.63, 0.67)


def resolve_times(case_dir, vtk_files):
    """Map VTK files to physical times via the case's time directories.

    foamToVTK names legacy files <case>_<N>.vtk where N is the write INDEX,
    not the time, so the filename number is meaningless as a clock.
    """
    times = sorted(float(d.name) for d in Path(case_dir).iterdir()
                   if d.is_dir() and d.name.replace(".", "").isdigit())
    if len(times) == len(vtk_files):
        return times
    return [float(f.stem.split("_")[-1]) for f in vtk_files]


def _clip(poly, origin, normal):
    """Clip polydata by one plane, returning a concrete vtkPolyData.

    Everything here works on DATA OBJECTS rather than output ports: chaining
    ports across function scopes lets Python collect the intermediate
    filters while the pipeline still references them, which segfaults VTK
    rather than raising.

    Deliberately NOT vtkClipClosedSurface. Capping would be nicer for the
    trimmed water column, but the alpha = 0.5 contour is not a closed
    manifold -- it is open where the water column meets the inlet patch and
    where slugs cross the outlet -- and the capping algorithm responds by
    stringing ribbons between disconnected components.
    """
    pl = vtk.vtkPlane()
    pl.SetOrigin(*origin)
    pl.SetNormal(*normal)
    c = vtk.vtkClipPolyData()
    c.SetInputData(poly)
    c.SetClipFunction(pl)
    c.Update()
    out = vtk.vtkPolyData()
    out.DeepCopy(c.GetOutput())
    return out


def build_pipeline(vtk_file, w_um, x_lo, x_hi, y_stub):
    """Return (droplet actor, channel-edge actor, n interface points)."""
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(str(vtk_file))
    reader.ReadAllScalarsOn()
    reader.Update()

    # half-depth solution -> full channel
    reflect = vtk.vtkReflectionFilter()
    reflect.SetInputData(reader.GetOutput())
    reflect.SetPlane(vtk.vtkReflectionFilter.USE_Z_MAX)
    reflect.CopyInputOn()
    reflect.Update()
    # Merge the duplicate points the reflection leaves along the symmetry
    # plane. Without this the two halves are topologically separate, so
    # marching cubes cannot stitch the interface across the seam and the
    # droplet comes out with a ring of holes around its mid-depth.
    clean = vtk.vtkStaticCleanUnstructuredGrid()
    clean.SetInputData(reflect.GetOutput())
    clean.ToleranceIsAbsoluteOn()
    clean.SetAbsoluteTolerance(1e-9)
    clean.Update()
    grid = vtk.vtkUnstructuredGrid()
    grid.DeepCopy(clean.GetOutput())

    # interFoam writes alpha as CELL data; vtkContourFilter interpolates
    # between POINT values, so contouring cell data gives a blocky voxel
    # surface instead of an interface.
    c2p = vtk.vtkCellDataToPointData()
    c2p.SetInputData(grid)
    c2p.PassCellDataOff()
    c2p.Update()
    pts = c2p.GetOutput()
    pts.GetPointData().SetActiveScalars("alpha.water")

    contour = vtk.vtkContourFilter()
    contour.SetInputData(pts)
    contour.SetValue(0, 0.5)
    contour.Update()
    poly = vtk.vtkPolyData()
    poly.DeepCopy(contour.GetOutput())

    # Trim AFTER contouring so the cut is a clean plane through the surface.
    # The water leg is cut to a short stub: at full height the oil film on
    # its walls wraps the column, and seen edge-on that reads as a picket
    # fence of vertical sheets rather than as a column of water.
    # Frame the junction and outlet, where formation happens. The water leg
    # is cut back to a stub: probing the field shows the leg's minimum
    # cell-centre alpha is 0.75 across x and 0.83 across z, so the oil film
    # on its walls is thinner than a cell and unresolved -- the interface
    # that does appear up there is corner intrusion near the junction, and
    # at full height it clutters the view without being trustworthy.
    y_hi = y_stub * 1e-6
    poly = _clip(poly, (x_lo * 1e-6, 0, 0), (1, 0, 0))
    poly = _clip(poly, (x_hi * 1e-6, 0, 0), (-1, 0, 0))
    poly = _clip(poly, (0, y_hi, 0), (0, -1, 0))

    # Drop numerical crumbs: keep only components with a real cell count.
    conn = vtk.vtkPolyDataConnectivityFilter()
    conn.SetInputData(poly)
    conn.SetExtractionModeToAllRegions()
    conn.Update()
    sizes = [conn.GetRegionSizes().GetValue(i)
             for i in range(conn.GetNumberOfExtractedRegions())]
    conn.SetExtractionModeToSpecifiedRegions()
    for i, n in enumerate(sizes):
        if n >= 40:
            conn.AddSpecifiedRegion(i)
    conn.Update()
    poly = vtk.vtkPolyData()
    poly.DeepCopy(conn.GetOutput())

    smooth = vtk.vtkWindowedSincPolyDataFilter()
    smooth.SetInputData(poly)
    smooth.SetNumberOfIterations(10)
    smooth.SetPassBand(0.12)
    smooth.NormalizeCoordinatesOn()
    smooth.Update()

    # Close the small holes marching cubes leaves where the interface grazes
    # a cell, then orient normals consistently. Inconsistent normals light
    # some facets from behind, which reads as bright holes punched in the
    # droplet.
    holes = vtk.vtkFillHolesFilter()
    holes.SetInputData(smooth.GetOutput())
    holes.SetHoleSize(w_um * 1e-6 * 0.5)
    holes.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(holes.GetOutput())
    normals.SetFeatureAngle(70)
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.SplittingOff()
    normals.Update()

    dm = vtk.vtkPolyDataMapper()
    dm.SetInputData(normals.GetOutput())
    dm.ScalarVisibilityOff()
    drop = vtk.vtkActor()
    drop.SetMapper(dm)
    pr = drop.GetProperty()
    pr.SetColor(*WATER); pr.SetSpecular(0.55); pr.SetSpecularPower(38)
    pr.SetDiffuse(0.8); pr.SetAmbient(0.18)

    # Channel drawn as feature EDGES, not translucent faces: a translucent
    # shell needs depth peeling for correct compositing, and depth peeling
    # segfaults in this offscreen GL context. Edges keep the scene fully
    # opaque, so there is no ordering problem and multisampling stays on.
    box = vtk.vtkBox()
    box.SetBounds(x_lo * 1e-6, x_hi * 1e-6, -1, y_hi, -1, 1)
    gclip = vtk.vtkExtractGeometry()
    gclip.SetInputData(grid)
    gclip.SetImplicitFunction(box)
    gclip.ExtractInsideOn()
    gclip.Update()
    surf = vtk.vtkDataSetSurfaceFilter()
    surf.SetInputData(gclip.GetOutput())
    surf.Update()
    edges = vtk.vtkFeatureEdges()
    edges.SetInputData(surf.GetOutput())
    edges.BoundaryEdgesOn(); edges.FeatureEdgesOn()
    edges.SetFeatureAngle(30)
    edges.NonManifoldEdgesOff(); edges.ManifoldEdgesOff()
    edges.Update()
    wm = vtk.vtkPolyDataMapper()
    wm.SetInputData(edges.GetOutput())
    wm.ScalarVisibilityOff()
    wall = vtk.vtkActor()
    wall.SetMapper(wm)
    wall.GetProperty().SetColor(*WALL)
    wall.GetProperty().SetLineWidth(1.3)
    wall.GetProperty().SetLighting(False)
    return drop, wall, normals.GetOutput().GetNumberOfPoints()


def render(vtk_file, w_um, x_lo, x_hi, y_stub, size, azim, elev, zoom):
    drop, wall, npts = build_pipeline(vtk_file, w_um, x_lo, x_hi, y_stub)
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    ren.AddActor(wall)
    ren.AddActor(drop)

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(*size)
    rw.SetMultiSamples(8)

    cam = ren.GetActiveCamera()
    ren.ResetCamera()
    cam.Azimuth(azim)
    cam.Elevation(elev)
    # The channel is ~8x longer than it is wide; ResetCamera frames the
    # bounding box, so the view has to be pulled in afterwards.
    ren.ResetCameraClippingRange()
    cam.Zoom(zoom)

    light = vtk.vtkLight()
    light.SetPosition(0.3, -0.6, 1.0)
    light.SetIntensity(0.9)
    light.SetLightTypeToCameraLight()
    ren.AddLight(light)

    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.SetScale(1)
    w2i.Update()
    img = w2i.GetOutput()
    dims = img.GetDimensions()
    arr = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars())
    arr = arr.reshape(dims[1], dims[0], -1)[::-1]
    return arr, npts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("--w-main-um", type=float, required=True)
    ap.add_argument("--t-start", type=float, required=True,
                    help="start of the cycle to render (s)")
    ap.add_argument("--period", type=float, required=True, help="one droplet period (s)")
    ap.add_argument("--x-lo-um", type=float, default=1600.0)
    ap.add_argument("--x-hi-um", type=float, default=5600.0)
    ap.add_argument("--y-stub-um", type=float, default=1500.0,
                    help="cut the water leg at this height")
    ap.add_argument("--n-frames", type=int, default=6, help="filmstrip panels")
    ap.add_argument("--azim", type=float, default=-38.0)
    ap.add_argument("--elev", type=float, default=26.0)
    ap.add_argument("--zoom", type=float, default=1.55)
    ap.add_argument("--size", type=int, nargs=2, default=[900, 620])
    ap.add_argument("--gif", action="store_true", help="also write an animation")
    ap.add_argument("--out", type=Path, default=Path("droplet_3d.png"))
    args = ap.parse_args()

    files = sorted((args.case_dir / "VTK").glob("*.vtk"),
                   key=lambda f: int(f.stem.split("_")[-1]))
    times = np.asarray(resolve_times(args.case_dir, files))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    picks = np.linspace(args.t_start, args.t_start + args.period, args.n_frames)
    n = len(picks)
    ncol = min(3, n)
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.6 * ncol, 3.3 * nrow))
    axes = np.atleast_1d(axes).ravel()
    for ax in axes:
        ax.axis("off")
    for k, tp in enumerate(picks):
        i = int(np.argmin(np.abs(times - tp)))
        arr, npts = render(files[i], args.w_main_um, args.x_lo_um, args.x_hi_um,
                           args.y_stub_um, args.size, args.azim, args.elev, args.zoom)
        axes[k].imshow(arr)
        axes[k].set_title(f"{(tp - picks[0]) * 1e3:.0f} ms into cycle",
                          fontsize=10, pad=3)
        print(f"  frame t={times[i]:.3f}s  {npts} interface points", flush=True)
    fig.suptitle(f"{args.w_main_um:.0f} µm milled chip — droplet formation, "
                 "3D interface (alpha = 0.5)\n"
                 "half-depth solution mirrored to the full channel; "
                 "channel outlined in grey", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(args.out, dpi=140)
    print(f"wrote {args.out}")

    if args.gif:
        from PIL import Image
        m = (times >= args.t_start) & (times <= args.t_start + args.period)
        idx = np.where(m)[0]
        frames = []
        for i in idx:
            arr, _ = render(files[i], args.w_main_um, args.x_lo_um, args.x_hi_um,
                            args.y_stub_um, args.size, args.azim, args.elev, args.zoom)
            frames.append(Image.fromarray(arr[..., :3].astype(np.uint8)))
        gif = args.out.with_suffix(".gif")
        frames[0].save(gif, save_all=True, append_images=frames[1:],
                       duration=90, loop=0)
        print(f"wrote {gif}  ({len(frames)} frames)")


if __name__ == "__main__":
    main()
