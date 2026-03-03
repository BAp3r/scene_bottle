# Teleoperation and Imitation Learning with Isaac Lab Mimic

## Teleoperation

We provide interfaces for providing commands in SE(2) and SE(3) space for robot control. In case of SE(2) teleoperation, the returned command is the linear x-y velocity and yaw rate, while in SE(3), the returned command is a 6-D vector representing the change in pose.

Note

Presently, Isaac Lab Mimic is only supported in Linux.

To play inverse kinematics (IK) control with a keyboard device:

```
./isaaclab.sh-pscripts/environments/teleoperation/teleop_se3_agent.py--taskIsaac-Stack-Cube-Franka-IK-Rel-v0--num_envs1--teleop_devicekeyboard
```

For smoother operation and off-axis operation, we recommend using a SpaceMouse as the input device. Providing smoother demonstrations will make it easier for the policy to clone the behavior. To use a SpaceMouse, simply change the teleop device accordingly:

```
./isaaclab.sh-pscripts/environments/teleoperation/teleop_se3_agent.py--taskIsaac-Stack-Cube-Franka-IK-Rel-v0--num_envs1--teleop_devicespacemouse
```

Note

If the SpaceMouse is not detected, you may need to grant additional user permissions by running `<span class="pre">sudo</span><span> </span><span class="pre">chmod</span><span> </span><span class="pre">666</span><span> </span><span class="pre">/dev/hidraw<#></span>` where `<span class="pre"><#></span>` corresponds to the device index of the connected SpaceMouse.

To determine the device index, list all `<span class="pre">hidraw</span>` devices by running `<span class="pre">ls</span><span> </span><span class="pre">-l</span><span> </span><span class="pre">/dev/hidraw*</span>`. Identify the device corresponding to the SpaceMouse by running `<span class="pre">cat</span><span> </span><span class="pre">/sys/class/hidraw/hidraw<#>/device/uevent</span>` on each of the devices listed from the prior step.

