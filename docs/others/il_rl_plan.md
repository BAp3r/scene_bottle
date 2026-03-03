# 灵巧手抓取任务：从模仿学习(IL)到强化学习(RL)开发计划

基于与傅里叶研发沟通的建议，结合你的团队目前正在使用的 `LeRobot` 框架，以及官方主推的 `IsaacLab`，我们将采取**“以 IsaacLab 为仿真与采集基座，以 LeRobot 为策略训练端”**的混合开发路线。

傅里叶给出的建议 1（使用 IsaacLab 自带遥操作 pipeline）是目前业界的**绝对最佳实践**。建议 2（基于底层 Isaac Sim 手搓全套 VR、状态机）开发周期极长，只有在特殊的非标传感硬件下才需要。既然 IsaacLab 已内置了完善的设备流，我们应果断采用方案 1。

下面是为您量身定制的完整开发落地计划：

---

## 核心技术栈定位
*   **仿真基座 (Environment)**: `IsaacLab` (通过资产配置系统加载我们刚才做的 GR2 和瓶子)。
*   **遥操作与前端采集 (Teleop & Data Collection)**: `IsaacLab` 内置的 `se3_keyboard` / `spacemouse` / `gamepad` 遥操作模块（VR 作为后续进阶接入）。
*   **模仿学习与策略网络 (Imitation Learning)**: `LeRobot` (HuggingFace生态，支持 Diffusion Policy、ACT 等前沿算法)。
*   **数据桥梁 (Data Pipeline)**: 编写采集转换器，将 IsaacLab 的 `Dict` 数据保存为 LeRobot 原生支持的 HuggingFace Dataset (`.zarr` / `.hdf5` 格式)。

---

## 详细阶段执行计划

### 阶段一：将场景迁移封装为 IsaacLab 环境 (RL/IL Env)
我们目前拥有的是基于纯 Isaac Sim 脚本的静态环境。接下来的第一步，是把它装进一个标准的 Gym 强化学习/采集容器中。
1.  **新建环境类**: 继承 `IsaacLab` 的 `ManagerBasedRLEnv` 或 `DirectRLEnv`。
2.  **资产配置 (Cfg)**:
    *   将 `gr2_standalone.usd` 中验证过物理属性的 GR2 模型导出为 `ArticulationCfg`，并为其配置 PD 控制器参数（为各个关节指定 stiffness 和 damping）。
    *   将瓶子配为 `RigidObjectCfg`，并跟踪其空间 6D Pose。
3.  **定义动作空间 (Action Space)**:
    *   **手臂控制**: 引入 IsaacLab 的逆运动学控制器 (`DifferentialIK`)，将动作空间抽象为末端执行器 (6DoF) 位置增量，而非艰难地直接控制全臂关节。
    *   **灵巧手控制**: 将手指关节阵列作为直接的位置输入映射 (`JointPosition` Action)。
4.  **定义观测空间 (Observation Space)**:
    *   配置传感器：在 GR2 头部/手腕添加相机，输出 RGB + Depth。
    *   状态输出：记录机械臂末端姿态、手指关节角、瓶子姿态。

### 阶段二：遥操作适配与轨迹录制 (Teleoperation & Collection)
在此阶段，人类专家登场接管机器人，提供“什么是对的数据”。
1.  **接入遥操作设备**:
    *   *初期验证*: 先使用 IsaacLab 开箱即用的键盘/鼠标、或是 3D 鼠标 (SpaceMouse) 映射末端的 6DoF 运动。
    *   *按键映射*: 定义夹爪/灵巧手的抓取与释放为特定的按键宏 (比如按下空格键，五指闭合)。
    *   *(可选) 后期VR增强*: 通过通过 OpenXR 获取 VR 设备的位姿，做 Retargeting 将真人的骨骼映射到灵巧手。
2.  **编写数据采集状态机**:
    *   基于 IsaacLab 的 `RobomimicDataCollector` 或写一个定制的 Python 收集器。
    *   定义录制帧率 (如 30 FPS 或 50 FPS)。
    *   状态管理：按下按键开始录制轨迹 ——> 执行抓取 ——> 松开按键保存一条 Episode 数据 (Done)。
