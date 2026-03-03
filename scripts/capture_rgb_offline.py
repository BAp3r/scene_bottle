"""
capture_rgb_offline.py

加载离线 Office 场景和 Orbbec Gemini 335L 相机 USD，抓取一张 RGB 图像。

运行示例：
    conda activate env_isaaclab
    python scripts/capture_rgb_offline.py

可选参数：
    python scripts/capture_rgb_offline.py --width 1280 --height 720
    python scripts/capture_rgb_offline.py --camera-prim /World/Orbbec/.../Camera
    python scripts/capture_rgb_offline.py --scene-usd usds/objects/Office/office.usd --camera-translate 0.0,-0.5,1.6 --camera-orient 1,0,0,0
    python scripts/capture_rgb_offline.py --post-exposure 2.0 --post-gamma 0.8
    python scripts/capture_rgb_offline.py --scene-usd usds/objects/Office/office.usd --skip-orbbec-model --list-cameras
"""

import argparse
import os

from isaacsim import SimulationApp


def parse_args():
    parser = argparse.ArgumentParser(description="Capture one RGB image from offline USD scene")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--warmup", type=int, default=120, help="Number of app.update() warmup frames")
    parser.add_argument("--camera-prim", type=str, default="", help="Optional explicit camera prim path")
    parser.add_argument(
        "--camera-translate",
        type=str,
        default="",
        help="Optional camera world translation as x,y,z",
    )
    parser.add_argument(
        "--camera-orient",
        type=str,
        default="",
        help="Optional camera world orientation as w,x,y,z",
    )
    parser.add_argument(
        "--scene-usd",
        type=str,
        default="",
        help="Optional scene USD path (e.g. usds/objects/Office/office.usd)",
    )
    parser.add_argument(
        "--skip-orbbec-model",
        action="store_true",
        help="Do not load Orbbec USD model; capture from existing camera prim in scene",
    )
    parser.add_argument(
        "--list-cameras",
        action="store_true",
        help="Only list detected camera prims and exit",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (default: GUI mode)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/rgb/orbbec_office_rgb.png",
        help="Output image path",
    )
    parser.add_argument(
        "--post-exposure",
        type=float,
        default=1.0,
        help="Optional brightness multiplier applied before saving",
    )
    parser.add_argument(
        "--post-gamma",
        type=float,
        default=1.0,
        help="Optional gamma correction (value < 1 brightens)",
    )
    return parser.parse_args()


args = parse_args()
app = SimulationApp({"headless": args.headless, "width": args.width, "height": args.height})

import numpy as np
import omni.replicator.core as rep
import omni.usd
from PIL import Image
from isaacsim.sensors.camera import Camera
from pxr import Gf, Usd, UsdGeom, UsdLux


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OFFICE_USD = os.path.join(ROOT_DIR, "usds", "objects", "Office", "office.usd")
ORBBEC_USD = os.path.join(ROOT_DIR, "usds", "objects", "orbbec_gemini_335L.usd")
DEBUG_LOG = os.path.join(ROOT_DIR, "outputs", "rgb", "capture_debug.log")


def log(msg):
    os.makedirs(os.path.dirname(DEBUG_LOG), exist_ok=True)
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg, flush=True)


def tick(n=1):
    for _ in range(n):
        app.update()


def ensure_exists(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"USD not found: {path}")


def parse_float_tuple(raw, expected_len, arg_name):
    parts = [x.strip() for x in raw.split(",") if x.strip() != ""]
    if len(parts) != expected_len:
        raise ValueError(f"{arg_name} must have {expected_len} comma-separated values, got: {raw}")
    return tuple(float(x) for x in parts)


def set_pose(prim, translation=None, orientation=None):
    xformable = UsdGeom.Xformable(prim)
    ops = xformable.GetOrderedXformOps()

    trans_op = None
    orient_op = None
    for op in ops:
        if op.GetOpName() == "xformOp:translate":
            trans_op = op
        elif op.GetOpName() == "xformOp:orient":
            orient_op = op

    if translation is not None:
        if trans_op is None:
            trans_op = xformable.AddTranslateOp()
        trans_op.Set(Gf.Vec3d(*translation))

    if orientation is not None:
        if orient_op is None:
            orient_op = xformable.AddOrientOp(precision=UsdGeom.XformOp.PrecisionFloat)
        try:
            orient_op.Set(Gf.Quatd(*orientation))
        except Exception:
            orient_op.Set(Gf.Quatf(*orientation))


def collect_cameras(stage):
    cams = []
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Camera):
            cams.append(str(prim.GetPath()))
    return cams


def create_fallback_camera(stage, prim_path="/World/FallbackCamera"):
    camera = UsdGeom.Camera.Define(stage, prim_path)
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.AddTranslateOp().Set(Gf.Vec3d(2.5, -2.0, 1.8))
    xform.AddRotateXYZOp().Set(Gf.Vec3f(65.0, 0.0, 35.0))
    return prim_path


def build_simple_scene(stage):
    cube = UsdGeom.Cube.Define(stage, "/World/DebugCube")
    cube.GetSizeAttr().Set(0.5)
    cube_xf = UsdGeom.Xformable(cube.GetPrim())
    cube_xf.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.25))

    if not stage.GetPrimAtPath("/World/Light"):
        light = UsdLux.DomeLight.Define(stage, "/World/Light")
        light.CreateIntensityAttr(1500.0)


