"""
setup_scene.py
在 Isaac Sim GUI 中搭建场景：桌子 + 水瓶 + GR2 机器人
检查物理属性后按 Ctrl+S 或调用 save_scene() 保存为 USD。

运行方式（Isaac Sim Python 环境内）：
    isaacsim --headless=False path/to/setup_scene.py
或直接在 Isaac Sim 的 Script Editor 里粘贴运行。
"""

from isaacsim import SimulationApp

# ── 启动 Isaac Sim（GUI 模式）──────────────────────────────────────────────────
simulation_app = SimulationApp({"headless": False, "width": 1920, "height": 1080})

# ── 标准导入（必须等 SimulationApp 初始化后）──────────────────────────────────
import os
import carb
import omni.usd
import omni.kit.commands
from pxr import Gf, UsdLux, UsdPhysics, PhysxSchema, Usd, UsdGeom, Sdf

# ── 路径配置 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
TABLE_USD     = os.path.join(SCRIPT_DIR, "usds", "thor_table.usd")
BOTTLE_USD    = os.path.join(SCRIPT_DIR, "usds", "SM_BottleA.usd")
ROBOT_USD     = os.path.join(SCRIPT_DIR, "usds",
                              "gr2v4_1_0_fourier_hand_6dof",
                              "gr2v4_1_0_fourier_hand_6dof.usd")
OUTPUT_USD    = os.path.join(SCRIPT_DIR, "scene_grasp.usd")

# ── 场景布局参数（可按实际模型尺寸调整）─────────────────────────────────────
TABLE_POS     = Gf.Vec3d(0.0,  0.0,  0.0)      # 桌子原点
BOTTLE_POS    = Gf.Vec3d(0.0, -0.15, 0.80)     # 瓶子放桌面（Z≈桌高）
ROBOT_POS     = Gf.Vec3d(0.0,  0.80, 0.0)      # GR2 站桌子对面
ROBOT_ORIENT  = Gf.Quatd(0.7071, 0.0, 0.0, 0.7071)  # 转向桌子（绕 Z 180°)

BOTTLE_MASS   = 0.5      # kg
BOTTLE_STATIC_FRICTION  = 0.6
BOTTLE_DYNAMIC_FRICTION = 0.4
BOTTLE_RESTITUTION      = 0.1


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def get_stage() -> Usd.Stage:
    return omni.usd.get_context().get_stage()


def add_reference(prim_path: str, usd_file: str, pos: Gf.Vec3d,
                  orient: Gf.Quatd = None, scale: Gf.Vec3d = None) -> Usd.Prim:
    """在 stage 里添加 USD 引用并设置 xform。"""
    stage = get_stage()
    prim = stage.DefinePrim(prim_path, "Xform")
    prim.GetReferences().AddReference(usd_file)

    xform = UsdGeom.Xformable(prim)
    xform.ClearXformOpOrder()

    xform.AddTranslateOp().Set(pos)
    if orient is not None:
        xform.AddOrientOp().Set(orient)
    else:
        xform.AddOrientOp().Set(Gf.Quatd(1, 0, 0, 0))
    if scale is not None:
        xform.AddScaleOp().Set(scale)

    print(f"[setup_scene] Added: {prim_path}  @  {pos}")
    return prim


def setup_physics_material(stage: Usd.Stage, mat_path: str,
                            static_friction: float, dynamic_friction: float,
                            restitution: float) -> Sdf.Path:
    """创建物理材质并返回路径。"""
    mat = UsdPhysics.MaterialAPI.Apply(stage.DefinePrim(mat_path, "Material"))
    mat.CreateStaticFrictionAttr(static_friction)
    mat.CreateDynamicFrictionAttr(dynamic_friction)
    mat.CreateRestitutionAttr(restitution)
    return Sdf.Path(mat_path)


def setup_bottle_physics(prim: Usd.Prim, mat_path: Sdf.Path):
    """给瓶子添加 RigidBody + Collider + Mass + 物理材质绑定。"""
    # Rigid Body
    rb = UsdPhysics.RigidBodyAPI.Apply(prim)
    rb.CreateRigidBodyEnabledAttr(True)

    # Mass
    mass_api = UsdPhysics.MassAPI.Apply(prim)
    mass_api.CreateMassAttr(BOTTLE_MASS)
    mass_api.CreateCenterOfMassAttr(Gf.Vec3f(0, 0, 0))

    # Collider（使用 convexDecomposition 更稳定）
    col = UsdPhysics.CollisionAPI.Apply(prim)
    col.CreateCollisionEnabledAttr(True)
    mesh_col = PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(prim)

    # 绑定物理材质
    binding = UsdPhysics.MaterialBindingAPI.Apply(prim)
    binding.Bind(get_stage().GetPrimAtPath(mat_path),
                 UsdPhysics.Tokens.strongerThanDescendants,
                 "physics")

    # PhysX 额外参数
    physx_rb = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
    physx_rb.CreateSleepThresholdAttr(0.005)
    physx_rb.CreateStabilizationThresholdAttr(0.001)

    print(f"[setup_scene] Bottle physics applied: mass={BOTTLE_MASS}kg, "
          f"friction={BOTTLE_STATIC_FRICTION}/{BOTTLE_DYNAMIC_FRICTION}")


