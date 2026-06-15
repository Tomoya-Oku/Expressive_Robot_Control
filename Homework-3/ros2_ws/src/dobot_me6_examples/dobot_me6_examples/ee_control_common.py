import argparse
import math
import sys
import time
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


JOINT_NAMES = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
READY_Q = [0.0, math.radians(-30.0), math.radians(45.0), 0.0, math.radians(35.0), 0.0]
HOME_Q = [0.0] * 6
JOINT_LIMITS = [
    (-6.27, 6.27),
    (-2.356, 2.356),
    (-2.6878, 2.6878),
    (-2.7925, 2.7925),
    (-3.0194, 3.0194),
    (-6.27, 6.27),
]


def _matmul(a, b):
    rows = len(a)
    cols = len(b[0])
    inner = len(b)
    return [[sum(a[i][k] * b[k][j] for k in range(inner)) for j in range(cols)] for i in range(rows)]


def _matvec(a, v):
    return [sum(row[i] * v[i] for i in range(len(v))) for row in a]


def _transpose(a):
    return [list(row) for row in zip(*a)]


def _eye(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def _cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _sub(a, b):
    return [a[i] - b[i] for i in range(len(a))]


def _add(a, b):
    return [a[i] + b[i] for i in range(len(a))]


def _scale(v, s):
    return [x * s for x in v]


def _norm(v):
    return math.sqrt(sum(x * x for x in v))


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _rot_x(r):
    c, s = math.cos(r), math.sin(r)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]


def _rot_y(p):
    c, s = math.cos(p), math.sin(p)
    return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]


def _rot_z(y):
    c, s = math.cos(y), math.sin(y)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def _rpy_to_rot(rpy):
    return _matmul(_matmul(_rot_z(rpy[2]), _rot_y(rpy[1])), _rot_x(rpy[0]))


def _axis_angle(axis, theta):
    x, y, z = axis
    c = math.cos(theta)
    s = math.sin(theta)
    v = 1.0 - c
    return [
        [x * x * v + c, x * y * v - z * s, x * z * v + y * s],
        [y * x * v + z * s, y * y * v + c, y * z * v - x * s],
        [z * x * v - y * s, z * y * v + x * s, z * z * v + c],
    ]


def _inv3(m):
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise ValueError("singular 3x3 matrix")
    inv_det = 1.0 / det
    return [
        [(e * i - f * h) * inv_det, (c * h - b * i) * inv_det, (b * f - c * e) * inv_det],
        [(f * g - d * i) * inv_det, (a * i - c * g) * inv_det, (c * d - a * f) * inv_det],
        [(d * h - e * g) * inv_det, (b * g - a * h) * inv_det, (a * e - b * d) * inv_det],
    ]


@dataclass
class JointSpec:
    origin_xyz: Tuple[float, float, float]
    origin_rpy: Tuple[float, float, float]
    axis: Tuple[float, float, float]


