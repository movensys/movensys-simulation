#!/usr/bin/env python3
"""
Create a 5×5×5 cm standard d6 dice USD asset for NVIDIA Isaac Sim.

Each face shows its value (1-6) via cylindrical indentations (pips) carved
into the cube body.  Standard opposite-face rule: 1+6, 2+5, 3+4.

Usage (standalone with system python + pxr installed):
    python3 create_dice.py [output.usda]

Usage with Isaac Sim's bundled python:
    isaacsim-python create_dice.py dice.usda

Usage inside Isaac Sim / Omniverse (in a Script Editor panel):
    from create_dice import build_dice
    import omni.usd
    build_dice("/World/Dice", omni.usd.get_context().get_stage())
"""
from __future__ import annotations

import math
import sys
from typing import List, Optional, Tuple

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

# ---------------------------------------------------------------------------
# Geometry constants (all in metres)
# ---------------------------------------------------------------------------
DICE_SIZE   = 0.05          # 5 cm cube
HALF        = DICE_SIZE / 2 # 2.5 cm

PIP_RADIUS  = 0.0035        # 3.5 mm pip radius
PIP_DEPTH   = 0.0025        # 2.5 mm indentation depth
PIP_SPACING = HALF * 0.52   # distance from face centre to outer pip row

GRID_N      = 80            # grid cells per face edge for body mesh
N_CIRC      = 24            # vertices per pip circle

# 2-D pip parameters in face-local [0,1] space
_PIP_R2D  = PIP_RADIUS / DICE_SIZE
_PIP_SP2D = PIP_SPACING / DICE_SIZE

# ---------------------------------------------------------------------------
# Standard pip patterns (u, v) in normalised [-1, 1] grid on each face
# ---------------------------------------------------------------------------
PIP_PATTERN: dict[int, list[Tuple[float, float]]] = {
    1: [( 0,  0)],
    2: [(-1, -1), ( 1,  1)],
    3: [(-1, -1), ( 0,  0), ( 1,  1)],
    4: [(-1, -1), ( 1, -1), (-1,  1), ( 1,  1)],
    5: [(-1, -1), ( 1, -1), ( 0,  0), (-1,  1), ( 1,  1)],
    6: [(-1, -1), (-1,  0), (-1,  1), ( 1, -1), ( 1,  0), ( 1,  1)],
}

# face_key -> die value
FACES = {
    "+Z": 1,  "-Z": 6,
    "+Y": 2,  "-Y": 5,
    "+X": 3,  "-X": 4,
}


# ---------------------------------------------------------------------------
# Face coordinate frames
# ---------------------------------------------------------------------------
def _face_frame(face: str):
    """Return (origin, u_vec, v_vec, normal) for a cube face.

    origin : corner of the face at (u=0, v=0)
    u_vec  : vector spanning the full face width along the u-axis
    v_vec  : vector spanning the full face width along the v-axis
    normal : outward unit normal

    Quad winding (origin, +u, +u+v, +v) is CCW when viewed from outside.
    """
    H, S = HALF, DICE_SIZE
    return {
        "+Z": (Gf.Vec3d(-H, -H,  H), Gf.Vec3d( S, 0, 0), Gf.Vec3d(0,  S, 0), Gf.Vec3d( 0, 0,  1)),
        "-Z": (Gf.Vec3d( H, -H, -H), Gf.Vec3d(-S, 0, 0), Gf.Vec3d(0,  S, 0), Gf.Vec3d( 0, 0, -1)),
        "+X": (Gf.Vec3d( H, -H, -H), Gf.Vec3d(0,  S, 0), Gf.Vec3d(0, 0,  S), Gf.Vec3d( 1, 0,  0)),
        "-X": (Gf.Vec3d(-H,  H, -H), Gf.Vec3d(0, -S, 0), Gf.Vec3d(0, 0,  S), Gf.Vec3d(-1, 0,  0)),
        "+Y": (Gf.Vec3d( H,  H, -H), Gf.Vec3d(-S, 0, 0), Gf.Vec3d(0, 0,  S), Gf.Vec3d( 0, 1,  0)),
        "-Y": (Gf.Vec3d(-H, -H, -H), Gf.Vec3d( S, 0, 0), Gf.Vec3d(0, 0,  S), Gf.Vec3d( 0,-1,  0)),
    }[face]


