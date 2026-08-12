#!/usr/bin/env python3
"""Export the coded-droplet interface (one or more frames) as a compact JSON
mesh for an interactive WebGL viewer: vertices, triangles, per-vertex RGB
(composition) and normals, plus the channel wireframe.
"""
import sys, json
import numpy as np
import vtk
from vtk.util import numpy_support
from pathlib import Path

CASE = Path(sys.argv[1]); OUT = Path(sys.argv[2])
X_LO, X_HI, Y_STUB = 2200e-6, 6400e-6, 1500e-6
W_UM = 800.0
frame_times = [float(x) for x in sys.argv[3].split(",")]

# map file -> exact time
vdir = CASE / "VTK"
files = sorted(vdir.glob("*.vtk"), key=lambda f: int(f.stem.split("_")[-1]))
series = json.loads(next(vdir.glob("*.vtk.series")).read_text())["files"]
name2t = {e["name"]: e["time"] for e in series}
times = np.array([name2t.get("_" + f.stem.split("_")[-1], np.nan) for f in files])


def clip(poly, origin, normal):
    pl = vtk.vtkPlane(); pl.SetOrigin(*origin); pl.SetNormal(*normal)
    c = vtk.vtkClipPolyData(); c.SetInputData(poly); c.SetClipFunction(pl); c.Update()
    o = vtk.vtkPolyData(); o.DeepCopy(c.GetOutput()); return o


def surface(vtk_file):
    r = vtk.vtkUnstructuredGridReader(); r.SetFileName(str(vtk_file)); r.ReadAllScalarsOn(); r.Update()
    ref = vtk.vtkReflectionFilter(); ref.SetInputData(r.GetOutput())
    ref.SetPlane(vtk.vtkReflectionFilter.USE_Z_MAX); ref.CopyInputOn(); ref.Update()
    cl = vtk.vtkStaticCleanUnstructuredGrid(); cl.SetInputData(ref.GetOutput())
    cl.ToleranceIsAbsoluteOn(); cl.SetAbsoluteTolerance(1e-9); cl.Update()
    grid = vtk.vtkUnstructuredGrid(); grid.DeepCopy(cl.GetOutput())
    cd = grid.GetCellData()
    w = [numpy_support.vtk_to_numpy(cd.GetArray(f"alpha.water{i}")) for i in (1,2,3)]
    aw = numpy_support.numpy_to_vtk(np.ascontiguousarray(w[0]+w[1]+w[2]), deep=1)
    aw.SetName("alpha.water"); grid.GetCellData().AddArray(aw)
    c2p = vtk.vtkCellDataToPointData(); c2p.SetInputData(grid); c2p.PassCellDataOff(); c2p.Update()
    pts = c2p.GetOutput(); pts.GetPointData().SetActiveScalars("alpha.water")
    ct = vtk.vtkContourFilter(); ct.SetInputData(pts); ct.SetValue(0, 0.5); ct.Update()
    poly = vtk.vtkPolyData(); poly.DeepCopy(ct.GetOutput())
    poly = clip(poly, (X_LO,0,0),(1,0,0)); poly = clip(poly,(X_HI,0,0),(-1,0,0))
    poly = clip(poly, (0,Y_STUB,0),(0,-1,0))
    conn = vtk.vtkPolyDataConnectivityFilter(); conn.SetInputData(poly)
    conn.SetExtractionModeToAllRegions(); conn.Update()
    sizes = [conn.GetRegionSizes().GetValue(i) for i in range(conn.GetNumberOfExtractedRegions())]
    conn.SetExtractionModeToSpecifiedRegions()
    for i,n in enumerate(sizes):
        if n >= 40: conn.AddSpecifiedRegion(i)
    conn.Update(); poly = vtk.vtkPolyData(); poly.DeepCopy(conn.GetOutput())
    sm = vtk.vtkWindowedSincPolyDataFilter(); sm.SetInputData(poly)
    sm.SetNumberOfIterations(10); sm.SetPassBand(0.12); sm.NormalizeCoordinatesOn(); sm.Update()
    hl = vtk.vtkFillHolesFilter(); hl.SetInputData(sm.GetOutput()); hl.SetHoleSize(W_UM*1e-6*0.5); hl.Update()
    nm = vtk.vtkPolyDataNormals(); nm.SetInputData(hl.GetOutput()); nm.SetFeatureAngle(70)
    nm.ConsistencyOn(); nm.AutoOrientNormalsOn(); nm.SplittingOff(); nm.ComputePointNormalsOn(); nm.Update()
    tf = vtk.vtkTriangleFilter(); tf.SetInputData(nm.GetOutput()); tf.Update()
    return tf.GetOutput()


def mesh_arrays(poly):
    P = numpy_support.vtk_to_numpy(poly.GetPoints().GetData()).astype(np.float64)
    polys = numpy_support.vtk_to_numpy(poly.GetPolys().GetData())
    tris = polys.reshape(-1,4)[:,1:4].astype(np.int32)          # drop the leading '3'
    N = numpy_support.vtk_to_numpy(poly.GetPointData().GetNormals()).astype(np.float64)
    pdd = poly.GetPointData()
    w = [numpy_support.vtk_to_numpy(pdd.GetArray(f"alpha.water{i}")) for i in (1,2,3)]
    tot = np.maximum(w[0]+w[1]+w[2], 1e-6)
    comp = np.clip(np.stack([w[0]/tot,w[1]/tot,w[2]/tot],1)**0.75, 0, 1)
    rgb = (comp*255).astype(np.uint8)
    return P, tris, N, rgb


def channel_wire():
    """Feature edges of the framed channel box, as line segments."""
    # simple box outline in the framed region (full depth -w/2..w/2)
    w = W_UM*1e-6; yhi = Y_STUB
    xs=[X_LO,X_HI]; ys=[0,0.8e-3]; zs=[-w/2, w/2]
    corners=[(x,y,z) for x in xs for y in ys for z in zs]
    segs=[]
    import itertools
    for a,b in itertools.combinations(range(8),2):
        ca,cb=corners[a],corners[b]
        if sum(1 for k in range(3) if abs(ca[k]-cb[k])>1e-12)==1:
            segs.append((ca,cb))
    return segs


# center + scale everything to a nice unit box for the viewer
frames=[]
for tp in frame_times:
    i=int(np.argmin(np.abs(times-tp)))
    P,tris,N,rgb=mesh_arrays(surface(files[i]))
    frames.append((times[i],P,tris,N,rgb))
    print(f"frame t={times[i]:.3f}s  {len(P)} verts  {len(tris)} tris", flush=True)

# common center/scale from the first frame's bounds (stable across frames)
allP=np.vstack([f[1] for f in frames])
c=allP.mean(0); s=1.0/(allP.max(0)-allP.min(0)).max()
def norm(P): return ((P-c)*s)

wire=[[list(norm(np.array(a))), list(norm(np.array(b)))] for a,b in channel_wire()]

out={"scale":s, "frames":[]}
for t,P,tris,N,rgb in frames:
    out["frames"].append({
        "t": round(float(t),4),
        "pos": np.round(norm(P),4).ravel().tolist(),
        "idx": tris.ravel().tolist(),
        "nrm": np.round(N,3).ravel().tolist(),
        "col": rgb.ravel().tolist(),
    })
out["wire"]=wire
OUT.write_text(json.dumps(out))
kb=OUT.stat().st_size/1024
print(f"wrote {OUT}  ({len(frames)} frames, {kb:.0f} KB)")
