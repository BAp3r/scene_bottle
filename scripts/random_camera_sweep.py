"""
random_camera_sweep.py

通过多次调用 capture_rgb_offline.py（每次独立启动 Isaac Sim）
进行随机机位采样、抓图、评分和排序。

优点：复用已验证稳定的抓图链路，避免同进程移动离线相机资产导致空帧。
"""

import argparse
import csv
import os
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageStat


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CAPTURE_SCRIPT = os.path.join(ROOT_DIR, "scripts", "capture_rgb_offline.py")


def parse_args():
    parser = argparse.ArgumentParser(description="Random camera pose sweep via subprocess capture")
    parser.add_argument("--scene-usd", type=str, required=True)
    parser.add_argument("--camera-prim", type=str, default="/World/Orbbec/camera_rgb/Camera_rgb")
    parser.add_argument("--num-samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup", type=int, default=240)

    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--headless", action="store_true")

    parser.add_argument("--tx-range", type=str, default="-1.2,1.2")
    parser.add_argument("--ty-range", type=str, default="-1.2,1.2")
    parser.add_argument("--tz-range", type=str, default="-0.2,0.6")

    parser.add_argument("--qwxyz", type=str, default="1.0,0.0,0.0,0.0", help="Camera orientation as w,x,y,z")

    parser.add_argument("--post-exposure", type=float, default=2.0)
    parser.add_argument("--post-gamma", type=float, default=0.85)

    parser.add_argument("--output-dir", type=str, default="outputs/rgb/sweep_subproc")
    return parser.parse_args()


def parse_range(raw, name):
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    if len(parts) != 2:
        raise ValueError(f"{name} must be min,max")
    lo, hi = float(parts[0]), float(parts[1])
    return (lo, hi) if lo <= hi else (hi, lo)


def parse_tuple(raw, n, name):
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    if len(parts) != n:
        raise ValueError(f"{name} must contain {n} values")
    return tuple(float(x) for x in parts)


def score_image(path):
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)

    luma = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    mean_luma = float(luma.mean())

    dx = np.abs(np.diff(luma, axis=1)).mean()
    dy = np.abs(np.diff(luma, axis=0)).mean()
    edge = float((dx + dy) * 0.5)

    brightness_term = 1.0 - min(abs(mean_luma - 110.0) / 110.0, 1.0)
    texture_term = min(edge / 12.0, 1.0)
    score = 0.55 * brightness_term + 0.45 * texture_term

    stat = ImageStat.Stat(img)
    return score, mean_luma, edge, stat.extrema


def main():
    args = parse_args()
    random.seed(args.seed)

    scene_usd = args.scene_usd if os.path.isabs(args.scene_usd) else os.path.join(ROOT_DIR, args.scene_usd)
    if not os.path.exists(scene_usd):
        raise FileNotFoundError(scene_usd)
    if not os.path.exists(CAPTURE_SCRIPT):
        raise FileNotFoundError(CAPTURE_SCRIPT)

    tx_range = parse_range(args.tx_range, "--tx-range")
    ty_range = parse_range(args.ty_range, "--ty-range")
    tz_range = parse_range(args.tz_range, "--tz-range")
    qwxyz = parse_tuple(args.qwxyz, 4, "--qwxyz")

    run_tag = time.strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(ROOT_DIR, args.output_dir, run_tag)
    os.makedirs(out_dir, exist_ok=True)

    log_path = os.path.join(out_dir, "sweep.log")
    csv_path = os.path.join(out_dir, "scores.csv")
    best_path = os.path.join(out_dir, "best_pose.txt")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(msg, flush=True)

    log(f"[sweep-subproc] scene={scene_usd}")
    log(f"[sweep-subproc] camera={args.camera_prim}")
    log(f"[sweep-subproc] samples={args.num_samples}, warmup={args.warmup}")

    records = []

    for i in range(args.num_samples):
        tx = random.uniform(tx_range[0], tx_range[1])
        ty = random.uniform(ty_range[0], ty_range[1])
        tz = random.uniform(tz_range[0], tz_range[1])

        sample_name = f"sample_{i:03d}.png"
        output_rel = os.path.join(args.output_dir, run_tag, sample_name)
        output_abs = os.path.join(ROOT_DIR, output_rel)

        cmd = [
            sys.executable,
            CAPTURE_SCRIPT,
            "--scene-usd",
            scene_usd,
            "--camera-prim",
            args.camera_prim,
            "--camera-translate",
            f"{tx:.6f},{ty:.6f},{tz:.6f}",
            "--camera-orient",
            f"{qwxyz[0]:.6f},{qwxyz[1]:.6f},{qwxyz[2]:.6f},{qwxyz[3]:.6f}",
            "--warmup",
            str(args.warmup),
            "--width",
            str(args.width),
            "--height",
            str(args.height),
            "--post-exposure",
            str(args.post_exposure),
            "--post-gamma",
            str(args.post_gamma),
            "--output",
            output_rel,
        ]
        if args.headless:
            cmd.append("--headless")

        try:
            subprocess.run(cmd, check=True, cwd=ROOT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            log(f"[sweep-subproc] sample {i:03d}: capture failed")
            continue

        if not os.path.exists(output_abs):
            log(f"[sweep-subproc] sample {i:03d}: output missing")
            continue

        score, mean_luma, edge, extrema = score_image(output_abs)
        records.append(
            {
                "idx": i,
                "path": output_abs,
                "score": score,
                "mean_luma": mean_luma,
                "edge": edge,
                "extrema": str(extrema),
                "tx": tx,
                "ty": ty,
                "tz": tz,
                "qw": qwxyz[0],
                "qx": qwxyz[1],
                "qy": qwxyz[2],
                "qz": qwxyz[3],
            }
        )
        log(f"[sweep-subproc] sample {i:03d}: score={score:.3f}, luma={mean_luma:.1f}, edge={edge:.2f}")

    if not records:
        raise RuntimeError("No valid samples captured")

    records.sort(key=lambda x: x["score"], reverse=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["idx", "path", "score", "mean_luma", "edge", "extrema", "tx", "ty", "tz", "qw", "qx", "qy", "qz"],
        )
        writer.writeheader()
        writer.writerows(records)

    best = records[0]
    with open(best_path, "w", encoding="utf-8") as f:
        f.write("Best camera pose from sweep_subproc\n")
        f.write(f"score: {best['score']:.4f}\n")
        f.write(f"image: {best['path']}\n")
        f.write(f"translation: {best['tx']:.6f},{best['ty']:.6f},{best['tz']:.6f}\n")
        f.write(f"orientation: {best['qw']:.6f},{best['qx']:.6f},{best['qy']:.6f},{best['qz']:.6f}\n")

    log(f"[sweep-subproc] done: valid={len(records)}")
    log(f"[sweep-subproc] csv -> {csv_path}")
    log(f"[sweep-subproc] best -> {best_path}")


if __name__ == "__main__":
    main()