def setup_table_collider(prim: Usd.Prim):
    """给桌子所有 Mesh 子 prim 添加静态碰撞体。"""
    stage = get_stage()
    count = 0
    for child in Usd.PrimRange(prim):
        if child.GetTypeName() in ("Mesh", "Cube", "Cylinder", "Cone", "Sphere"):
            if not UsdPhysics.CollisionAPI(child):
                col = UsdPhysics.CollisionAPI.Apply(child)
                col.CreateCollisionEnabledAttr(True)
                count += 1
    print(f"[setup_scene] Table: applied collider to {count} mesh(es)")


def setup_physics_scene(stage: Usd.Stage):
    """添加 Physics Scene 和地面。"""
    # Physics Scene
    scene_path = "/World/PhysicsScene"
    if not stage.GetPrimAtPath(scene_path):
        scene = UsdPhysics.Scene.Define(stage, scene_path)
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        scene.CreateGravityMagnitudeAttr(9.81)

    # PhysX Scene 参数
    physx_scene = PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath(scene_path))
    physx_scene.CreateEnableCCDAttr(True)          # 连续碰撞检测，防止穿透
    physx_scene.CreateEnableStabilizationAttr(True)
    physx_scene.CreateTimeStepsPerSecondAttr(120)  # 120Hz 物理步

    # 地面
    ground_path = "/World/GroundPlane"
    if not stage.GetPrimAtPath(ground_path):
        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=stage,
            planePath=ground_path,
            axis="Z",
            size=10.0,
            position=Gf.Vec3f(0, 0, 0),
            color=Gf.Vec3f(0.3, 0.3, 0.3),
        )
    print("[setup_scene] Physics scene created (gravity=9.81, 120Hz, CCD=on)")


def add_lighting(stage: Usd.Stage):
    """添加基础光照。"""
    dome_path = "/World/Lights/DomeLight"
    if not stage.GetPrimAtPath(dome_path):
        dome = UsdLux.DomeLight.Define(stage, dome_path)
        dome.CreateIntensityAttr(1000.0)

    distant_path = "/World/Lights/DistantLight"
    if not stage.GetPrimAtPath(distant_path):
        dlight = UsdLux.DistantLight.Define(stage, distant_path)
        dlight.CreateIntensityAttr(3000.0)
        UsdGeom.Xformable(dlight).AddRotateXYZOp().Set(Gf.Vec3f(-45, 0, 45))
    print("[setup_scene] Lighting added")


def save_scene(output_path: str = OUTPUT_USD):
    """将当前 Stage 导出为 Flatten USD（可独立打开，不依赖外部引用）。"""
    stage = get_stage()
    stage.Export(output_path)
    print(f"\n[setup_scene] ✅ Scene saved -> {output_path}\n")


# ─────────────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────────────

def main():
    stage = get_stage()

    # 1. 设置上轴和单位
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)   # 1 unit = 1 metre

    # 2. 创建 /World 根节点
    if not stage.GetPrimAtPath("/World"):
        stage.DefinePrim("/World", "Xform")

    # 3. 物理场景 + 光照
    setup_physics_scene(stage)
    add_lighting(stage)

    # 4. 加载资产
    table_prim  = add_reference("/World/Table",  TABLE_USD,  TABLE_POS)
    bottle_prim = add_reference("/World/Bottle", BOTTLE_USD, BOTTLE_POS)
    robot_prim  = add_reference("/World/GR2",    ROBOT_USD,  ROBOT_POS, ROBOT_ORIENT)

    # 5. 物理材质（放在 /World/PhysicsMaterials/）
    mat_path = setup_physics_material(
        stage,
        "/World/PhysicsMaterials/BottleMaterial",
        BOTTLE_STATIC_FRICTION,
        BOTTLE_DYNAMIC_FRICTION,
        BOTTLE_RESTITUTION,
    )

    # 6. 应用物理属性
    setup_table_collider(table_prim)
    setup_bottle_physics(bottle_prim, mat_path)
    # GR2 已是 Articulation USD，不需要额外处理

    # 7. 保存 live layer（这里的 stage 是 in-memory 的，先写磁盘留一份）
    save_scene(OUTPUT_USD)

    print("\n" + "="*60)
    print("  场景已就绪，请在 GUI 中检查以下内容：")
    print("  1. 瓶子是否在桌面上方（Z≈0.80），可拖动调整 BOTTLE_POS")
    print("  2. GR2 是否面朝桌子，可调整 ROBOT_POS / ROBOT_ORIENT")
    print("  3. Physics Inspector: 右键 Bottle prim -> Physics -> Rigid Body")
    print("  4. 按 Play 检查瓶子是否稳定落在桌面（不穿透/不飞走）")
    print("  5. 确认后，在脚本末尾或 Script Editor 调用:")
    print("     from setup_scene import save_scene; save_scene()")
    print("  或直接 File > Save / Ctrl+S 保存 live layer")
    print("="*60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────
main()

# 保持 GUI 运行，等待用户检查
while simulation_app.is_running():
    simulation_app.update()

simulation_app.close()

