"""Add the PushT sheet and the green T block to 9a_imitation_push_t_simulation.usd.

Mirrors movensys-imitation's ``sim/isaacsim/build_scene.py`` (sheet frame, sheet quad, T block
physics) with this scene's look: white sheet with a black filled goal T, green T block.

Authored under ``/World/pusht`` (replaced on every run, so the script can be re-run):

* ``/World/pusht``               sheet frame: axes of ``world_manipulator``, origin at the
                                 push-area centre on the table top (wm -0.03, -0.05, z 0.0431)
* ``/World/pusht/target_sheet``  0.60 x 0.30 m textured quad (``push_t/target_sheet.png``),
                                 visual only, 0.3 mm above the table
* ``/World/pusht/t_block``       rigid T: bar 120 x 30 mm + stem 30 x 90 mm, 30 mm tall, 0.15 kg,
                                 friction 0.40 / 0.35, green, at start-state seed 0

Run ``make_sheet.py`` first. Needs USD's Python (pxr) and numpy; with Isaac Sim's bundled copies:

    E=~/isaacsim/extscache
    L=$E/omni.usd.libs-1.0.1+8131b85d.lx64.r.cp311
    N=$E/omni.kit.pip_archive-0.0.0+8131b85d.lx64.cp311/pip_prebundle
    PYTHONPATH=$L:$N LD_LIBRARY_PATH=$L/bin ~/isaacsim/kit/python/bin/python3 \\
        dobot_cr3a/push_t/add_push_t.py

Close the scene in Isaac Sim first (or reload it afterwards without saving), or Isaac Sim will
overwrite these edits.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

HERE = Path(__file__).resolve().parent
PUSHT = "/World/pusht"
SHEET = f"{PUSHT}/target_sheet"
BLOCK = f"{PUSHT}/t_block"
LOOKS = f"{PUSHT}/Looks"
BLOCK_RGB = (30, 160, 60)  # green T, 0-255 sRGB
# world_manipulator in /World: the robot payload is yawed +90 deg about z at the origin.
WM_IN_WORLD = Gf.Quatf(math.cos(math.pi / 4), 0, 0, math.sin(math.pi / 4))
CENTER_WM = (-0.03, -0.05)  # push-area centre in world_manipulator (imitation default)
TABLE_TOP_Z = 0.0431  # table collision mesh top in world_manipulator / World


def load_geometry(imitation: Path):
    path = imitation / "movensys_imitation/tasks/pusht/geometry.py"
    spec = importlib.util.spec_from_file_location("pusht_geometry", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def set_xform(prim, translate, orient=None, scale=(1, 1, 1)):
    xf = UsdGeom.Xformable(prim)
    xf.ClearXformOpOrder()
    xf.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*translate))
    xf.AddOrientOp(UsdGeom.XformOp.PrecisionFloat).Set(orient or Gf.Quatf(1, 0, 0, 0))
    xf.AddScaleOp(UsdGeom.XformOp.PrecisionFloat).Set(Gf.Vec3f(*scale))


def srgb_to_linear(rgb8):
    out = []
    for c in rgb8:
        c = c / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return Gf.Vec3f(*out)


def surface(stage, path: str, roughness: float):
    mat = UsdShade.Material.Define(stage, path)
    surf = UsdShade.Shader.Define(stage, f"{path}/surface")
    surf.CreateIdAttr("UsdPreviewSurface")
    surf.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    surf.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    mat.CreateSurfaceOutput().ConnectToSource(surf.CreateOutput("surface", Sdf.ValueTypeNames.Token))
    return mat, surf


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", type=Path, default=HERE.parent / "9a_imitation_push_t_simulation.usd")
    ap.add_argument("--imitation", type=Path, default=Path.home() / "movensys-imitation")
    args = ap.parse_args()
    assert (HERE / "target_sheet.png").exists(), "missing target_sheet.png: run make_sheet.py"
    g = load_geometry(args.imitation)

    stage = Usd.Stage.Open(str(args.scene))
    if stage.GetPrimAtPath(PUSHT):
        stage.RemovePrim(PUSHT)

    # Sheet frame. world_manipulator (x, y) -> World (-y, x).
    pusht = UsdGeom.Xform.Define(stage, PUSHT)
    set_xform(pusht.GetPrim(), (-CENTER_WM[1], CENTER_WM[0], TABLE_TOP_Z), WM_IN_WORLD)
    UsdGeom.Scope.Define(stage, LOOKS)

    # Sheet: white with the black filled goal T (texture), visual only.
    hw, hh, z = g.SHEET_SIZE[0] / 2, g.SHEET_SIZE[1] / 2, 0.0003
    mesh = UsdGeom.Mesh.Define(stage, SHEET)
    mesh.CreatePointsAttr([Gf.Vec3f(-hw, -hh, z), Gf.Vec3f(hw, -hh, z), Gf.Vec3f(hw, hh, z), Gf.Vec3f(-hw, hh, z)])
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    mesh.CreateNormalsAttr([Gf.Vec3f(0, 0, 1)] * 4)
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    mesh.CreateExtentAttr([Gf.Vec3f(-hw, -hh, z), Gf.Vec3f(hw, hh, z)])
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateDoubleSidedAttr(True)
    UsdGeom.PrimvarsAPI(mesh).CreatePrimvar(
        "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex
    ).Set(Vt.Vec2fArray([Gf.Vec2f(0, 0), Gf.Vec2f(1, 0), Gf.Vec2f(1, 1), Gf.Vec2f(0, 1)]))

    sheet_mat, surf = surface(stage, f"{LOOKS}/sheet_material", 0.8)
    reader = UsdShade.Shader.Define(stage, f"{LOOKS}/sheet_material/st_reader")
    reader.CreateIdAttr("UsdPrimvarReader_float2")
    reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
    tex = UsdShade.Shader.Define(stage, f"{LOOKS}/sheet_material/texture")
    tex.CreateIdAttr("UsdUVTexture")
    # Relative to the scene file, so the scene keeps working wherever the repo is checked out.
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set("./push_t/target_sheet.png")
    tex.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("clamp")
    tex.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("clamp")
    tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)
    )
    surf.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
    )
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(sheet_mat)

    # Green T block: rigid body made of two box colliders.
    block = UsdGeom.Xform.Define(stage, BLOCK)
    bprim = block.GetPrim()
    x0, y0, yaw0 = g.sample_start_pose(0)
    set_xform(bprim, (x0, y0, 0.001), Gf.Quatf(*g.yaw_to_quat_wxyz(yaw0)))
    rb = UsdPhysics.RigidBodyAPI.Apply(bprim)
    rb.CreateVelocityAttr(Gf.Vec3f(0, 0, 0))
    rb.CreateAngularVelocityAttr(Gf.Vec3f(0, 0, 0))
    UsdPhysics.MassAPI.Apply(bprim).CreateMassAttr(g.BLOCK_MASS)

    block_mat, bsurf = surface(stage, f"{LOOKS}/block_material", 0.6)
    bsurf.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(srgb_to_linear(BLOCK_RGB))
    phys = UsdShade.Material.Define(stage, f"{LOOKS}/block_physics")
    pm = UsdPhysics.MaterialAPI.Apply(phys.GetPrim())
    pm.CreateStaticFrictionAttr(0.40)
    pm.CreateDynamicFrictionAttr(0.35)
    pm.CreateRestitutionAttr(0.0)

    h = g.BLOCK_HEIGHT
    for name, size, centre in (
        ("bar", (g.BAR[0], g.BAR[1], h), (0.0, g.BAR[1] / 2, h / 2)),
        ("stem", (g.STEM[0], g.STEM[1], h), (0.0, -g.STEM[1] / 2, h / 2)),
    ):
        cube = UsdGeom.Cube.Define(stage, f"{BLOCK}/{name}")
        cube.CreateSizeAttr(1.0)
        set_xform(cube.GetPrim(), centre, None, size)
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        api = UsdShade.MaterialBindingAPI.Apply(cube.GetPrim())
        api.Bind(block_mat)
        api.Bind(phys, UsdShade.Tokens.weakerThanDescendants, "physics")

    stage.GetRootLayer().Save()
    print(f"added {PUSHT} to {args.scene}: T start (seed 0) {x0:.3f}, {y0:.3f}, {math.degrees(yaw0):.1f} deg")


if __name__ == "__main__":
    main()
