# Isaac Sim 开发与 OpenUSD 学习笔记

在配置 GR2 机器人场景时，积累了以下关键经验和踩坑记录：

---

## 1. 物理材质绑定的正确 API 
**问题**: 尝试把摩擦力材质绑定到碰撞体上时报错 `AttributeError: module 'pxr.UsdPhysics' has no attribute 'MaterialBindingAPI'`。
**原因与解法**: 
在较新的 OpenUSD 标准里，物理参数定义在 `UsdPhysics` 里（如 `UsdPhysics.MaterialAPI`），但**“将材质绑定到某个网格上”**这一动作受材质阴影系统的共同管理。必须调用 `pxr.UsdShade` 模块。
**正确范式**:
```python
from pxr import UsdPhysics, UsdShade

# 让该 Prim 变为一个"物理材质"
gp_mat_api = UsdPhysics.MaterialAPI.Apply(gp_mat_prim)
# 设置摩擦力等
gp_mat_api.CreateStaticFrictionAttr(0.5)

# ✨ 关键：用 UsdShade 进行绑定，并指定用途为 "physics"
UsdShade.MaterialBindingAPI.Apply(collider_prim).Bind(
    UsdShade.Material(gp_mat_prim), 
    UsdShade.Tokens.strongerThanDescendants, 
    "physics"   # 明确声明绑定为物理材质，而非视觉渲染材质
)
```

## 2. 位姿操作的精度冲突 (Precision Conflict)
**问题**: 在使用 Python 给机器人指定朝向时，抛出 `XformOp <...xformOp:orient> has typeName 'quatd' which does not match the requested precision 'PrecisionFloat'.`
**原因**: 别人做好的 USD 资产在内部定义方位时，可能采用的是单精度浮点（`float`，即 `Gf.Quatf`），当我们直接用 `AddOrientOp().Set(Gf.Quatd(...))` 给双精度（`double`）覆盖时会冲突。
**解法**: 做位姿操作时应先检查已有变换。
```python
xf = UsdGeom.Xformable(prim)
ops = [op.GetOpName() for op in xf.GetOrderedXformOps()]
# 对于已有的，利用 try-except 兼容类型，对没有的以 Float 注入
if "xformOp:orient" in ops:
    op = xf.GetOrderedXformOps()[ops.index("xformOp:orient")]
    try:
        op.Set(Gf.Quatf(1, 0, 0, 0))
    except:
        op.Set(Gf.Quatd(1, 0, 0, 0))
```

## 3. Reference vs Flatten 机制
这是 USD 框架中最核心的概念：
*   **按引用组装 (AddReference)**: 对 `A.usd` AddReference 到新场景 `C.usd` 时，保存 `C` 的结果只有几十 KB。这类似代码里的 `import` 或者快捷方式。它的优势在于：当底层资产（如机器人的 `configuration` 各路子文件）发生修改时，`C.usd` 打开时能**自动吃到最新变更**。这是推荐的模式。
*   **展平导出 (Flatten)**: 仅在需要对外分发、脱离原有工程文件夹时使用。通过 `stage.Flatten().Export("out.usd")`，引擎会沿着所有的引用路径把几何、材质数据**像解压缩一样拷贝到单个文件内**（会导致体积达到好几十MB及以上）。

## 4. 彻底抛弃封装，写原生的 Ground Plane
由于各种 Isaac Sim 版本的更新（如 5.1.x 开始 `omni.isaac.core.*` 大规模迁移/淘汰），与其调封装好的 `add_ground_plane` 因为路径找不到而闪退，不如直接调用底层 USD 撰写。
创建一个合格的无限地面需要 3 个 Prim：
1. **一个挂载点**: `/World/GroundPlane` (`Xform`)
2. **一个无限碰撞体**: `/World/GroundPlane/CollisionPlane` (`Plane` 类型 + `UsdPhysics.CollisionAPI`)
3. **一个虚拟网格用于显示**: `/World/GroundPlane/Visual` (`UsdGeom.Mesh` 画一个 20x20 的四边形)。