We recommend using local deployment of Isaac Lab to use the SpaceMouse. If using container deployment ([Docker Guide](https://isaac-sim.github.io/IsaacLab/main/source/deployment/docker.html#deployment-docker)), you must manually mount the SpaceMouse to the `<span class="pre">isaac-lab-base</span>` container by adding a `<span class="pre">devices</span>` attribute with the path to the device in your `<span class="pre">docker-compose.yaml</span>` file:

```
devices:
-/dev/hidraw<#>:/dev/hidraw<#>
```

where `<span class="pre"><#></span>` is the device index of the connected SpaceMouse.

If you are using the IsaacLab + CloudXR container deployment ([Setting up CloudXR Teleoperation](https://isaac-sim.github.io/IsaacLab/main/source/how-to/cloudxr_teleoperation.html#cloudxr-teleoperation)), you can add the `<span class="pre">devices</span>` attribute under the `<span class="pre">services</span><span> </span><span class="pre">-></span><span> </span><span class="pre">isaac-lab-base</span>` section of the `<span class="pre">docker/docker-compose.cloudxr-runtime.patch.yaml</span>` file.

Isaac Lab is only compatible with the SpaceMouse Wireless and SpaceMouse Compact models from 3Dconnexion.

For tasks that benefit from the use of an extended reality (XR) device with hand tracking, Isaac Lab supports using NVIDIA CloudXR to immersively stream the scene to compatible XR devices for teleoperation. Note that when using hand tracking we recommend using the absolute variant of the task (`<span class="pre">Isaac-Stack-Cube-Franka-IK-Abs-v0</span>`), which requires the `<span class="pre">handtracking</span>` device:

```
./isaaclab.sh-pscripts/environments/teleoperation/teleop_se3_agent.py--taskIsaac-Stack-Cube-Franka-IK-Abs-v0--teleop_devicehandtracking--devicecpu
```

Note

See [Setting up CloudXR Teleoperation](https://isaac-sim.github.io/IsaacLab/main/source/how-to/cloudxr_teleoperation.html#cloudxr-teleoperation) to learn how to use CloudXR and experience teleoperation with Isaac Lab.

The script prints the teleoperation events configured. For keyboard, these are as follows:

```
Keyboard Controller for SE(3): Se3Keyboard
   Reset all commands: R
   Toggle gripper (open/close): K
   Move arm along x-axis: W/S
   Move arm along y-axis: A/D
   Move arm along z-axis: Q/E
   Rotate arm along x-axis: Z/X
   Rotate arm along y-axis: T/G
   Rotate arm along z-axis: C/V
```

For SpaceMouse, these are as follows:

```
SpaceMouse Controller for SE(3): Se3SpaceMouse
   Reset all commands: Right click
   Toggle gripper (open/close): Click the left button on the SpaceMouse
   Move arm along x/y-axis: Tilt the SpaceMouse
   Move arm along z-axis: Push or pull the SpaceMouse
   Rotate arm: Twist the SpaceMouse
```

The next section describes how teleoperation devices can be used for data collection for imitation learning.

## Imitation Learning with Isaac Lab Mimic

Using the teleoperation devices, it is also possible to collect data for learning from demonstrations (LfD). For this, we provide scripts to collect data into the open HDF5 format.

### Collecting demonstrations

To collect demonstrations with teleoperation for the environment `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-v0</span>`, use the following commands:

```
# step a: create folder for datasets
mkdir-pdatasets
# step b: collect data with a selected teleoperation device. Replace <teleop_device> with your preferred input device.
# Available options: spacemouse, keyboard, handtracking
./isaaclab.sh-pscripts/tools/record_demos.py--taskIsaac-Stack-Cube-Franka-IK-Rel-v0--devicecpu--teleop_device<teleop_device>--dataset_file./datasets/dataset.hdf5--num_demos10
# step a: replay the collected dataset
./isaaclab.sh-pscripts/tools/replay_demos.py--taskIsaac-Stack-Cube-Franka-IK-Rel-v0--devicecpu--dataset_file./datasets/dataset.hdf5
```

Note

The order of the stacked cubes should be blue (bottom), red (middle), green (top).

Tip

When using an XR device, we suggest collecting demonstrations with the `<span class="pre">Isaac-Stack-Cube-Frank-IK-Abs-v0</span>` version of the task and `<span class="pre">--teleop_device</span><span> </span><span class="pre">handtracking</span>`, which controls the end effector using the absolute position of the hand.

About 10 successful demonstrations are required in order for the following steps to succeed.

Here are some tips to perform demonstrations that lead to successful policy training:

* Keep demonstrations short. Shorter demonstrations mean fewer decisions for the policy, making training easier.
* Take a direct path. Do not follow along arbitrary axis, but move straight toward the goal.
* Do not pause. Perform smooth, continuous motions instead. It is not obvious for a policy why and when to pause, hence continuous motions are easier to learn.

If, while performing a demonstration, a mistake is made, or the current demonstration should not be recorded for some other reason, press the `<span class="pre">R</span>` key to discard the current demonstration, and reset to a new starting position.

Note

Non-determinism may be observed during replay as physics in IsaacLab are not determimnistically reproducible when using `<span class="pre">env.reset</span>`.

### Pre-recorded demonstrations

We provide a pre-recorded `<span class="pre">dataset.hdf5</span>` containing 10 human demonstrations for `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-v0</span>` here: [[Franka Dataset]](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/Mimic/franka_stack_datasets/dataset.hdf5). This dataset may be downloaded and used in the remaining tutorial steps if you do not wish to collect your own demonstrations.

Note

Use of the pre-recorded dataset is optional.

### Generating additional demonstrations with Isaac Lab Mimic

Additional demonstrations can be generated using Isaac Lab Mimic.

Isaac Lab Mimic is a feature in Isaac Lab that allows generation of additional demonstrations automatically, allowing a policy to learn successfully even from just a handful of manual demonstrations.

In the following example, we will show how to use Isaac Lab Mimic to generate additional demonstrations that can be used to train either a state-based policy (using the `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-Mimic-v0</span>` environment) or visuomotor policy (using the `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0</span>` environment).

Note

The following commands are run using CPU mode as a small number of envs are used which are I/O bound rather than compute bound.

Important

All commands in the following sections must keep a consistent policy type. For example, if choosing to use a state-based policy, then all commands used should be from the “State-based policy” tab.

In order to use Isaac Lab Mimic with the recorded dataset, first annotate the subtasks in the recording:

[X] State-based policy

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/annotate_demos.py\
--devicecpu--taskIsaac-Stack-Cube-Franka-IK-Rel-Mimic-v0--auto\
--input_file./datasets/dataset.hdf5--output_file./datasets/annotated_dataset.hdf5
```

[ ] Visuomotor policy

Then, use Isaac Lab Mimic to generate some additional demonstrations:

[X] State-based policy

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/generate_dataset.py\
--devicecpu--num_envs10--generation_num_trials10\
--input_file./datasets/annotated_dataset.hdf5--output_file./datasets/generated_dataset_small.hdf5
```

[ ] Visuomotor policy

Note

The output_file of the `<span class="pre">annotate_demos.py</span>` script is the input_file to the `<span class="pre">generate_dataset.py</span>` script

Inspect the output of generated data (filename: `<span class="pre">generated_dataset_small.hdf5</span>`), and if satisfactory, generate the full dataset:

[X] State-based policy

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/generate_dataset.py\
--devicecpu--headless--num_envs10--generation_num_trials1000\
--input_file./datasets/annotated_dataset.hdf5--output_file./datasets/generated_dataset.hdf5
```

[ ] Visuomotor policy

The number of demonstrations can be increased or decreased, 1000 demonstrations have been shown to provide good training results for this task.

Additionally, the number of environments in the `<span class="pre">--num_envs</span>` parameter can be adjusted to speed up data generation. The suggested number of 10 can be executed on a moderate laptop GPU. On a more powerful desktop machine, use a larger number of environments for a significant speedup of this step.

### Robomimic setup

As an example, we will train a BC agent implemented in [Robomimic](https://robomimic.github.io/) to train a policy. Any other framework or training method could be used.

To install the robomimic framework, use the following commands:

```
# install the dependencies
sudoaptinstallcmakebuild-essential
# install python module (for robomimic)
./isaaclab.sh-irobomimic
```

### Training an agent

Using the Mimic generated data we can now train a state-based BC agent for `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-v0</span>`, or a visuomotor BC agent for `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-v0</span>`:

[X] State-based policy

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/train.py\
--taskIsaac-Stack-Cube-Franka-IK-Rel-v0--algobc\
--dataset./datasets/generated_dataset.hdf5
```

[ ] Visuomotor policy

Note

By default the trained models and logs will be saved to `<span class="pre">IssacLab/logs/robomimic</span>`.

### Visualizing results

Tip

**Important: Testing Multiple Checkpoint Epochs**

When evaluating policy performance, it is common for different training epochs to yield significantly different results. If you don’t see the expected performance, **always test policies from various epochs** (not just the final checkpoint) to find the best-performing model. Model performance can vary substantially across training, and the final epoch is not always optimal.

By inferencing using the generated model, we can visualize the results of the policy:

[X] State-based policy

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/play.py\
--devicecpu--taskIsaac-Stack-Cube-Franka-IK-Rel-v0--num_rollouts50\
--checkpoint/PATH/TO/desired_model_checkpoint.pth
```

[ ] Visuomotor policy

Tip

**If you don’t see expected performance results:** Test policies from multiple checkpoint epochs, not just the final one. Policy performance can vary significantly across training epochs, and intermediate checkpoints often outperform the final model.

Note

**Expected Success Rates and Timings for Franka Cube Stack Task**

* Data generation success rate: ~50% (for both state + visuomotor)
* Data generation time: ~30 mins for state, ~4 hours for visuomotor (varies based on num envs the user runs)
* BC RNN training time: 1000 epochs + ~30 mins (for state), 600 epochs + ~6 hours (for visuomotor)
* BC RNN policy success rate: ~40-60% (for both state + visuomotor)
* **Recommendation:** Evaluate checkpoints from various epochs throughout training to identify the best-performing model

## Demo 1: Data Generation and Policy Training for a Humanoid Robot

[![GR-1 humanoid robot performing a pick and place task](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place.gif)

Isaac Lab Mimic supports data generation for robots with multiple end effectors. In the following demonstration, we will show how to generate data to train a Fourier GR-1 humanoid robot to perform a pick and place task.

### Optional: Collect and annotate demonstrations

#### Collect human demonstrations

Note

Data collection for the GR-1 humanoid robot environment requires use of an Apple Vision Pro headset. If you do not have access to an Apple Vision Pro, you may skip this step and continue on to the next step: [Generate the dataset](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html#generate-the-dataset). A pre-recorded annotated dataset is provided in the next step.

Tip

The GR1 scene utilizes the wrist poses from the Apple Vision Pro (AVP) as setpoints for a differential IK controller (Pink-IK). The differential IK controller requires the user’s wrist pose to be close to the robot’s initial or current pose for optimal performance. Rapid movements of the user’s wrist may cause it to deviate significantly from the goal state, which could prevent the IK controller from finding the optimal solution. This may result in a mismatch between the user’s wrist and the robot’s wrist. You can increase the gain of all the [Pink-IK controller’s FrameTasks](https://github.com/isaac-sim/IsaacLab/blob/main/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/pick_place/pickplace_gr1t2_env_cfg.py) to track the AVP wrist poses with lower latency. However, this may lead to more jerky motion. Separately, the finger joints of the robot are retargeted to the user’s finger joints using the [dex-retargeting](https://github.com/dexsuite/dex-retargeting) library.

Set up the CloudXR Runtime and Apple Vision Pro for teleoperation by following the steps in [Setting up CloudXR Teleoperation](https://isaac-sim.github.io/IsaacLab/main/source/how-to/cloudxr_teleoperation.html#cloudxr-teleoperation). CPU simulation is used in the following steps for better XR performance when running a single environment.

Collect a set of human demonstrations. A success demo requires the object to be placed in the bin and for the robot’s right arm to be retracted to the starting position.

The Isaac Lab Mimic Env GR-1 humanoid robot is set up such that the left hand has a single subtask, while the right hand has two subtasks. The first subtask involves the right hand remaining idle while the left hand picks up and moves the object to the position where the right hand will grasp it. This setup allows Isaac Lab Mimic to interpolate the right hand’s trajectory accurately by using the object’s pose, especially when poses are randomized during data generation. Therefore, avoid moving the right hand while the left hand picks up the object and brings it to a stable position.

[![GR-1 humanoid robot performing a good pick and place demonstration](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place_good_demo.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place_good_demo.gif) [![GR-1 humanoid robot performing a bad pick and place demonstration](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place_bad_demo.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place_bad_demo.gif)

**Left: A good human demonstration with smooth and steady motion. Right: A bad demonstration with jerky and exaggerated motion.**

Collect five demonstrations by running the following command:

```
./isaaclab.sh-pscripts/tools/record_demos.py\
--devicecpu\
--taskIsaac-PickPlace-GR1T2-Abs-v0\
--teleop_devicehandtracking\
--dataset_file./datasets/dataset_gr1.hdf5\
--num_demos5--enable_pinocchio
```

Note

We also provide a GR-1 pick and place task with waist degrees-of-freedom enabled `<span class="pre">Isaac-PickPlace-GR1T2-WaistEnabled-Abs-v0</span>` (see [Available Environments](https://isaac-sim.github.io/IsaacLab/main/source/overview/environments.html#environments) for details on the available environments, including the GR1 Waist Enabled variant). The same command above applies but with the task name changed to `<span class="pre">Isaac-PickPlace-GR1T2-WaistEnabled-Abs-v0</span>`.

Tip

If a demo fails during data collection, the environment can be reset using the teleoperation controls panel in the XR teleop client on the Apple Vision Pro or via voice control by saying “reset”. See [Teleoperate an Isaac Lab Robot with Apple Vision Pro](https://isaac-sim.github.io/IsaacLab/main/source/how-to/cloudxr_teleoperation.html#teleoperate-apple-vision-pro) for more details.

The robot uses simplified collision meshes for physics calculations that differ from the detailed visual meshes displayed in the simulation. Due to this difference, you may occasionally observe visual artifacts where parts of the robot appear to penetrate other objects or itself, even though proper collision handling is occurring in the physics simulation.

You can replay the collected demonstrations by running the following command:

```
./isaaclab.sh-pscripts/tools/replay_demos.py\
--devicecpu\
--taskIsaac-PickPlace-GR1T2-Abs-v0\
--dataset_file./datasets/dataset_gr1.hdf5--enable_pinocchio
```

Note

Non-determinism may be observed during replay as physics in IsaacLab are not determimnistically reproducible when using `<span class="pre">env.reset</span>`.

#### Annotate the demonstrations

Unlike the prior Franka stacking task, the GR-1 pick and place task uses manual annotation to define subtasks.

The pick and place task has one subtask for the left arm (pick) and two subtasks for the right arm (idle, place). Annotations denote the end of a subtask. For the pick and place task, this means there are no annotations for the left arm and one annotation for the right arm (the end of the final subtask is always implicit).

Each demo requires a single annotation between the first and second subtask of the right arm. This annotation (“S” button press) should be done when the right robot arm finishes the “idle” subtask and begins to move towards the target object. An example of a correct annotation is shown below:

[![../../../_images/gr-1_pick_place_annotation.jpg](https://isaac-sim.github.io/IsaacLab/main/_images/gr-1_pick_place_annotation.jpg)](https://isaac-sim.github.io/IsaacLab/main/_images/gr-1_pick_place_annotation.jpg)

Annotate the demonstrations by running the following command:

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/annotate_demos.py\
--devicecpu\
--taskIsaac-PickPlace-GR1T2-Abs-Mimic-v0\
--input_file./datasets/dataset_gr1.hdf5\
--output_file./datasets/dataset_annotated_gr1.hdf5--enable_pinocchio
```

Note

The script prints the keyboard commands for manual annotation and the current subtask being annotated:

```
Annotating episode #0 (demo_0)
   Playing the episode for subtask annotations for eef "right".
   Subtask signals to annotate:
      - Termination:      ['idle_right']

   Press "N" to begin.
   Press "B" to pause.
   Press "S" to annotate subtask signals.
   Press "Q" to skip the episode.
```

Tip

If the object does not get placed in the bin during annotation, you can press “N” to replay the episode and annotate again. Or you can press “Q” to skip the episode and annotate the next one.

### Generate the dataset

If you skipped the prior collection and annotation step, download the pre-recorded annotated dataset `<span class="pre">dataset_annotated_gr1.hdf5</span>` from here: [[Annotated GR1 Dataset]](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/Mimic/pick_place_datasets/dataset_annotated_gr1.hdf5). Place the file under `<span class="pre">IsaacLab/datasets</span>` and run the following command to generate a new dataset with 1000 demonstrations.

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/generate_dataset.py\
--devicecpu--headless--num_envs20--generation_num_trials1000--enable_pinocchio\
--input_file./datasets/dataset_annotated_gr1.hdf5--output_file./datasets/generated_dataset_gr1.hdf5
```

### Train a policy

Use [Robomimic](https://robomimic.github.io/) to train a policy for the generated dataset.

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/train.py\
--taskIsaac-PickPlace-GR1T2-Abs-v0--algobc\
--normalize_training_actions\
--dataset./datasets/generated_dataset_gr1.hdf5
```

The training script will normalize the actions in the dataset to the range [-1, 1]. The normalization parameters are saved in the model directory under `<span class="pre">PATH_TO_MODEL_DIRECTORY/logs/normalization_params.txt</span>`. Record the normalization parameters for later use in the visualization step.

Note

By default the trained models and logs will be saved to `<span class="pre">IssacLab/logs/robomimic</span>`.

### Visualize the results

Visualize the results of the trained policy by running the following command, using the normalization parameters recorded in the prior training step:

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/play.py\
--devicecpu\
--enable_pinocchio\
--taskIsaac-PickPlace-GR1T2-Abs-v0\
--num_rollouts50\
--horizon400\
--norm_factor_min<NORM_FACTOR_MIN>\
--norm_factor_max<NORM_FACTOR_MAX>\
--checkpoint/PATH/TO/desired_model_checkpoint.pth
```

Note

Change the `<span class="pre">NORM_FACTOR</span>` in the above command with the values generated in the training step.

Tip

**If you don’t see expected performance results:** It is critical to test policies from various checkpoint epochs. Performance can vary significantly between epochs, and the best-performing checkpoint is often not the final one.

[![GR-1 humanoid robot performing a pick and place task](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place_policy.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_steering_wheel_pick_place_policy.gif)
The trained policy performing the pick and place task in Isaac Lab.

Note

**Expected Success Rates and Timings for Pick and Place GR1T2 Task**

* Success rate for data generation depends on the quality of human demonstrations (how well the user performs them) and dataset annotation quality. Both data generation and downstream policy success are sensitive to these factors and can show high variance. See [Common Pitfalls when Generating Data](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html#common-pitfalls-generating-data) for tips to improve your dataset.
* Data generation success for this task is typically 65-80% over 1000 demonstrations, taking 18-40 minutes depending on GPU hardware and success rate (19 minutes on a RTX ADA 6000 @ 80% success rate).
* Behavior Cloning (BC) policy success is typically 75-86% (evaluated on 50 rollouts) when trained on 1000 generated demonstrations for 2000 epochs (default), depending on demonstration quality. Training takes approximately 29 minutes on a RTX ADA 6000.
* **Recommendation:** Train for 2000 epochs with 1000 generated demonstrations, and **evaluate multiple checkpoints saved between the 1000th and 2000th epochs** to select the best-performing policy. Testing various epochs is essential for finding optimal performance.

## Demo 2: Data Generation and Policy Training for Humanoid Robot Locomanipulation with Unitree G1

In this demo, we showcase the integration of locomotion and manipulation capabilities within a single humanoid robot system. This locomanipulation environment enables data collection for complex tasks that combine navigation and object manipulation. The demonstration follows a multi-step process: first, it generates pick and place tasks similar to Demo 1, then introduces a navigation component that uses specialized scripts to generate scenes where the humanoid robot must move from point A to point B. The robot picks up an object at the initial location (point A) and places it at the target destination (point B).

[![G1 humanoid robot with locomanipulation performing a pick and place task](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/locomanipulation-g-1_steering_wheel_pick_place.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/locomanipulation-g-1_steering_wheel_pick_place.gif)

Note

**Locomotion policy training**

The locomotion policy used in this integration example was trained using the [AGILE](https://github.com/nvidia-isaac/WBC-AGILE) framework. AGILE is an officially supported humanoid control training pipeline that leverages the manager based environment in Isaac Lab. It will also be seamlessly integrated with other evaluation and deployment tools across Isaac products. This allows teams to rely on a single, maintained stack covering all necessary infrastructure and tooling for policy training, with easy export to real-world deployment. The AGILE repository contains updated pre-trained policies with separate upper and lower body policies for flexibtility. They have been verified in the real world and can be directly deployed. Users can also train their own locomotion or whole-body control policies using the AGILE framework.

### Generate the manipulation dataset

The same data generation and policy training steps from Demo 1.0 can be applied to the G1 humanoid robot with locomanipulation capabilities. This demonstration shows how to train a G1 robot to perform pick and place tasks with full-body locomotion and manipulation.

The process follows the same workflow as Demo 1.0, but uses the `<span class="pre">Isaac-PickPlace-Locomanipulation-G1-Abs-v0</span>` task environment.

Follow the same data collection, annotation, and generation process as demonstrated in Demo 1.0, but adapted for the G1 locomanipulation task.

Hint

If desired, data collection and annotation can be done using the same commands as the prior examples for validation of the dataset.

The G1 robot with locomanipulation capabilities combines full-body locomotion with manipulation to perform pick and place tasks.

**Note that the following commands are only for your reference and dataset validation purposes - they are not required for this demo.**

To collect demonstrations:

```
./isaaclab.sh-pscripts/tools/record_demos.py\
--devicecpu\
--taskIsaac-PickPlace-Locomanipulation-G1-Abs-v0\
--teleop_devicehandtracking\
--dataset_file./datasets/dataset_g1_locomanip.hdf5\
--num_demos5--enable_pinocchio
```

Note

Depending on how the Apple Vision Pro app was initialized, the hands of the operator might be very far up or far down compared to the hands of the G1 robot. If this is the case, you can click **Stop AR** in the AR tab in Isaac Lab, and move the AR Anchor prim. Adjust it down to bring the hands of the operator lower, and up to bring them higher. Click **Start AR** to resume teleoperation session. Make sure to match the hands of the robot before clicking **Play** in the Apple Vision Pro, otherwise there will be an undesired large force generated initially.

You can replay the collected demonstrations by running:

```
./isaaclab.sh-pscripts/tools/replay_demos.py\
--devicecpu\
--taskIsaac-PickPlace-Locomanipulation-G1-Abs-v0\
--dataset_file./datasets/dataset_g1_locomanip.hdf5--enable_pinocchio
```

To annotate the demonstrations:

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/annotate_demos.py\
--devicecpu\
--taskIsaac-Locomanipulation-G1-Abs-Mimic-v0\
--input_file./datasets/dataset_g1_locomanip.hdf5\
--output_file./datasets/dataset_annotated_g1_locomanip.hdf5--enable_pinocchio
```

If you skipped the prior collection and annotation step, download the pre-recorded annotated dataset `<span class="pre">dataset_annotated_g1_locomanip.hdf5</span>` from here: [[Annotated G1 Dataset]](https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/Mimic/pick_place_datasets/dataset_annotated_g1_locomanip.hdf5). Place the file under `<span class="pre">IsaacLab/datasets</span>` and run the following command to generate a new dataset with 1000 demonstrations.

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/generate_dataset.py\
--devicecpu--headless--num_envs20--generation_num_trials1000--enable_pinocchio\
--input_file./datasets/dataset_annotated_g1_locomanip.hdf5--output_file./datasets/generated_dataset_g1_locomanip.hdf5
```

### Train a manipulation-only policy

At this point you can train a policy that only performs manipulation tasks using the generated dataset:

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/train.py\
--taskIsaac-PickPlace-Locomanipulation-G1-Abs-v0--algobc\
--normalize_training_actions\
--dataset./datasets/generated_dataset_g1_locomanip.hdf5
```

### Visualize the results

Visualize the trained policy performance:

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/play.py\
--devicecpu\
--enable_pinocchio\
--taskIsaac-PickPlace-Locomanipulation-G1-Abs-v0\
--num_rollouts50\
--horizon400\
--norm_factor_min<NORM_FACTOR_MIN>\
--norm_factor_max<NORM_FACTOR_MAX>\
--checkpoint/PATH/TO/desired_model_checkpoint.pth
```

Note

Change the `<span class="pre">NORM_FACTOR</span>` in the above command with the values generated in the training step.

Tip

**If you don’t see expected performance results:** Always test policies from various checkpoint epochs. Different epochs can produce significantly different results, so evaluate multiple checkpoints to find the optimal model.

[![G1 humanoid robot performing a pick and place task](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/locomanipulation-g-1_steering_wheel_pick_place.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/locomanipulation-g-1_steering_wheel_pick_place.gif)
The trained policy performing the pick and place task in Isaac Lab.

Note

**Expected Success Rates and Timings for Locomanipulation Pick and Place Task**

* Success rate for data generation depends on the quality of human demonstrations (how well the user performs them) and dataset annotation quality. Both data generation and downstream policy success are sensitive to these factors and can show high variance. See [Common Pitfalls when Generating Data](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html#common-pitfalls-generating-data) for tips to improve your dataset.
* Data generation success for this task is typically 65-82% over 1000 demonstrations, taking 18-40 minutes depending on GPU hardware and success rate (18 minutes on a RTX ADA 6000 @ 82% success rate).
* Behavior Cloning (BC) policy success is typically 75-85% (evaluated on 50 rollouts) when trained on 1000 generated demonstrations for 2000 epochs (default), depending on demonstration quality. Training takes approximately 40 minutes on a RTX ADA 6000.
* **Recommendation:** Train for 2000 epochs with 1000 generated demonstrations, and **evaluate multiple checkpoints saved between the 1000th and 2000th epochs** to select the best-performing policy. Testing various epochs is essential for finding optimal performance.

### Generate the dataset with manipulation and point-to-point navigation

To create a comprehensive locomanipulation dataset that combines both manipulation and navigation capabilities, you can generate a navigation dataset using the manipulation dataset from the previous step as input.

[![G1 humanoid robot combining navigation with locomanipulation](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/disjoint_navigation.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/disjoint_navigation.gif)
G1 humanoid robot performing locomanipulation with navigation capabilities.

The locomanipulation dataset generation process takes the previously generated manipulation dataset and creates scenarios where the robot must navigate from one location to another while performing manipulation tasks. This creates a more complex dataset that includes both locomotion and manipulation behaviors.

To generate the locomanipulation dataset, use the following command:

```
./isaaclab.sh-p\
scripts/imitation_learning/locomanipulation_sdg/generate_data.py\
--devicecpu\
--kit_args="--enable isaacsim.replicator.mobility_gen"\
--task="Isaac-G1-SteeringWheel-Locomanipulation"\
--dataset./datasets/generated_dataset_g1_locomanip.hdf5\
--num_runs1\
--lift_step60\
--navigate_step130\
--enable_pinocchio\
--output_file./datasets/generated_dataset_g1_locomanipulation_sdg.hdf5\
--enable_cameras
```

Note

The input dataset (`<span class="pre">--dataset</span>`) should be the manipulation dataset generated in the previous step. You can specify any output filename using the `<span class="pre">--output_file_name</span>` parameter.

The key parameters for locomanipulation dataset generation are:

* `<span class="pre">--lift_step</span><span> </span><span class="pre">70</span>`: Number of steps for the lifting phase of the manipulation task. This should mark the point immediately after the robot has grasped the object.
* `<span class="pre">--navigate_step</span><span> </span><span class="pre">120</span>`: Number of steps for the navigation phase between locations. This should make the point where the robot has lifted the object and is ready to walk.
* `<span class="pre">--output_file</span>`: Name of the output dataset file

This process creates a dataset where the robot performs the manipulation task at different locations, requiring it to navigate between points while maintaining the learned manipulation behaviors. The resulting dataset can be used to train policies that combine both locomotion and manipulation capabilities.

Note

You can visualize the robot trajectory results with the following script command:

```
./isaaclab.sh-pscripts/imitation_learning/locomanipulation_sdg/plot_navigation_trajectory.py--input_filedatasets/generated_dataset_g1_locomanipulation_sdg.hdf5--output_dir/PATH/TO/DESIRED_OUTPUT_DIR
```

The data generated from this locomanipulation pipeline can also be used to finetune an imitation learning policy using GR00T N1.5. To do this, you may convert the generated dataset to LeRobot format as expected by GR00T N1.5, and then run the finetuning script provided in the GR00T N1.5 repository. An example closed-loop policy rollout is shown in the video below:

[![Simulation rollout of GR00T N1.5 policy finetuned for locomanipulation](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/locomanipulation_sdg_disjoint_nav_groot_policy_4x.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/locomanipulation_sdg_disjoint_nav_groot_policy_4x.gif)
Simulation rollout of GR00T N1.5 policy finetuned for locomanipulation.

The policy shown above uses the camera image, hand poses, hand joint positions, object pose, and base goal pose as inputs. The output of the model is the target base velocity, hand poses, and hand joint positions for the next several timesteps.

## Demo 3: Visuomotor Policy for a Humanoid Robot

[![GR-1 humanoid robot performing a pouring task](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_nut_pouring_policy.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_nut_pouring_policy.gif)

### Download the Dataset

Download the pre-generated dataset from [here](https://download.isaacsim.omniverse.nvidia.com/isaaclab/dataset/generated_dataset_gr1_nut_pouring.hdf5) and place it under `<span class="pre">IsaacLab/datasets/generated_dataset_gr1_nut_pouring.hdf5</span>` ( **Note: The dataset size is approximately 12GB** ). The dataset contains 1000 demonstrations of a humanoid robot performing a pouring/placing task that was generated using Isaac Lab Mimic for the `<span class="pre">Isaac-NutPour-GR1T2-Pink-IK-Abs-Mimic-v0</span>` task.

Hint

If desired, data collection, annotation, and generation can be done using the same commands as the prior examples.

The robot first picks up the red beaker and pours the contents into the yellow bowl. Then, it drops the red beaker into the blue bin. Lastly, it places the yellow bowl onto the white scale. See the video in the [Visualize the results](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html#visualize-results-demo-2) section below for a visual demonstration of the task.

**The success criteria for this task requires the red beaker to be placed in the blue bin, the green nut to be in the yellow bowl, and the yellow bowl to be placed on top of the white scale.**

Attention

**The following commands are only for your reference and are not required for this demo.**

To collect demonstrations:

```
./isaaclab.sh-pscripts/tools/record_demos.py\
--devicecpu\
--taskIsaac-NutPour-GR1T2-Pink-IK-Abs-v0\
--teleop_devicehandtracking\
--dataset_file./datasets/dataset_gr1_nut_pouring.hdf5\
--num_demos5--enable_pinocchio
```

Since this is a visuomotor environment, the `<span class="pre">--enable_cameras</span>` flag must be added to the annotation and data generation commands.

To annotate the demonstrations:

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/annotate_demos.py\
--devicecpu\
--enable_cameras\
--rendering_modebalanced\
--taskIsaac-NutPour-GR1T2-Pink-IK-Abs-Mimic-v0\
--input_file./datasets/dataset_gr1_nut_pouring.hdf5\
--output_file./datasets/dataset_annotated_gr1_nut_pouring.hdf5--enable_pinocchio
```

Warning

There are multiple right eef annotations for this task. Annotations for subtasks for the same eef cannot have the same action index. Make sure to annotate the right eef subtasks with different action indices.

To generate the dataset:

```
./isaaclab.sh-pscripts/imitation_learning/isaaclab_mimic/generate_dataset.py\
--devicecpu\
--headless\
--enable_pinocchio\
--enable_cameras\
--rendering_modebalanced\
--taskIsaac-NutPour-GR1T2-Pink-IK-Abs-Mimic-v0\
--generation_num_trials1000\
--num_envs5\
--input_file./datasets/dataset_annotated_gr1_nut_pouring.hdf5\
--output_file./datasets/generated_dataset_gr1_nut_pouring.hdf5
```

### Train a policy

Use [Robomimic](https://robomimic.github.io/) to train a visuomotor BC agent for the task.

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/train.py\
--taskIsaac-NutPour-GR1T2-Pink-IK-Abs-v0--algobc\
--normalize_training_actions\
--dataset./datasets/generated_dataset_gr1_nut_pouring.hdf5
```

The training script will normalize the actions in the dataset to the range [-1, 1]. The normalization parameters are saved in the model directory under `<span class="pre">PATH_TO_MODEL_DIRECTORY/logs/normalization_params.txt</span>`. Record the normalization parameters for later use in the visualization step.

Note

By default the trained models and logs will be saved to `<span class="pre">IsaacLab/logs/robomimic</span>`.

You can also post-train a [GR00T](https://github.com/NVIDIA/Isaac-GR00T) foundation model to deploy a Vision-Language-Action policy for the task.

Please refer to the [IsaacLabEvalTasks](https://github.com/isaac-sim/IsaacLabEvalTasks/) repository for more details.

### Visualize the results

Visualize the results of the trained policy by running the following command, using the normalization parameters recorded in the prior training step:

```
./isaaclab.sh-pscripts/imitation_learning/robomimic/play.py\
--devicecpu\
--enable_pinocchio\
--enable_cameras\
--rendering_modebalanced\
--taskIsaac-NutPour-GR1T2-Pink-IK-Abs-v0\
--num_rollouts50\
--horizon350\
--norm_factor_min<NORM_FACTOR_MIN>\
--norm_factor_max<NORM_FACTOR_MAX>\
--checkpoint/PATH/TO/desired_model_checkpoint.pth
```

Note

Change the `<span class="pre">NORM_FACTOR</span>` in the above command with the values generated in the training step.

Tip

**If you don’t see expected performance results:** Test policies from various checkpoint epochs, not just the final one. Policy performance can vary substantially across training, and intermediate checkpoints often yield better results.

[![GR-1 humanoid robot performing a pouring task](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_nut_pouring_policy.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/gr-1_nut_pouring_policy.gif)
The trained visuomotor policy performing the pouring task in Isaac Lab.

Note

**Expected Success Rates and Timings for Visuomotor Nut Pour GR1T2 Task**

* Success rate for data generation depends on the quality of human demonstrations (how well the user performs them) and dataset annotation quality. Both data generation and downstream policy success are sensitive to these factors and can show high variance. See [Common Pitfalls when Generating Data](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html#common-pitfalls-generating-data) for tips to improve your dataset.
* Data generation for 1000 demonstrations takes approximately 10 hours on a RTX ADA 6000.
* Behavior Cloning (BC) policy success is typically 50-60% (evaluated on 50 rollouts) when trained on 1000 generated demonstrations for 600 epochs (default). Training takes approximately 15 hours on a RTX ADA 6000.
* **Recommendation:** Train for 600 epochs with 1000 generated demonstrations, and **evaluate multiple checkpoints saved between the 300th and 600th epochs** to select the best-performing policy. Testing various epochs is critical for achieving optimal performance.

## Common Pitfalls when Generating Data

**Demonstrations are too long:**

* Longer time horizon is harder to learn for a policy
* Start close to the first object and minimize motions

**Demonstrations are not smooth:**

* Irregular motion is hard for policy to decipher
* Better teleop devices result in better data (i.e. SpaceMouse is better than Keyboard)

**Pauses in demonstrations:**

* Pauses are difficult to learn
* Keep the human motions smooth and fluid

**Excessive number of subtasks:**

* Minimize the number of defined subtasks for completing a given task
* Less subtacks results in less stitching of trajectories, yielding higher data generation success rate

**Lack of action noise:**

* Action noise makes policies more robust

**Recording cropped too tight:**

* If recording stops on the frame the success term triggers, it may not re-trigger during replay
* Allow for some buffer at the end of recording

**Non-deterministic replay:**

* Physics in IsaacLab are not deterministically reproducible when using `<span class="pre">env.reset</span>` so demonstrations may fail on replay
* Collect more human demos than needed, use the ones that succeed during annotation
* All data in Isaac Lab Mimic generated HDF5 file represent a successful demo and can be used for training (even if non-determinism causes failure when replayed)

## Creating Your Own Isaac Lab Mimic Compatible Environments

### How it works

Isaac Lab Mimic works by splitting the input demonstrations into subtasks. Subtasks are user-defined segments in the demonstrations that are common to all demonstrations. Examples for subtasks are “grasp an object”, “move end effector to some pre-defined position”, “release object” etc.. Note that most subtasks are defined with respect to some object that the robot interacts with.

Subtasks need to be defined, and then annotated for each input demonstration. Annotation can either happen algorithmically by defining heuristics for subtask detection, as was done in the example above, or it can be done manually.

With subtasks defined and annotated, Isaac Lab Mimic utilizes a small number of helper methods to then transform the subtask segments, and generate new demonstrations by stitching them together to match the new task at hand.

For each thusly generated candidate demonstration, Isaac Lab Mimic uses a boolean success criteria to determine whether the demonstration succeeded in performing the task, and if so, add it to the output dataset. Success rate of candidate demonstrations can be as high as 70% in simple cases, and as low as <1%, depending on the difficulty of the task, and the complexity of the robot itself.

### Configuration and subtask definition

Subtasks, among other configuration settings for Isaac Lab Mimic, are defined in a Mimic compatible environment configuration class that is created by extending the existing environment config with additional Mimic required parameters.

All Mimic required config parameters are specified in the [`<span class="pre">MimicEnvCfg</span>`](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.envs.html#isaaclab.envs.MimicEnvCfg "isaaclab.envs.MimicEnvCfg") class.

The config class `<span class="pre">FrankaCubeStackIKRelMimicEnvCfg</span>` serves as an example of creating a Mimic compatible environment config class for the Franka stacking task that was used in the examples above.

The `<span class="pre">DataGenConfig</span>` member contains various parameters that influence how data is generated. It is initially sufficient to just set the `<span class="pre">name</span>` parameter, and revise the rest later.

Subtasks are a list of [`<span class="pre">SubTaskConfig</span>`](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.envs.html#isaaclab.envs.SubTaskConfig "isaaclab.envs.SubTaskConfig") objects, of which the most important members are:

* `<span class="pre">object_ref</span>` is the object that is being interacted with. This will be used to adjust motions relative to this object during data generation. Can be `<span class="pre">None</span>` if the current subtask does not involve any object.
* `<span class="pre">subtask_term_signal</span>` is the ID of the signal indicating whether the subtask is active or not.

For multi end-effector environments, subtask ordering between end-effectors can be enforced by specifying subtask constraints. These constraints are defined in the [`<span class="pre">SubTaskConstraintConfig</span>`](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.envs.html#isaaclab.envs.SubTaskConstraintConfig "isaaclab.envs.SubTaskConstraintConfig") class.

### Subtask annotation

Once the subtasks are defined, they need to be annotated in the source data. There are two methods to annotate source demonstrations for subtask boundaries: Manual annotation or using heuristics.

It is often easiest to perform manual annotations, since the number of input demonstrations is usually very small. To perform manual annotations, use the `<span class="pre">annotate_demos.py</span>` script without the `<span class="pre">--auto</span>` flag. Then press `<span class="pre">B</span>` to pause, `<span class="pre">N</span>` to continue, and `<span class="pre">S</span>` to annotate a subtask boundary.

For more accurate boundaries, or to speed up repeated processing of a given task for experiments, heuristics can be implemented to perform the same task. Heuristics are observations in the environment. An example how to add subtask terms can be found in `<span class="pre">source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/stack/stack_env_cfg.py</span>`, where they are added as an observation group called `<span class="pre">SubtaskCfg</span>`. This example is using prebuilt heuristics, but custom heuristics are easily implemented.

### Helpers for demonstration generation

Helpers needed for Isaac Lab Mimic are defined in the environment. All tasks that are to be used with Isaac Lab Mimic are derived from the [`<span class="pre">ManagerBasedRLMimicEnv</span>`](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.envs.html#isaaclab.envs.ManagerBasedRLMimicEnv "isaaclab.envs.ManagerBasedRLMimicEnv") base class, and must implement the following functions:

* `<span class="pre">get_robot_eef_pose</span>`: Returns the current robot end effector pose in the same frame as used by the robot end effector controller.
* `<span class="pre">target_eef_pose_to_action</span>`: Takes a target pose and a gripper action for the end effector controller and returns an action which achieves the target pose.
* `<span class="pre">action_to_target_eef_pose</span>`: Takes an action and returns a target pose for the end effector controller.
* `<span class="pre">actions_to_gripper_actions</span>`: Takes a sequence of actions and returns the gripper actuation part of the actions.
* `<span class="pre">get_object_poses</span>`: Returns the pose of each object in the scene that is used for data generation.
* `<span class="pre">get_subtask_term_signals</span>`: Returns a dictionary of binary flags for each subtask in a task. The flag of true is set when the subtask has been completed and false otherwise.

The class `<span class="pre">FrankaCubeStackIKRelMimicEnv</span>` shows an example of creating a Mimic compatible environment from an existing Isaac Lab environment.

### Registering the environment

Once both Mimic compatible environment and environment config classes have been created, a new Mimic compatible environment can be registered using `<span class="pre">gym.register</span>`. For the Franka stacking task in the examples above, the Mimic environment is registered as `<span class="pre">Isaac-Stack-Cube-Franka-IK-Rel-Mimic-v0</span>`.

The registered environment is now ready to be used with Isaac Lab Mimic.

## Tips for Successful Data Generation with Isaac Lab Mimic

### Splitting subtasks

A general rule of thumb is to split the task into as few subtasks as possible, while still being able to complete the task. Isaac Lab Mimic data generation uses linear interpolation to bridge and stitch together subtask segments. More subtasks result in more stitching of trajectories which can result in less smooth motions and more failed demonstrations. For this reason, it is often best to annoatate subtask boundaries where the robot’s motion is unlikely to collide with other objects.

For example, in the scenario below, there is a subtask partition after the robot’s left arm grasps the object. On the left, the subtask annotation is marked immediately after the grasp, while on the right, the annotation is marked after the robot has grasped and lifted the object. In the left case, the interpolation causes the robot’s left arm to collide with the table and it’s motion lags while on the right the motion is continuous and smooth.

[![Subtask splitting example](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/lagging_subtask.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/lagging_subtask.gif)

**Motion lag/collision caused by poor subtask splitting (left)**

### Selecting number of interpolation steps

The number of interpolation steps between subtask segments can be specified in the [`<span class="pre">SubTaskConfig</span>`](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.envs.html#isaaclab.envs.SubTaskConfig "isaaclab.envs.SubTaskConfig") class. Once transformed, the subtask segments don’t start/end at the same spot, thus to create a continuous motion, Isaac Lab Mimic will apply linear interpolation between the last point of the previous subtask and the first point of the next subtask.

The number of interpolation steps can be tuned to control the smoothness of the generated demonstrations during this stitching process. The appropriate number of interpolation steps depends on the speed of the robot and the complexity of the task. A complex task with a large object reset distribution will have larger gaps between subtask segments and require more interpolation steps to create a smooth motion. Alternatively, a task with small gaps between subtask segments should use a small number of interpolation steps to avoid unnecessary motion lag caused by too many steps.

An example of how the number of interpolation steps can affect the generated demonstrations is shown below. In the example, an interpolation is applied to the right arm of the robot to bridge the gap between the left arm’s grasp and the right arm’s placement. With 0 steps, the right arm exhibits a jerky jump in motion while with 20 steps, the motion is laggy. With 5 steps, the motion is smooth and natural.

[![GR-1 robot with 0 interpolation steps](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/0_interpolation_steps.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/0_interpolation_steps.gif) [![GR-1 robot with 5 interpolation steps](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/5_interpolation_steps.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/5_interpolation_steps.gif) [![GR-1 robot with 20 interpolation steps](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/20_interpolation_steps.gif)](https://download.isaacsim.omniverse.nvidia.com/isaaclab/images/20_interpolation_steps.gif)

**Left: 0 steps. Middle: 5 steps. Right: 20 steps.**