def pick_camera(camera_paths, preferred_prefix="/World/Orbbec"):
    rgb_candidates = [p for p in camera_paths if "rgb" in p.lower()]
    if rgb_candidates:
        for path in rgb_candidates:
            if path.startswith(preferred_prefix):
                return path
        return rgb_candidates[0]

    for path in camera_paths:
        if path.startswith(preferred_prefix):
            return path
    if camera_paths:
        return camera_paths[0]
    return ""


def main():
    if os.path.exists(DEBUG_LOG):
        os.remove(DEBUG_LOG)
    log("[capture] Script started")
    log(f"[capture] ORBBEC_USD={ORBBEC_USD}")
    log(f"[capture] headless={args.headless}")
    log(f"[capture] skip_orbbec_model={args.skip_orbbec_model}")

    if not args.skip_orbbec_model:
        ensure_exists(ORBBEC_USD)

    camera_translate = None
    camera_orient = None
    if args.camera_translate:
        camera_translate = parse_float_tuple(args.camera_translate, 3, "--camera-translate")
    if args.camera_orient:
        camera_orient = parse_float_tuple(args.camera_orient, 4, "--camera-orient")

    scene_usd = ""
    if args.scene_usd:
        scene_usd = args.scene_usd
        if not os.path.isabs(scene_usd):
            scene_usd = os.path.join(ROOT_DIR, scene_usd)
        ensure_exists(scene_usd)
        log(f"[capture] scene_usd={scene_usd}")

    ctx = omni.usd.get_context()
    ctx.new_stage()
    tick(20)
    stage = ctx.get_stage()

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))

    if scene_usd:
        scene_prim = stage.DefinePrim("/World/Scene", "Xform")
        scene_prim.GetReferences().AddReference(scene_usd)
        log("[capture] Scene referenced")
    else:
        build_simple_scene(stage)
        log("[capture] Built simple debug scene")

    if not args.skip_orbbec_model:
        orbbec_prim = stage.DefinePrim("/World/Orbbec", "Xform")
        orbbec_prim.GetReferences().AddReference(ORBBEC_USD)
        set_pose(orbbec_prim, translation=(0.0, 0.0, 1.6), orientation=(1.0, 0.0, 0.0, 0.0))
        log("[capture] Orbbec referenced")

    if not stage.GetPrimAtPath("/World/Light"):
        light = UsdLux.DomeLight.Define(stage, "/World/Light")
        light.CreateIntensityAttr(1000.0)

    tick(args.warmup)
    log(f"[capture] Warmup done: {args.warmup} frames")

    cameras = collect_cameras(stage)
    if not cameras:
        fallback = create_fallback_camera(stage)
        tick(10)
        cameras = collect_cameras(stage)
        log(f"[capture] No camera found in USD; created fallback camera: {fallback}")

    if args.list_cameras:
        log("[capture] Detected cameras:")
        for cam in cameras:
            log("  - " + cam)
        log("[capture] list-cameras mode done")
        return

    if args.camera_prim:
        camera_path = args.camera_prim
        if camera_path not in cameras:
            raise RuntimeError(f"Camera prim not found: {camera_path}\nDetected cameras:\n" + "\n".join(cameras))
    else:
        camera_path = pick_camera(cameras)

    log("[capture] Detected cameras:")
    for cam in cameras:
        log("  - " + cam)
    log("[capture] Using camera: " + camera_path)

    camera_prim = stage.GetPrimAtPath(camera_path)
    if camera_prim and (camera_translate is not None or camera_orient is not None):
        set_pose(camera_prim, translation=camera_translate, orientation=camera_orient)
        tick(30)
        log(f"[capture] Applied camera pose override: T={camera_translate}, Q={camera_orient}")

    rgb = None

    try:
        render_product = rep.create.render_product(camera_path, (args.width, args.height))
        rgb_annotator = rep.AnnotatorRegistry.get_annotator("rgb")
        rgb_annotator.attach([render_product])

        for _ in range(30):
            rep.orchestrator.step()
            data = rgb_annotator.get_data()
            if isinstance(data, np.ndarray) and data.ndim == 3 and data.shape[0] > 0:
                rgb = data
                break

        rgb_annotator.detach([render_product])
    except Exception as rep_err:
        log(f"[capture] Replicator path failed: {repr(rep_err)}")

    if rgb is None:
        camera = Camera(prim_path=camera_path, resolution=(args.width, args.height))
        camera.initialize()
        camera.add_rgb_to_frame()
        tick(60)
        frame = camera.get_current_frame()
        rgb = frame.get("rgb", None)

    if rgb is None:
        raise RuntimeError("Failed to fetch RGB frame from camera")

    if rgb.ndim != 3:
        raise RuntimeError(f"Unexpected RGB data shape: {getattr(rgb, 'shape', None)}")

    if rgb.shape[-1] == 4:
        rgb = rgb[:, :, :3]

    if args.post_exposure != 1.0 or args.post_gamma != 1.0:
        rgb_float = np.asarray(rgb, dtype=np.float32) / 255.0
        rgb_float = np.clip(rgb_float * float(args.post_exposure), 0.0, 1.0)
        gamma = max(float(args.post_gamma), 1e-6)
        rgb_float = np.power(rgb_float, gamma)
        rgb = np.clip(rgb_float * 255.0, 0.0, 255.0)
        log(f"[capture] Applied post process: exposure={args.post_exposure}, gamma={args.post_gamma}")

    rgb_u8 = np.asarray(rgb, dtype=np.uint8)
    out_path = os.path.join(ROOT_DIR, args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(rgb_u8).save(out_path)
    log(f"[capture] Saved RGB image -> {out_path}")


try:
    main()
except Exception as e:
    log(f"[capture] ERROR: {repr(e)}")
    raise
finally:
    log("[capture] Closing app")
    app.close()
