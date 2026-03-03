# Isaac Sim 场景搭建与 RL 训练准备进度

## 📌 当前总目标
创建一个可用于强化学习（RL）训练的抓取场景。
任务描述：利用人形机器人 GR2 的灵巧手，抓取放置在桌面上的水瓶。目前具备的资产：
- 机器人模型：GR2 (`gr2v4_1_0_fourier_hand_6dof.usd` 等分层结构文件)
- 桌面模型：Thor Table (`thor_table.usd`)
- 抓取物：水瓶 (`SM_BottleA.usd`)

---

## ✅ 已完成工作

1. **工作流环境跑通**
   - 验证了通过 `python` 独立运行 `SimulationApp` 脚本的方式（避免与 GUI 直接启动发生进程冲突）。
2. **场景资产实例化（USD 原生编程）**
   - 采用纯 `pxr` (OpenUSD) 原生 API 取代部分易引发版本报错的 Isaac Sim 封装件。
   - 手写了包含可视化网格（Mesh）及无限大物理碰撞平面（PhysX Plane）的**标准化地面**。
   - 设置好了包含重力（9.81m/s²）的物理场景 `PhysicsScene` 和光源。
3. **资产导入及物理验证**
   - 将 GR2 放置于标准路径 `/World/GR2` 下，理解了其主 USD 对 `configuration/` 目录下 `_base`, `_physics`, `_robot`, `_sensor` 文件的**自动 Sublayer 组装机制**。
   - 修复了因为资产内置精度（float）和 Isaac Sim 脚本默认设值（double）导致的 `xformOp:orient` **旋转精度报错**。
   - 修复了材质绑定库报错，纠正了 `UsdPhysics` 与 `UsdShade.MaterialBindingAPI` 之间的混淆。
4. **场景的持久化保存**
   - **引用保存模式 (6.7KB)**：掌握 `AddReference()`，仅保存修改路径的快捷方式。
   - **完全独立保存模式 (大体积)**：使用 `stage.Flatten().Export()` 压平节点树，导出了完全不依赖原有 `usds` 目录的 `gr2_standalone.usd` 文件备用。

---

## 🚀 下一步计划

1. **完整整合三个物体并调参**
   - 利用当前跑通的底层 API，将 `thor_table` 和 `SM_BottleA` 一并加入现有的 `load_gr2.py`。
   - 调整三者的空间位置、确保机器人手部和水瓶在交互区域。
   - 给瓶子加上 `ConvexDecomposition` 碰撞体及其物理参数。
2. **构建强化学习环境（Isaac Lab 架构）**
   - 使用 `EnvCfg` 完成多环境（`num_envs = 64/512`）克隆阵列（Cloner）。
   - 域随机化（Domain Randomization）：加入物体质量随机、摩擦力随机、末端微小位姿随机以增强鲁棒性。
3. **设计奖励函数**
   - 奖励 1: 手眼距离接近反馈（Distance Reward）。
   - 奖励 2: 接触判定与平稳度（Contact & Stability Reward）。
   - 奖励 3: 高度抬升最终奖励（Success Reward）。
4. **连接算法训练**
   - 接入 RL 算法接口（例如 PPO）跑通第一波闭环训练流程。
## 阶段三：物体相对坐标微调与物理刚体注入
**时间**: 2026-02-28
**状态**: ✅ 完成
**工作内容**:
1. **解决物体陷入地面的问题**: 分析原点坐标系特征（发现 GR2、桌子、瓶子原始文件的原点在几何中心），通过全局 `Z` 轴动态提升进行修复。
   * GR2：提升至 Z = 0.98m
   * Table：提升至 Z = 0.42m
   * Bottle：放置在桌面上方 Z = 0.90m
2. **纯 USD 开发范式的物理属性重绑定**:
   * **桌子 (Table)**: 遍历下属 Mesh 赋予 `UsdPhysics.CollisionAPI`，确立为静态受力碰撞体，避免坠落并可以自然承托物体。
   * **瓶子 (Bottle)**: 赋予 `UsdPhysics.RigidBodyAPI` 将其设为动态刚体，补充质量属性和密度 `1000.0`，受重力影响自然下落。
   * **机器人 (GR2)**: 识别了内部 `ArticulationRoot` 并修复了嵌套（Nested roots）导致的引擎警告，使其受物理规则管理。
3. **验证结果**: 最终执行 `python load_gr2.py` 输出的 `gr2_standalone.usd` 文件导入图形界面后，点击运行能正确产生物理重力表现（瓶子受重力掉下并砸在桌面上）。

## 阶段四：通过 Bounding Box 包围盒数据进行数学级对齐与物理现象解析
**时间**: 2026-02-28
**状态**: ✅ 完成
**工作内容**:
1. **坐标系精准对缝**: 利用 `UsdGeom.BBoxCache` 测出了各资产最原生的 Local Min/Max Z值。并重新应用到场景拼接中：
   * `GR2`: `Min Z = -1.00`，我们设置全局偏移 Z=1.00，让脚底贴地无缝。
   * `Table`: `Min Z = -0.79`，最大表面为 0，设置全局偏移 Z=0.79。
   * `Bottle`: `Min Z = 0.00`，设置全局偏移 Z=0.81（放于 0.79 的桌面上且留 2 厘米微缝防止初态穿模）。
2. **分析碰撞挤出力现象**: 解答了为何点击Play时陷在地面里的脚会被自动“抽出来”。（PhysX物理引擎会在第一帧检测重叠，然后根据穿透深度施加一个极大的排斥力强制解算分离）。
3. **确认机器人的固定根 (Fixed Base)**: 分析了具有庞大刚体树 (55 刚体) 的 GR2 为何“点击Play不掉落”。由于这是为了抓取训练或者由于默认缺少 PD 控制器（为防止其像布娃娃一样瞬间瘫软在地），机器人的根节点 (Root) 往往会被通过 `physxArticulation:fixBase` 绑定在世界坐标上成为固定基座。

## 阶段五：碰撞逼近与无关紧要的引擎警告排查
**时间**: 2026-02-28
**状态**: ✅ 完成
**工作内容**:
1. **排查动态刚体报错**: 针对在控制台反复出现的 `triangle mesh collision ... cannot be a part of a dynamic body` 警告进行了分析。
2. **确认不影响 RL 训练**: 虽然原始 `SM_BottleA.usd` 内部带有了强制的 Triangle 属性，我们用 Python 覆盖 `physxCollision:approximation` 也无法完全根除其初始时刻的警告文本，但是由于 PhysX 的保护机制，它已经成功被底层的自动 Fallback 转换成了轻量、合法的 `convexHull`（凸包体）。
3. **结论**: 记录进 `learned.md`，这个红字仅仅是一个提醒，绝不会干扰任何物理碰撞表现和后端抓取控制，可以直接无视。我们的初始环境搭建工作全部宣告竣工。
