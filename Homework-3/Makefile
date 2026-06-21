.PHONY: build shell ws rviz sim sim-rviz moveit fake real-check real-probe real-prepare real-bridge real clean

UPSTREAM_PACKAGES := cra_description dobot_rviz dobot_gazebo dobot_moveit me6_moveit cr_robot_ros2 dobot_msgs_v4
LOCAL_PACKAGES := dobot_me6_bringup dobot_me6_driver dobot_me6_examples
BUILD_PACKAGES := $(UPSTREAM_PACKAGES) $(LOCAL_PACKAGES)
COLCON_BUILD := colcon build --symlink-install --cmake-clean-first --packages-up-to $(BUILD_PACKAGES)

build:
	docker compose build

shell: build
	docker compose run --rm ros2 bash

ws: build
	docker compose run --rm ros2 bash -lc "rosdep update && rosdep install --from-paths src --ignore-src -r -y --dependency-types buildtool --dependency-types build --dependency-types exec --skip-keys 'message_generation warehouse_ros_mongo' && $(COLCON_BUILD)"

rviz: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch dobot_me6_bringup display.launch.py"

fake: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch dobot_me6_bringup fake_control.launch.py"

sim: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch dobot_me6_bringup gazebo.launch.py"

sim-rviz: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch dobot_me6_bringup gazebo.launch.py start_rviz:=true"

moveit: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch dobot_moveit moveit_demo.launch.py"

real-check: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 run dobot_me6_driver safety_check"

real-probe: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 run dobot_me6_driver hardware_setup"

real-prepare: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 run dobot_me6_driver hardware_setup --prepare --enable"

real-bridge: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch dobot_me6_driver real_validation.launch.py dry_run:=false speed_ratio:=10.0"

real: build
	docker compose run --rm ros2 bash -lc "$(COLCON_BUILD) && source install/setup.bash && ros2 launch cr_robot_ros2 dobot_bringup_ros2.launch.py"

clean:
	rm -rf ros2_ws/build ros2_ws/install ros2_ws/log