## 5. SimulationApp 的 Hydration 时延
通过 headless / 单独的 Python 脚本唤起 Isaac Sim 引擎本身是耗时过程，在实例化 `SimulationApp` 后，所有的插件加载和 `omni.usd` 上下文生成都是在后台异步建立的。
**铁律**: 在创建完 App 后，并进行任何关键操作前后，切记打上：
```python
for _ in range(60):
    app.update()
```
来给予渲染系统、物理系统“水合”反应时间。避免报出段错误或返回 None。
## 6. OpenUSD 里的刚体与碰撞（RigidBody & Collision API）
在按纯 USD 开发的范式下（不依赖老版本被弃用的 Isaac Sim 辅助函数），让一个静态视觉网格体拥有刚体与力学属性有其固定的套路：
*   **静态障碍物 (如桌子)**：它们不需要参与重力计算也不受力跌落，只要能够挡住东西即可。方法是递归其底下所有的视觉网格（`UsdGeom.Mesh`），通过 `UsdPhysics.CollisionAPI.Apply(prim)` 将这些网格包装为物理碰撞外壳。
*   **动态刚体 (如瓶子)**：在包含静态外壳（`CollisionAPI`）的基础上，额外需要在整个资产的**根物体或外层 Xform / Mesh** 上附加 `UsdPhysics.RigidBodyAPI.Apply(prim)`。
*   **质量生成**：默认刚体可能没有重量（无法正常受重力约束产生坠落动作），必须加上 `UsdPhysics.MassAPI.Apply(prim)`，并显式指定密度（例如 `mass_api.CreateDensityAttr(1000.0)`），物理引擎才能自动根据体积算出力学特性。
*   **Convex Hull (凸包) 回退**：对于那些非凸几何体的动态刚体，Isaac Sim PhysX 会由于“复杂三维网格碰撞开销大且无解”而在后台发出警告，自动退化成一个“包在网格外的简单凸形气球”来进行碰撞演算，除非你专门给它设为凸分解结构（Convex Decomposition）。

## 7. 机器人的 Articulation Root 坑
机器人（包括带很多关节的手、腿）本质上是一棵复杂的刚体力学树（Articulation Tree）。由于 Isaac Sim 的 PhysX 限制：一个连杆体系内，**只允许出现一个 `ArticulationRoot`（发音节点根）**。
若是重复用 Python 去 `UsdPhysics.ArticulationRootAPI.Apply(gr2_prim)` 包裹一个原来已经自带 Root 的 USD 文件，会导致 "Nested articulation roots are not allowed" 警告并使这一级物理规则崩溃失效。因此处理导入进来的第三方机器人资产时，务必要用 `if not prim.HasAPI(UsdPhysics.ArticulationRootAPI)` 检查。

## 8. Bounding Box 获取与精确场景拼接
直接肉眼猜高度容易出错，专业的场景摆放应该利用 `UsdGeom.BBoxCache` 查询本地几何极点（Min / Max 值）：
```python
bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
bounds = bbox_cache.ComputeWorldBound(root_prim).ComputeAlignedRange()
min_z, max_z = bounds.GetMin()[2], bounds.GetMax()[2]
```
凭借这个，可以对资产使用绝对偏移，使得它们的最低面（Min）能准确抵靠在其他物体的最高面（Max）上（比如瓶底放桌上）。

## 9. PhysX 的穿透解析机制 (Penetration Resolution)
在使用类似 Isaac Sim 的重物理场景时如果发现**“点击Play时模型会瞬间弹飞或者从中抽出来”**，不要惊讶。这是底层引擎（PhysX 等）的标准容错机制：
当两个刚体或者碰撞体的包围盒在时间 $t=0$ 时发生了空间上的重叠（Intersect/Penetrate），系统会在下一步进行一个能量极大的“碰撞解算”，用一个虚拟的反向排斥力硬生生将两者挤开。这提示我们要么预留安全空隙，要么关闭它们之间的碰撞层掩码。

## 10. 为何复杂机器人点击Play “不掉落”？（Fixed Base 机制）
如果一个由 50+ 个复杂刚体连杆通过 Articulation 相连的人形机器人不掉落，主要原因在于：
如果没有控制底层电机持续输出力矩（控制器的 PD 参数未介入），纯刚体机器人本该像关掉电源一样瞬间瘫软在一地（Ragdoll collapse）。
为了避免这种情况阻碍简单的上肢操纵强化学习任务，资产往往在根节点开启了 `physxArticulation:fixBase = True`（又或者建立了一个对世界 `/World` 的 FixedJoint），将机器人“钉”在了空间里让它能执行机械臂操作。未来做全场运动 (Locomotion) 训练时一定要解除这个固定钉。

## 11. 动态刚体的碰撞网格逼近限制 (Triangle Mesh vs Convex Hull)
**报错现象**:
当给复杂的 3D 模型（如带有凹面的瓶子 `SM_BottleA`）强加上 `RigidBodyAPI` (使其受重力成为动态物体) 但不指定碰撞逼近形式时，引擎会报出类似 `triangle mesh collision ... cannot be a part of a dynamic body, falling back to convexHull` 的 Error/Warning。

