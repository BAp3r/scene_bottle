"""
load_gr2.py — Isaac Sim 5.1.0
加载 GR2 机器人到一个新 Stage，放在 flat ground 上。

运行：
    cd /home/baper/code/scene_bottle
    isaacsim load_gr2.py
"""

import os, sys

# ── 1. SimulationApp ───────────────────────────────────────────────────────
from isaacsim import SimulationApp
app = SimulationApp({"headless": False, "width": 1920, "height": 1080})
for _ in range(60):
    app.update()

# ── 2. 导入 ───────────────────────────────────────────────────────────────
import omni.usd
import omni.kit.commands
from pxr import Gf, Usd, UsdGeom, UsdLux, UsdPhysics, PhysxSchema, Sdf, UsdShade

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROBOT_USD  = os.path.join(SCRIPT_DIR, "usds",
                           "gr2v4_1_0_fourier_hand_6dof",
                           "gr2v4_1_0_fourier_hand_6dof.usd")
TABLE_USD  = os.path.join(SCRIPT_DIR, "usds", "thor_table.usd")
BOTTLE_USD = os.path.join(SCRIPT_DIR, "usds", "SM_BottleA.usd")

def tick(n=10):
    for _ in range(n):
        app.update()


def main():
    # ── 新 Stage ──────────────────────────────────────────────────────────
    ctx = omni.usd.get_context()
    ctx.new_stage()
    tick(40)
    stage = ctx.get_stage()

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
    tick()

    # ── Physics Scene ─────────────────────────────────────────────────────
    sp = stage.DefinePrim("/World/PhysicsScene", "PhysicsScene")
    ps = UsdPhysics.Scene(sp)
    ps.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    ps.CreateGravityMagnitudeAttr(9.81)
    px = PhysxSchema.PhysxSceneAPI.Apply(sp)
    px.CreateEnableCCDAttr(True)
    px.CreateEnableStabilizationAttr(True)
    px.CreateTimeStepsPerSecondAttr(120)
    tick()

    # ── Ground Plane ──────────────────────────────────────────────────────────
    # 用 PhysicsGroundPlane 实现无限静态碰撞平面 + 可视网格
    gp_root = stage.DefinePrim("/World/GroundPlane", "Xform")

    # 无限碰撞平面（PhysX Plane = Z 向上的无限静态面）
    gp_col = stage.DefinePrim("/World/GroundPlane/CollisionPlane", "Plane")
    UsdPhysics.CollisionAPI.Apply(gp_col).CreateCollisionEnabledAttr(True)
    # 物理材质
    gp_mat = stage.DefinePrim("/World/GroundPlane/PhysicsMaterial", "Material")
    gp_mat_api = UsdPhysics.MaterialAPI.Apply(gp_mat)
    gp_mat_api.CreateStaticFrictionAttr(0.5)
    gp_mat_api.CreateDynamicFrictionAttr(0.5)
    gp_mat_api.CreateRestitutionAttr(0.0)
    UsdShade.MaterialBindingAPI.Apply(gp_col).Bind(
        UsdShade.Material(gp_mat), UsdShade.Tokens.strongerThanDescendants, "physics")

    # 可视：用细分网格线模拟 flat grid 外观（灰色大平面）
    gp_vis = UsdGeom.Mesh.Define(stage, "/World/GroundPlane/VisualMesh")
    grid_size = 20    # 总尺寸（米）
    half = grid_size / 2.0
    gp_vis.CreatePointsAttr([
        Gf.Vec3f(-half, -half, 0), Gf.Vec3f( half, -half, 0),
        Gf.Vec3f( half,  half, 0), Gf.Vec3f(-half,  half, 0),
    ])
    gp_vis.CreateFaceVertexCountsAttr([4])
    gp_vis.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    gp_vis.CreateSubdivisionSchemeAttr("none")
    gp_vis.GetDisplayColorAttr().Set([Gf.Vec3f(0.35, 0.35, 0.35)])
    tick(10)

    # ── Lighting ──────────────────────────────────────────────────────────
    UsdLux.DomeLight.Define(stage, "/World/Lights/Dome").CreateIntensityAttr(1000)
    sun = UsdLux.DistantLight.Define(stage, "/World/Lights/Sun")
    sun.CreateIntensityAttr(3000)
    UsdGeom.Xformable(sun).AddRotateXYZOp().Set(Gf.Vec3f(-60, 0, 45))
    tick()

    # ── GR2 ───────────────────────────────────────────────────────────────
    # /World/GR2 是标准路径：
    #   /World 是 Isaac Sim 的场景根节点（必须是 default prim）
    #   /World/GR2 是机器人实例，GR2 原始 USD 的根 prim 会 merge 进来
    #   多个机器人时用 /World/GR2_0、/World/GR2_1 以此类推
    gr2 = stage.DefinePrim("/World/GR2", "Xform")
    gr2.GetReferences().AddReference(ROBOT_USD)
    tick(20)  # 等 reference 加载

    def set_transform(prim_path, translation, orientation):
        prim = stage.GetPrimAtPath(prim_path)
        xf = UsdGeom.Xformable(prim)
        ops = xf.GetOrderedXformOps()
        has_trans = any(op.GetOpName() == "xformOp:translate" for op in ops)
        has_rot = any(op.GetOpName() == "xformOp:orient" for op in ops)
        
        if has_trans:
            idx = [op.GetOpName() for op in ops].index("xformOp:translate")
            ops[idx].Set(Gf.Vec3d(*translation))
        else:
            xf.AddTranslateOp().Set(Gf.Vec3d(*translation))
            
        if has_rot:
            idx = [op.GetOpName() for op in ops].index("xformOp:orient")
            try:
                ops[idx].Set(Gf.Quatf(*orientation))
            except Exception:
                ops[idx].Set(Gf.Quatd(*orientation))
        else:
            xf.AddOrientOp(precision=UsdGeom.XformOp.PrecisionFloat).Set(Gf.Quatf(*orientation))
            
    # 根据包围盒检测结果: GR2 本地 Z 极小值为 -1.00m，所以将其提升 1.00m 恰好脚底贴地
    set_transform("/World/GR2", (0.0, 0.0, 1.00), (1.0, 0.0, 0.0, 0.0))
    tick(40)

    # ── Table ───────────────────────────────────────────────────────────────
    table = stage.DefinePrim("/World/Table", "Xform")
    table.GetReferences().AddReference(TABLE_USD)
    # 桌子本地 Z 极小值为 -0.79m，提升 0.79m 后底座接触地面，桌面处于绝对高度 0.79m 处
    set_transform("/World/Table", (0.6, 0.0, 0.79), (1.0, 0.0, 0.0, 0.0))
    tick(20)

    # 桌子作为静态碰撞体 (只有 Collision 无 RigidBody)
    for p in stage.TraverseAll():
        if p.GetPath().HasPrefix("/World/Table") and p.IsA(UsdGeom.Mesh):
            if not p.HasAPI(UsdPhysics.CollisionAPI):
                UsdPhysics.CollisionAPI.Apply(p)
            if not p.HasAPI(PhysxSchema.PhysxCollisionAPI):
                PhysxSchema.PhysxCollisionAPI.Apply(p)

    # ── Bottle ───────────────────────────────────────────────────────────────
    bottle = stage.DefinePrim("/World/Bottle", "Xform")
    bottle.GetReferences().AddReference(BOTTLE_USD)
    # 瓶子 Z 最低点就是 0.00m。既然桌面绝对高度为 0.79m，我们将瓶子设为 0.81m 即可让它离桌子 2cm 微小下落
    set_transform("/World/Bottle", (0.6, 0.0, 0.81), (1.0, 0.0, 0.0, 0.0))
    tick(20)

    # 瓶子作为动态刚体 (RigidBody + Collision)
    for p in stage.TraverseAll():
        if p.GetPath().HasPrefix("/World/Bottle") and p.IsA(UsdGeom.Mesh):
            if not p.HasAPI(UsdPhysics.CollisionAPI):
                UsdPhysics.CollisionAPI.Apply(p)
                col_api = PhysxSchema.PhysxCollisionAPI.Apply(p)
                # 明确指定为凸包(Convex Hull) 或者 凸分解(Convex Decomposition) 消除报错
                col_api.CreateRestOffsetAttr(0.0)
                
                # 手动给这个 Mesh 加上 mesh approximation 属性，设为 convexHull
                # 虽然 PhysxSchema 没有直接的高层python函数配置 approximation, 但可以用 GetPrim().CreateAttribute 强写
                attr = p.GetPrim().CreateAttribute("physxCollision:approximation", Sdf.ValueTypeNames.Token)
                attr.Set("convexHull")
    
    bottle_prim = stage.GetPrimAtPath("/World/Bottle")
    # 给外部根节点绑定刚体并估算质量
    if not bottle_prim.HasAPI(UsdPhysics.RigidBodyAPI):
        UsdPhysics.RigidBodyAPI.Apply(bottle_prim)
        PhysxSchema.PhysxRigidBodyAPI.Apply(bottle_prim)
        # 补加刚体质量/密度让它受到有效重力
        mass_api = UsdPhysics.MassAPI.Apply(bottle_prim)
        mass_api.CreateDensityAttr(1000.0)
    
    # 强制仿真步骤应用上述物理属性
    tick(40)

    # ── 视口相机 ──────────────────────────────────────────────────────────
    try:
        from omni.kit.viewport.utility import get_active_viewport
        vp = get_active_viewport()
        if vp:
            vp.set_camera_position("/OmniverseKit_Persp",
                                    Gf.Vec3d(3.0, -3.0, 2.0), True)
            vp.set_camera_target("/OmniverseKit_Persp",
                                  Gf.Vec3d(0, 0, 0.8), True)
    except Exception:
        pass
    tick(60)

    print("\n" + "="*50)
    print("  GR2 loaded on flat ground.")
    print("  Press Play to test physics.")
    print("="*50 + "\n")

    # ── 导出独立 USD（Flatten，不依赖外部引用）────────────────────────────
    output_path = os.path.join(SCRIPT_DIR, "gr2_standalone.usd")
    flat_stage = stage.Flatten()
    flat_stage.Export(output_path)
    print(f"[setup] ✅  Standalone USD saved → {output_path}")
    print(f"[setup]    (This file contains all geometry/materials, no external refs)")


main()

while app.is_running():
    app.update()
app.close()