# ---------------------------------------------------------------------------
# 2-D circle-clipping helpers (face-local coordinate space)
# ---------------------------------------------------------------------------
def _seg_circle_ts(
    ax: float, ay: float, bx: float, by: float,
    cx: float, cy: float, r: float,
) -> List[float]:
    """Return sorted list of t values in [0,1] where segment AB crosses circle (C,r)."""
    dx, dy = bx - ax, by - ay
    fx, fy = ax - cx, ay - cy
    a = dx * dx + dy * dy
    if a < 1e-18:
        return []
    b = 2.0 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - r * r
    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return []
    sq = math.sqrt(disc)
    inv = 0.5 / a
    ts = []
    for t in [(-b - sq) * inv, (-b + sq) * inv]:
        if -1e-9 <= t <= 1.0 + 1e-9:
            ts.append(max(0.0, min(1.0, t)))
    ts.sort()
    return ts


def _clip_poly_outside_circle(
    poly: List[Tuple[float, float]],
    cx: float, cy: float, r: float,
) -> Optional[List[Tuple[float, float]]]:
    """Clip *poly*, keeping the region OUTSIDE circle (C, r).

    Uses Sutherland-Hodgman style traversal with chord approximation
    for the circular arc (error < 0.02 mm at our grid resolution).
    """
    result: List[Tuple[float, float]] = []
    n = len(poly)
    r_sq = r * r

    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        a_in = (ax - cx) ** 2 + (ay - cy) ** 2 < r_sq
        b_in = (bx - cx) ** 2 + (by - cy) ** 2 < r_sq

        if not a_in and not b_in:
            result.append((ax, ay))
            # Edge might still pass through the circle
            ts = _seg_circle_ts(ax, ay, bx, by, cx, cy, r)
            if len(ts) >= 2 and ts[-1] - ts[0] > 1e-9:
                t1, t2 = ts[0], ts[-1]
                result.append((ax + t1 * (bx - ax), ay + t1 * (by - ay)))
                result.append((ax + t2 * (bx - ax), ay + t2 * (by - ay)))

        elif not a_in and b_in:
            result.append((ax, ay))
            ts = _seg_circle_ts(ax, ay, bx, by, cx, cy, r)
            if ts:
                t = ts[0]
                result.append((ax + t * (bx - ax), ay + t * (by - ay)))

        elif a_in and not b_in:
            ts = _seg_circle_ts(ax, ay, bx, by, cx, cy, r)
            if ts:
                t = ts[-1]
                result.append((ax + t * (bx - ax), ay + t * (by - ay)))
        # both inside → skip vertex

    return result if len(result) >= 3 else None


# ---------------------------------------------------------------------------
# Mesh builders
# ---------------------------------------------------------------------------
def _build_meshes(stage, root_path, mat_body, mat_pip):
    """Create the visible dice geometry as two Mesh prims.

    Body : white cube faces with smooth circular holes (grid + circle clipping).
    Pips : black cylindrical indentations (walls + bottom caps).
    """
    body_pts: List[Gf.Vec3f] = []
    body_cnts: List[int] = []
    body_idx: List[int] = []

    pip_pts: List[Gf.Vec3f] = []
    pip_cnts: List[int] = []
    pip_idx: List[int] = []

    inv_n = 1.0 / GRID_N
    cell_diag = inv_n * math.sqrt(2.0)

    for face, value in FACES.items():
        origin, u_vec, v_vec, normal = _face_frame(face)

        # Scalars for fast 3-D reconstruction (no Gf objects in inner loop)
        ox, oy, oz = float(origin[0]), float(origin[1]), float(origin[2])
        ux, uy, uz = float(u_vec[0]), float(u_vec[1]), float(u_vec[2])
        vx, vy, vz = float(v_vec[0]), float(v_vec[1]), float(v_vec[2])

        def to_3f(u: float, v: float) -> Gf.Vec3f:
            return Gf.Vec3f(ox + ux * u + vx * v,
                            oy + uy * u + vy * v,
                            oz + uz * u + vz * v)

        # Pip centres in 2-D face-local [0,1] space
        pip_2d = [(0.5 + pu * _PIP_SP2D, 0.5 + pv * _PIP_SP2D)
                  for pu, pv in PIP_PATTERN[value]]

        # ---- body face (grid with smooth circular holes) ------------------
        base = len(body_pts)

        # Pre-add grid vertices
        for j in range(GRID_N + 1):
            fj = j * inv_n
            for i in range(GRID_N + 1):
                fi = i * inv_n
                body_pts.append(to_3f(fi, fj))

        def grid_vi(i: int, j: int) -> int:
            return base + j * (GRID_N + 1) + i

        r = _PIP_R2D
        r_sq = r * r
        threshold_sq = (r + cell_diag) ** 2

        for j in range(GRID_N):
            fj0 = j * inv_n
            fj1 = (j + 1) * inv_n
            qcy = (j + 0.5) * inv_n

            for i in range(GRID_N):
                fi0 = i * inv_n
                fi1 = (i + 1) * inv_n
                qcx = (i + 0.5) * inv_n

                # Quick check: is this quad near any pip?
                near = None
                for pcx, pcy in pip_2d:
                    if (qcx - pcx) ** 2 + (qcy - pcy) ** 2 < threshold_sq:
                        near = (pcx, pcy)
                        break

                if near is None:
                    # Full quad — use pre-existing grid vertex indices
                    body_idx.extend([grid_vi(i, j), grid_vi(i + 1, j),
                                     grid_vi(i + 1, j + 1), grid_vi(i, j + 1)])
                    body_cnts.append(4)
                    continue

                pcx, pcy = near
                q = [(fi0, fj0), (fi1, fj0), (fi1, fj1), (fi0, fj1)]
                inside = [(v[0] - pcx) ** 2 + (v[1] - pcy) ** 2 < r_sq
                          for v in q]

                if all(inside):
                    continue  # fully inside pip hole — skip

                if not any(inside):
                    # All vertices outside — but edge might pass through
                    has_crossing = False
                    for k in range(4):
                        ax, ay = q[k]
                        bx, by = q[(k + 1) % 4]
                        ts = _seg_circle_ts(ax, ay, bx, by, pcx, pcy, r)
                        if len(ts) >= 2:
                            has_crossing = True
                            break
                    if not has_crossing:
                        body_idx.extend([grid_vi(i, j), grid_vi(i + 1, j),
                                         grid_vi(i + 1, j + 1), grid_vi(i, j + 1)])
                        body_cnts.append(4)
                        continue

                # Clip the quad against the pip circle
                clipped = _clip_poly_outside_circle(q, pcx, pcy, r)
                if clipped is None:
                    continue

                # Add clipped polygon vertices and fan-triangulate
                vi0 = len(body_pts)
                for uv in clipped:
                    body_pts.append(to_3f(uv[0], uv[1]))
                for k in range(1, len(clipped) - 1):
                    body_idx.extend([vi0, vi0 + k, vi0 + k + 1])
                    body_cnts.append(3)

        # ---- pip indentations (cylinder wall + bottom cap) ----------------
        u_dir = Gf.Vec3d(u_vec).GetNormalized()
        v_dir = Gf.Vec3d(v_vec).GetNormalized()
        lift = normal * 0.0002          # tiny lift to cover grid seam

        for pcx, pcy in pip_2d:
            pc_3d = origin + u_vec * pcx + v_vec * pcy
            pb = len(pip_pts)
            depth_off = normal * PIP_DEPTH

            # Top ring (at face surface + tiny lift)
            for n in range(N_CIRC):
                a = 2.0 * math.pi * n / N_CIRC
                off = u_dir * (math.cos(a) * PIP_RADIUS) \
                    + v_dir * (math.sin(a) * PIP_RADIUS)
                p = pc_3d + off + lift
                pip_pts.append(Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])))

            # Bottom ring (indentation floor)
            for n in range(N_CIRC):
                a = 2.0 * math.pi * n / N_CIRC
                off = u_dir * (math.cos(a) * PIP_RADIUS) \
                    + v_dir * (math.sin(a) * PIP_RADIUS)
                p = pc_3d - depth_off + off
                pip_pts.append(Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])))

            # Bottom centre
            bc = pc_3d - depth_off
            bc_vi = len(pip_pts)
            pip_pts.append(Gf.Vec3f(float(bc[0]), float(bc[1]), float(bc[2])))

            top, bot = pb, pb + N_CIRC

            # Cylinder wall quads (normals face inward — visible from outside)
            for n in range(N_CIRC):
                n1 = (n + 1) % N_CIRC
                pip_idx.extend([top + n, top + n1, bot + n1, bot + n])
                pip_cnts.append(4)

            # Bottom cap triangles (normal faces outward toward viewer)
            for n in range(N_CIRC):
                n1 = (n + 1) % N_CIRC
                pip_idx.extend([bc_vi, bot + n, bot + n1])
                pip_cnts.append(3)

    # ---- write body mesh --------------------------------------------------
    body = UsdGeom.Mesh.Define(stage, f"{root_path}/Body")
    body.GetPointsAttr().Set(Vt.Vec3fArray(body_pts))
    body.GetFaceVertexCountsAttr().Set(Vt.IntArray(body_cnts))
    body.GetFaceVertexIndicesAttr().Set(Vt.IntArray(body_idx))
    body.GetDoubleSidedAttr().Set(True)
    UsdShade.MaterialBindingAPI(body.GetPrim()).Bind(mat_body)

    # ---- write pip mesh ---------------------------------------------------
    pips = UsdGeom.Mesh.Define(stage, f"{root_path}/Pips")
    pips.GetPointsAttr().Set(Vt.Vec3fArray(pip_pts))
    pips.GetFaceVertexCountsAttr().Set(Vt.IntArray(pip_cnts))
    pips.GetFaceVertexIndicesAttr().Set(Vt.IntArray(pip_idx))
    pips.GetDoubleSidedAttr().Set(True)
    UsdShade.MaterialBindingAPI(pips.GetPrim()).Bind(mat_pip)


# ---------------------------------------------------------------------------
# Material helper
# ---------------------------------------------------------------------------
def _make_material(
    stage: Usd.Stage,
    path: str,
    color: Gf.Vec3f,
    roughness: float = 0.3,
) -> UsdShade.Material:
    mat = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, f"{path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(color)
    shader.CreateInput("roughness",    Sdf.ValueTypeNames.Float).Set(roughness)
    mat.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    return mat


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_dice(root_path: str, stage: Usd.Stage) -> UsdGeom.Xform:
    """
    Build a dice hierarchy under *root_path* on an existing *stage*.

    Hierarchy:

        <root>        -- RigidBodyAPI + MassAPI
          Collision    -- invisible Cube with CollisionAPI (box shape for PhysX)
          Body         -- Mesh: white cube faces with smooth circular holes
          Pips         -- Mesh: black cylindrical indentations
          Materials/

    Returns the root Xform prim.
    """
    root = UsdGeom.Xform.Define(stage, root_path)

    # ---- materials --------------------------------------------------------
    mat_dir = f"{root_path}/Materials"
    mat_white = _make_material(stage, f"{mat_dir}/White",
                               Gf.Vec3f(0.95, 0.95, 0.95), roughness=0.25)
    mat_black = _make_material(stage, f"{mat_dir}/Black",
                               Gf.Vec3f(0.05, 0.05, 0.05), roughness=0.25)

    # ---- physics on root --------------------------------------------------
    UsdPhysics.RigidBodyAPI.Apply(root.GetPrim())
    mass_api = UsdPhysics.MassAPI.Apply(root.GetPrim())
    mass_api.GetMassAttr().Set(0.012)   # 12 g — typical plastic die

    # ---- invisible collision cube -----------------------------------------
    collision = UsdGeom.Cube.Define(stage, f"{root_path}/Collision")
    collision.GetSizeAttr().Set(DICE_SIZE)
    collision.GetPurposeAttr().Set("guide")
    UsdPhysics.CollisionAPI.Apply(collision.GetPrim())

    # ---- visual meshes (body + pips) --------------------------------------
    _build_meshes(stage, root_path, mat_white, mat_black)

    return root


# ---------------------------------------------------------------------------
# Standalone entry-point
# ---------------------------------------------------------------------------
def main() -> None:
    output = sys.argv[1] if len(sys.argv) > 1 else "dice.usda"

    stage = Usd.Stage.CreateNew(output)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(0)

    root = build_dice("/Dice", stage)
    stage.SetDefaultPrim(root.GetPrim())

    stage.GetRootLayer().Save()

    total_pips = sum(len(v) for v in PIP_PATTERN.values())
    print(f"Saved: {output}")
    print(f"  Cube size  : {DICE_SIZE*100:.0f} x {DICE_SIZE*100:.0f} x {DICE_SIZE*100:.0f} cm")
    print(f"  Pip radius : {PIP_RADIUS*1000:.1f} mm")
    print(f"  Pip depth  : {PIP_DEPTH*1000:.1f} mm (indentation)")
    print(f"  Total pips : {total_pips}")
    print()
    print("Face layout (Z-up, standard opposite rule):")
    for face, val in FACES.items():
        dots = len(PIP_PATTERN[val])
        print(f"  {face:3s} face -> {val} pip{'s' if val > 1 else ' '} "
              f"({dots} dot{'s' if val > 1 else ''})")


if __name__ == "__main__":
    main()
