# Articulation Controller

## Overview

Articulation controller is the low level controller that controls joint position, joint velocity, and joint effort in Isaac Sim. The articulation controller can be interfaced using Python and Omnigraph.

Note

Angular units are expressed in radians while angles in USD are expressed in degrees and will be adjusted accordingly by the articulation controller.

## Python Interface

### Create the articulation controller

There are several ways to create the articulation controller. The articulation controller is usually created implicitly by applying articulation on a robot prim through the class. However, the articulation controller can be created directly by importing the controller class before the simulation starts, but this approach will require you to create or pass in the during initialization.`<span class="pre">SingleArticulation</span>``<span class="pre">Articulation</span>`

[X] Single Articulation> The snippet below will load and apply articulation on a franka robot.

> ```
> importisaacsim.core.utils.stageasstage_utils
> fromisaacsim.core.primsimport SingleArticulation
> usd_path = "/Path/To/Robots/FrankaRobotics/FrankaPanda/franka.usd"
> prim_path = "/World/envs/env_0/panda"
>
> # load the Franka Panda robot USD file
> stage_utils.add_reference_to_stage(usd_path, prim_path)
> # wrap the prim as an articulation
> prim = SingleArticulation(prim_path=prim_path, name="franka_panda")
> ```

[ ] Articulation Controller

### Initialize the controller

After the simulation is started, the robot articulation must be initialized before any commands can be passed to the robot.

[X] Single Articulation> The more common approach is by initializing the single articulation object that you have created earlier, this will initialize the articulation controller and articulation view stored in the SingleArticulation object

> ```
> prim.initialize()
> ```

[ ] Articulation Controller

### Articulation Action

Joint controls commands are packaged in objects first, before sending them to the articulation controller. The articulation controller allows you to specify the command joint postion, velocity and effort, as well as joint indicies of the joints actuated.`<span class="pre">ArticulationAction</span>`

If the joint indice is empty, the articulation action will assume the command will apply to all joints of the robot, and if any of the command is 0, articulation action will assume it is unactuated.

For example, the snippet below creates the command that closes the franka robot fingers: panda_finger_joint1 (7) and panda_finger_joint2 (8) to 0.0

```
importnumpyasnp
fromisaacsim.core.utils.typesimport ArticulationAction

action = ArticulationAction(joint_positions=np.array([0.0, 0.0]), joint_indices=np.array([7, 8]))
```

This snippet creates the command that moves all the robot joints to the indicated position

```
importnumpyasnp
fromisaacsim.core.utils.typesimport ArticulationAction

action = ArticulationAction(joint_positions=np.array([0.0, -1.0, 0.0, -2.2, 0.0, 2.4, 0.8, 0.04, 0.04]))
```

Important

Make sure the joint commands matches the order and the number of joint indices passed in to the articulation action. If joint indice is not passed in, make sure the command matches the number of joints in the robot.

Note

A joint can only be controlled by one control method. For example a joint cannot be controlled by both desired position and desired torque

### Apply Action

The function in both and classes will apply the you created earlier to the robot.`<span class="pre">apply_action</span>``<span class="pre">SingleArticulation</span>``<span class="pre">ArticulationController</span>``<span class="pre">ArticulationAction</span>`

[X] Single Articulation>

> ```
> prim.apply_action(action)
> ```

[ ] Articulation Controller

### Script Editor Example

You can try out basic articulation controller examples by running the following code snippets in the Script Editor. For more advanced usage, it is recommended to follow the [Core API Tutorial Series](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/index.html#isaac-sim-core-api-tutorials-page).

[X] Single Articulation>

> ```
> importnumpyasnp
> fromisaacsim.core.utils.stageimport add_reference_to_stage
> fromisaacsim.storage.nativeimport get_assets_root_path
> fromisaacsim.core.primsimport SingleArticulation
> fromisaacsim.core.utils.typesimport ArticulationAction
> fromisaacsim.core.api.worldimport World
> importasyncio
>
> async defrobot_control_example():
>     if World.instance():
>         World.instance().clear_instance()
>     world = World()
>     await world.initialize_simulation_context_async()
>     world.scene.add_default_ground_plane()
>
>     # Load the robot USD file
>     usd_path = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
>     prim_path = "/World/envs/env_0/panda"
>     add_reference_to_stage(usd_path, prim_path)
>
>     # Create SingleArticulation wrapper (automatically creates articulation controller)
>     robot = SingleArticulation(prim_path=prim_path, name="franka_panda")
>     await world.reset_async()
>
>     # Initialize the robot (initializes articulation controller internally)
>     robot.initialize()
>
>     # Run simulation
>     await world.play_async()
>
>     # Get current joint positions
>     current_positions = robot.get_joint_positions()
>     print(f"Current joint positions: {current_positions}")
>
>     # Create target positions
>     target_positions = np.array([0.0, -1.5, 0.0, -2.8, 0.0, 2.8, 1.2, 0.04, 0.04])
>
>     # Create and apply articulation action
>     action = ArticulationAction(joint_positions=target_positions)
>     robot.apply_action(action)
>
>     await asyncio.sleep(5.0)  # Run for 5 seconds to reach target positions
>
>     # Get current joint positions
>     current_positions = robot.get_joint_positions()
>     print(f"Current joint positions: {current_positions}")
>
>     world.pause()
>
> # Run the example
> asyncio.ensure_future(robot_control_example())
> ```

[ ] Articulation Controller

## Omnigraph Interface

The articulation controller can also be accessed through Omnigraph nodes, providing a visual, node-based approach to robot control.

### Input Parameters

The articulation controller Omnigraph node accepts the following input parameters:

**Articulation Controller Omnigraph Inputs**| Input Parameter | Description |
| - | - |
| ------------------------------------------------------------------------------------------------------------------------ |

| **execIn**          | Input execution trigger - connects to other nodes to control when the articulation controller runs |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| **targetPrim**      | The prim containing the robot articulation root. Leave empty if using robotPath                    |
| **robotPath**       | String path to the robot articulation root. Leave empty if using targetPrim                        |
| **jointIndices**    | Array of joint indices to control. Leave empty to control all joints or use jointNames             |
| **jointNames**      | Array of joint names to control. Leave empty to control all joints or use jointIndices             |
| **positionCommand** | Desired joint positions. Leave empty if not using position control                                 |
| **velocityCommand** | Desired joint velocities. Leave empty if not using velocity control                                |
| **effortCommand**   | Desired joint efforts/torques. Leave empty if not using effort control                             |

### Usage Guidelines

Important

 **Parameter Validation** : Ensure joint commands match the order and number of joint indices or joint names. If neither joint indices nor joint names are specified, the command must match the total number of joints in the robot.

Note

 **Control Method Limitation** : A joint can only be controlled by one method at a time. For example, a joint cannot be controlled by both position and effort commands simultaneously.

### Example Usage

For a complete example of the articulation controller Omnigraph node in action, see the asset in the Content Browser at Isaac Sim > Samples > Rigging > MockRobot > mock_robot_rigged.usd.`<span class="pre">mock_robot_rigged</span>`

[![Articulation Controller Omnigraph Node Example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_images/isim_4.5_base_ref_gui_rigging_mockrobot_controller.png)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_images/isim_4.5_base_ref_gui_rigging_mockrobot_controller.png)
