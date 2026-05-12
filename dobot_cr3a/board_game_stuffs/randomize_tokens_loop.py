"""
Domain randomization loop for Monopoly tokens in Isaac Sim.

Paste into Window -> Script Editor and click Run, then press Play in the
viewport. The script teleports piece_1 and piece_2 to new poses + colors
every EPISODE_SECONDS *without* stopping the timeline, so the cadence is
actually EPISODE_SECONDS (not stop/restart wall-clock time).

Call stop_loop() to break out.
"""

import math
import random

import numpy as np
import omni.kit.app
import omni.timeline
import omni.usd
from isaacsim.core.prims import RigidPrim
from pxr import Gf, Sdf, UsdShade


# --------------------------------------------------------------------------
# Idempotent cleanup of any previous run
# --------------------------------------------------------------------------
for _name in ("_sub", "_update_sub", "_probe_sub"):
    if _name in globals():
        globals()[_name] = None
if "_running" in globals():
    globals()["_running"] = False


# --------------------------------------------------------------------------
# Tunables
# --------------------------------------------------------------------------
GRID_X = (0.05, 0.28)
GRID_Y = (-0.18, 0.18)
GRID_Z = 0.068
MIN_SEPARATION = 0.04
EPISODE_SECONDS = 3.0

TOKENS = [
    ("/Monopoly/piece_1", "/Monopoly/piece_1_color"),
    ("/Monopoly/piece_2", "/Monopoly/piece_2_color"),
]


# --------------------------------------------------------------------------
# Stage helpers
# --------------------------------------------------------------------------
stage = omni.usd.get_context().get_stage()
timeline = omni.timeline.get_timeline_interface()

# Cache RigidPrim wrappers so we don't rebuild them every cycle.
_rigid_prims = {path: RigidPrim(prim_paths_expr=path) for path, _ in TOKENS}


def _sample_xy(existing):
    for _ in range(100):
        x = random.uniform(*GRID_X)
        y = random.uniform(*GRID_Y)
        if all((x - ex) ** 2 + (y - ey) ** 2 >= MIN_SEPARATION ** 2
               for ex, ey in existing):
            return x, y
    return x, y


def _yaw_quat_wxyz(deg):
    h = math.radians(deg) * 0.5
    return [math.cos(h), 0.0, 0.0, math.sin(h)]


def _teleport(prim_path, x, y, z, yaw_deg):
    """Physics-aware pose set: moves the rigid body and zeroes velocities."""
    rb = _rigid_prims[prim_path]
    rb.set_world_poses(
        positions=np.array([[x, y, z]], dtype=np.float32),
        orientations=np.array([_yaw_quat_wxyz(yaw_deg)], dtype=np.float32),
    )
    rb.set_linear_velocities(np.zeros((1, 3), dtype=np.float32))
    rb.set_angular_velocities(np.zeros((1, 3), dtype=np.float32))


def _set_color(material_path, rgb):
    mat_prim = stage.GetPrimAtPath(material_path)
    for child in mat_prim.GetChildren():
        if not child.IsA(UsdShade.Shader):
            continue
        shader = UsdShade.Shader(child)
        for input_name in ("diffuse_color_constant", "diffuseColor"):
            inp = shader.GetInput(input_name)
            if inp is None:
                if shader.GetImplementationSourceAttr().Get() == "sourceAsset":
                    inp = shader.CreateInput(input_name, Sdf.ValueTypeNames.Color3f)
                else:
                    continue
            inp.Set(Gf.Vec3f(*rgb))
            return
    print(f"[warn] no color input found under {material_path}")


def randomize_tokens():
    placed = []
    for piece_path, mat_path in TOKENS:
        x, y = _sample_xy(placed)
        placed.append((x, y))
        yaw = random.uniform(0, 360)
        _teleport(piece_path, x, y, GRID_Z, yaw)
        _set_color(mat_path, (random.random(), random.random(), random.random()))
        print(f"  {piece_path}: pos=({x:.3f}, {y:.3f}) yaw={yaw:.1f}")
    print(f"randomized; next in {EPISODE_SECONDS}s")


# --------------------------------------------------------------------------
# Loop machinery (wall-clock timer, no timeline stop)
# --------------------------------------------------------------------------
_running = False
_update_sub = None
_last_random_time = 0.0


def _on_update(_dt):
    global _last_random_time
    if not _running or not timeline.is_playing():
        return
    now = timeline.get_current_time()
    if now - _last_random_time >= EPISODE_SECONDS:
        randomize_tokens()
        _last_random_time = now


def start_loop():
    global _running, _update_sub, _last_random_time
    # Long timeline so we don't auto-stop. We drive randomization ourselves.
    timeline.set_start_time(0.0)
    timeline.set_end_time(1e9)
    timeline.set_looping(False)

    _update_sub = (
        omni.kit.app.get_app()
        .get_update_event_stream()
        .create_subscription_to_pop(_on_update)
    )
    _running = True
    _last_random_time = timeline.get_current_time()

    randomize_tokens()
    print("loop started -- press Play in the viewport. call stop_loop() to end.")


def stop_loop():
    global _running, _update_sub
    _running = False
    _update_sub = None
    print("loop stopped (timeline left running)")


start_loop()