class DobotME6Kinematics:
    """Small FK/Jacobian model matching the official cra_description ME6 xacro."""

    def __init__(self):
        self.joints = [
            JointSpec((0.0, 0.0, 0.1268), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
            JointSpec((-0.046, 0.0, 0.04), (1.5708, 0.0, -1.5708), (0.0, 0.0, 1.0)),
            JointSpec((0.0, 0.18906, 0.003), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
            JointSpec((0.0, 0.16, 0.005), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
            JointSpec((0.0, 0.067, 0.032), (-1.5708, 1.5708, 0.0), (0.0, 0.0, 1.0)),
            JointSpec((-0.047, 0.0, 0.034), (1.5708, 0.0, -1.5708), (0.0, 0.0, 1.0)),
        ]
        self.tool_xyz = (0.0, 0.0, 0.0)

    def forward(self, q):
        pos = [0.0, 0.0, 0.0]
        rot = _eye(3)
        joint_positions = []
        joint_axes = []
        for theta, spec in zip(q, self.joints):
            pos = _add(pos, _matvec(rot, spec.origin_xyz))
            rot = _matmul(rot, _rpy_to_rot(spec.origin_rpy))
            axis_world = _matvec(rot, spec.axis)
            joint_positions.append(pos[:])
            joint_axes.append(axis_world)
            rot = _matmul(rot, _axis_angle(spec.axis, theta))
        tool_pos = _add(pos, _matvec(rot, self.tool_xyz))
        return tool_pos, joint_positions, joint_axes

    def jacobian_position(self, q):
        tool_pos, joint_positions, joint_axes = self.forward(q)
        columns = [_cross(axis, _sub(tool_pos, joint_pos)) for joint_pos, axis in zip(joint_positions, joint_axes)]
        return [[columns[col][row] for col in range(6)] for row in range(3)]

    def step_ik(self, q, target_pos, gain=2.0, damping=0.04, max_joint_step=0.035, posture_target=None, posture_gain=0.12):
        current_pos, _, _ = self.forward(q)
        error = _sub(target_pos, current_pos)
        v = _scale(error, gain)
        j = self.jacobian_position(q)
        jt = _transpose(j)
        jjt = _matmul(j, jt)
        for idx in range(3):
            jjt[idx][idx] += damping * damping
        task_step = _matvec(jt, _matvec(_inv3(jjt), v))

        if posture_target is not None:
            jj_pinv_j = _matmul(jt, _matmul(_inv3(jjt), j))
            null_projector = [[(1.0 if i == k else 0.0) - jj_pinv_j[i][k] for k in range(6)] for i in range(6)]
            posture_error = [_clamp(posture_target[i] - q[i], -0.5, 0.5) for i in range(6)]
            posture_step = _matvec(null_projector, _scale(posture_error, posture_gain))
            task_step = _add(task_step, posture_step)

        step_norm = _norm(task_step)
        if step_norm > max_joint_step:
            task_step = _scale(task_step, max_joint_step / step_norm)
        next_q = [_clamp(q[i] + task_step[i], JOINT_LIMITS[i][0], JOINT_LIMITS[i][1]) for i in range(6)]
        return next_q, _norm(error)


class TrajectoryClient(Node):
    def __init__(self, action_name, trajectory_topic="/me6_arm_controller/joint_trajectory"):
        super().__init__("dobot_me6_ee_trajectory_client")
        self.client = ActionClient(self, FollowJointTrajectory, action_name)
        self.publisher = self.create_publisher(JointTrajectory, trajectory_topic, 10)
        self.latest_joints = None
        self.create_subscription(JointState, "/joint_states", self._joint_state_cb, 10)

    def _joint_state_cb(self, msg):
        values = []
        for name in JOINT_NAMES:
            if name not in msg.name:
                return
            values.append(msg.position[msg.name.index(name)])
        self.latest_joints = values

    def wait_for_joints(self, timeout=2.0):
        deadline = time.time() + timeout
        while rclpy.ok() and time.time() < deadline and self.latest_joints is None:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.latest_joints

    def send_positions(self, positions, dt, verbose=True):
        if not self.client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("FollowJointTrajectory action server is not available.")
            return 1

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINT_NAMES
        for index, q in enumerate(positions, start=1):
            point = JointTrajectoryPoint()
            point.positions = q
            t = index * dt
            point.time_from_start.sec = int(t)
            point.time_from_start.nanosec = int((t - int(t)) * 1e9)
            goal.trajectory.points.append(point)

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected.")
            return 1

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result
        if verbose:
            self.get_logger().info(f"Result error_code={result.error_code}")
        return 0 if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL else 1

    def publish_positions(self, positions, dt):
        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES
        for index, q in enumerate(positions, start=1):
            point = JointTrajectoryPoint()
            point.positions = q
            t = index * dt
            point.time_from_start.sec = int(t)
            point.time_from_start.nanosec = int((t - int(t)) * 1e9)
            trajectory.points.append(point)
        self.publisher.publish(trajectory)
        return 0


def add_common_args(parser):
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument("--rate", type=float, default=20.0)
    parser.add_argument("--action-name", default="/me6_arm_controller/follow_joint_trajectory")
    parser.add_argument("--start", choices=("current", "ready", "home"), default="current")
    parser.add_argument("--gain", type=float, default=2.0)
    parser.add_argument("--damping", type=float, default=0.04)
    parser.add_argument("--max-joint-step", type=float, default=0.035)
    parser.add_argument("--z-offset", type=float, default=0.0)


def get_start_q(node, start):
    if start == "ready":
        return READY_Q[:]
    if start == "home":
        return HOME_Q[:]
    return node.wait_for_joints() or READY_Q[:]


def generate_joint_path(
    q0: Sequence[float],
    duration: float,
    rate: float,
    target_at: Callable[[float], Sequence[float]],
    gain: float,
    damping: float,
    max_joint_step: float,
    posture_target: Optional[Sequence[float]] = None,
):
    kin = DobotME6Kinematics()
    q = list(q0)
    dt = 1.0 / rate
    count = max(1, int(duration * rate))
    path = []
    max_error = 0.0
    for index in range(count):
        t = index * dt
        target = list(target_at(t))
        q, err = kin.step_ik(q, target, gain, damping, max_joint_step, posture_target)
        path.append(q[:])
        max_error = max(max_error, err)
    return path, max_error


def run_trajectory(name: str, args, target_factory):
    rclpy.init()
    node = TrajectoryClient(args.action_name)
    start_q = get_start_q(node, args.start)
    kin = DobotME6Kinematics()
    center, _, _ = kin.forward(start_q)
    center[2] += args.z_offset
    target_at = target_factory(center)
    path, max_error = generate_joint_path(
        start_q,
        args.duration,
        args.rate,
        target_at,
        args.gain,
        args.damping,
        args.max_joint_step,
    )
    node.get_logger().info(f"{name}: generated {len(path)} points, max position error estimate={max_error:.4f} m")
    rc = node.send_positions(path, 1.0 / args.rate)
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(rc)


def positive_float(value):
    parsed = float(value)
    if parsed <= 0.0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed
