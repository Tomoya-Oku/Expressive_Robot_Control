.PHONY: build shell ws rviz sim moveit fake real-check real clean

UPSTREAM_PACKAGES := cra_description dobot_rviz dobot_gazebo dobot_moveit me6_moveit cr_robot_ros2 dobot_msgs_v4
LOCAL_PACKAGES := dobot_me6_description dobot_me6_bringup dobot_me6_driver dobot_me6_examples
BUILD_PACKAGES := $(UPSTREAM_PACKAGES) $(LOCAL_PACKAGES)

build:
	docker compose build

shell: build
	docker compose run --rm ros2 bash

ws: build
	docker compose run --rm ros2 bash -lc "rosdep update && rosdep install --from-paths src --ignore-src -r -y --dependency-types buildtool --dependency-types build --dependency-types exec --skip-keys 'message_generation warehouse_ros_mongo' && colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES)"

rviz: build
	docker compose run --rm ros2 bash -lc "colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES) && source install/setup.bash && ros2 launch dobot_rviz dobot_rviz.launch.py gui:=true"

fake: build
	docker compose run --rm ros2 bash -lc "colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES) && source install/setup.bash && ros2 launch dobot_me6_bringup fake_control.launch.py"

sim: build
	docker compose run --rm ros2 bash -lc "colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES) && source install/setup.bash && ros2 launch dobot_gazebo dobot_gazebo.launch.py"

moveit: build
	docker compose run --rm ros2 bash -lc "colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES) && source install/setup.bash && ros2 launch dobot_moveit moveit_demo.launch.py"

real-check: build
	docker compose run --rm ros2 bash -lc "colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES) && source install/setup.bash && ros2 run dobot_me6_driver safety_check"

real: build
	docker compose run --rm ros2 bash -lc "colcon build --symlink-install --packages-up-to $(BUILD_PACKAGES) && source install/setup.bash && ros2 launch cr_robot_ros2 dobot_bringup_ros2.launch.py"

clean:
	rm -rf ros2_ws/build ros2_ws/install ros2_ws/log