3.  **生成基准数据集**: 亲手遥控机器人抓起瓶子，录制 50 - 100 条成功的示范轨迹 (`Demonstrations`)。

### 阶段三：数据转换与 LeRobot 训练 (Imitation Learning)
将人类专家的直觉“教”给神经网络。
1.  **向 LeRobot 数据集对齐**:
    *   LeRobot 预期的标准格式是统一的 HF Dataset。我们需要写一个 `isaaclab_to_lerobot.py` 数据处理脚本。
    *   将我们前面收集的：`[obs: 相机RGB, obs: 当前末端姿态, action: 人类专家下一帧给出的增量姿态]` 打包打包转化为 `.parquet` 或 `.zarr` 硬盘格式。
2.  **配置 IL 算法**:
    *   在 LeRobot 中选取前沿算法。抓取任务目前最成功的是 **ACT (Action Chunking with Transformers)** 或者 **Diffusion Policy (扩散模型策略)**。
    *   将整理好的本地 Dataset 喂入 LeRobot 开始训练 (Train)。
3.  **闭环评估 (Eval)**:
    *   训练完后，把生成的 `.pth/safetensors` 模型权重提出来。
    *   回到 IsaacLab 环境中，每帧调用 LeRobot 提供动作。观察机器人在没有人类遥控下，能不能自主地伸手抓向瓶子。

### 阶段四：冷启动后的强化学习微调 (RL Fine-tuning)
模仿学习的缺点是稍微偏离录制过的轨迹就容易崩溃（分布极移），此时需要利用 RL 去无监督探索。
1.  **设定期望奖励 (Reward Design)**:
    *   *靠近奖励*: 手到瓶子的距离越近得分越高。
    *   *触碰奖励*: 手指接触到了瓶子。
    *   *抓取奖励*: 瓶子的 Z 轴被抬高了超过 5 厘米且维持稳定。
2.  **导入策略冷启动 (Cold Start)**:
    *   将刚刚由 LeRobot 训练出来的 Actor 网络参数作为 RL 算法 (如 PPO, SAC) 的初始化权重。
3.  **并行探索 (Parallel Training)**:
    *   利用 IsaacSim 强大的 GPU 算力，同时克隆 1024 / 4096 个桌子和机器人的环境 (`env_spacing`)。
    *   进行大规模并行试错。因为有了模仿学习作为“冷启动”，模型一开始就知道“手应该伸向瓶子”，从而极大缓解了 RL 第一阶段庞大而漫无目的的乱碰期，使得收敛速度飙升。

---

## 我们接下来的首要行动项

在明白上述蓝图后，我们手头的下一行代码任务是**“阶段一”**：从直接加载 USD（当前我们写的 `load_gr2.py`）转向**采用 IsaacLab 的 `InteractiveSceneCfg` 系统去注册我们的机器人和物体**。

**行动建议**：
1. 确认 IsaacLab 是否已经在你的 `env_isaaclab` 环境下安装好，并且能成功 import（如 `import omni.isaac.lab`）。
2. 在 `scene_bottle` 下建一个新脚本 `gr2_env_cfg.py` 去定义 GR2 机器人的 Articulation 配置和 桌子瓶子的 RigidObject 配置。你会希望我先写哪一部分？
---

### 2026-03-03 更新：当前进度与执行方案
1. **当前状态**：官方 Franka 的 teleop 遥操作已在本地完全跑通。我们明确了 IsaacLab `omni` 包的导入必须依赖 `./isaaclab.sh -p`。
2. **马上要写的代码**：我们将暂时搁置深挖底层的 Mimic 算法逻辑。当务之急是把 GR2 从独立的 USD 变成一个 **符合 IsaacLab 规范的任务环境 (Task Registry)**。
3. **下一步执行计划**：
   - 创建 `gr2_asset.py`，对接 GR2 的关节驱动 (ArticulationCfg)。
   - 创建 `gr2_env_cfg.py`，拼凑桌子、瓶子与 GR2，挂载 IK 控制器 (InteractiveSceneCfg)。
   - 创建自定义 `teleop_gr2.py` 进行遥操作录制 (HDF5 数据集)。