**原因**:
1. **纯三角形网格 (Triangle Mesh/None) 的物理计算开销呈指数级**: 如果两个布满孔洞、凹槽、几万个三角面的高模在天上相互碰撞翻滚，实时求解精确接触点的算力开销是现代 PC 无法承受的。
2. **PhysX 的铁律**: 纯 Triangle Mesh 仅能用于**静态物体 (Static Collider)**，比如地形、房屋、不受力移动的桌子。任何能满场乱飞的**动态刚体 (Dynamic Body)**，其形状必须经过简化 (Approximation)。
3. **引擎的智能回退 (Fallback)**: 当 Isaac Sim 发现一个动态物体没有配置简化模式，它为了保证不把电脑卡死，会自动将其降级 (Fallback) 到 **"Convex Hull" (凸包)** 模式。想象用一张保鲜膜把整个瓶子紧紧包裹起来，掩盖掉所有的内部孔洞和凹陷（比如杯口本来有洞，套上凸包后就成了实心的瓶盖），利用这个保鲜膜的外皮去算物理碰撞。

**解法**:
可以通过 USD 属性主动设定 `physxCollision:approximation` 为 `convexHull`（消除警告并且性能最好）或者 `convexDecomposition`（当网格凹陷非常关键，必须要能把东西丢进原本的洞口里时使用，物理引擎会用多个凸面的积木将它拼凑出来），而不要使用默认的 `none`。

**关于继续出现错误日志的补充记录**:
在通过代码强制赋值 `attr.Set("convexHull")` 后引擎依然在控制台抛出该报错，这通常是因为原始借用的 `SM_BottleA.usd` 文件自身内部的嵌套 Primitive 网格上被制作它的作者“硬编码 (Hardcoded)” 写入了三角形相关的属性信息，导致我们在最外层或其内部网格覆盖时没有彻底覆盖底层设定。
**这不影响任何结果！** 因为报错提示本身就是明确说明：“由于非法，底层的 PhysX 引擎**已经自动帮你 Fallback 到凸包了**”。相当于除了日志多一行红字，最终的运行时力学与结果是完全由凸包构成的，符合我们的强化学习预期。所以我们只需要放任该警告即可。

## 12. 离线相机 RGB 抓图阶段的关键坑点（Orbbec Gemini 335L）
**时间**: 2026-03-03

### 12.1 “为什么没有 GUI”
脚本若使用 `SimulationApp({"headless": True})`，终端会正常启动 Isaac Sim 内核，但不会弹出图形窗口。这不是失败，而是无界面模式。

### 12.2 `xformOp:orient` 精度冲突会导致流程中断
在给相机或其父节点设置姿态时，如果 USD 原属性是 `quatd` 而脚本写入 `quatf`（或反之），会触发类型冲突异常。
实践中应使用“兼容写法”：优先尝试 `Gf.Quatd`，失败后回退 `Gf.Quatf`。

### 12.3 白图 / 空帧并不一定是“没拍到”
我们遇到两种现象：
1. **均匀亮底图（近似全白）**：相机有输出，但场景内容或曝光/朝向不理想；
2. **空帧 shape=(0,)**：某些离线资产组合下，Replicator 或 Camera 路径可能拿到无效帧。

结论：需要“多路径抓图 + 参数化调机位 + 亮度后处理”三者结合，不能只依赖单一路径。

### 12.4 离线场景加载需要更长 warmup
在 `Office` 这类重资产场景里，短 warmup 会导致抓图时机过早，容易出现暗图、空帧或无效内容。
将 warmup 提高到 `240` 帧后，稳定性明显提升。

### 12.5 采图脚本应具备工程化能力
当前 `capture_rgb_offline.py` 已验证以下设计有效：
1. 可切换 `headless/GUI`；
2. 可指定离线场景 `--scene-usd`；
3. 可显式指定相机 prim（优先使用 `camera_rgb`）；
4. 可调相机位姿（`--camera-translate` / `--camera-orient`）；
5. 可做轻量图像后处理（`--post-exposure` / `--post-gamma`）；
6. 输出调试日志，便于定位“空帧/过暗/姿态错误”等问题。

### 12.6 当前结论
“拍到墙砖但偏暗”是一个有效中间里程碑：说明传感器链路已经打通，剩下的问题主要是机位和曝光策略，而不是资产加载或相机系统失效。
