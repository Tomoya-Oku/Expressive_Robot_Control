import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from sensor_msgs.msg import JointState
from visualization_msgs.msg import Marker, MarkerArray

from dobot_me6_examples.ee_control_common import DobotME6Kinematics, JOINT_NAMES


class EEMarkerPublisher(Node):
    def __init__(self):
        super().__init__("dobot_me6_ee_marker")
        self.kinematics = DobotME6Kinematics()
        self.trail = []
        self.max_trail_points = 300
        self.frame_id = self.declare_parameter("frame_id", "base_link").value
        self.publisher = self.create_publisher(MarkerArray, "me6_ee_marker", 10)
        self.create_subscription(JointState, "/joint_states", self.joint_state_callback, 10)

    def joint_state_callback(self, msg):
        if any(name not in msg.name for name in JOINT_NAMES):
            return
        q = [msg.position[msg.name.index(name)] for name in JOINT_NAMES]
        position, _, _ = self.kinematics.forward(q)
        self.trail.append(position)
        if len(self.trail) > self.max_trail_points:
            self.trail = self.trail[-self.max_trail_points :]
        self.publisher.publish(self.make_markers(position))

    def make_markers(self, position):
        now = self.get_clock().now().to_msg()
        markers = MarkerArray()
        markers.markers.append(self.make_sphere(position, now))
        markers.markers.append(self.make_trail(now))
        markers.markers.append(self.make_text(position, now))
        return markers

    def base_marker(self, marker_id, marker_type, now):
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = now
        marker.ns = "dobot_me6_ee"
        marker.id = marker_id
        marker.type = marker_type
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.lifetime.sec = 0
        return marker

    def make_sphere(self, position, now):
        marker = self.base_marker(0, Marker.SPHERE, now)
        marker.pose.position.x = position[0]
        marker.pose.position.y = position[1]
        marker.pose.position.z = position[2]
        marker.scale.x = 0.055
        marker.scale.y = 0.055
        marker.scale.z = 0.055
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.25
        marker.color.a = 0.95
        return marker

    def make_trail(self, now):
        marker = self.base_marker(1, Marker.LINE_STRIP, now)
        marker.scale.x = 0.012
        marker.color.r = 1.0
        marker.color.g = 0.65
        marker.color.b = 0.0
        marker.color.a = 0.9
        marker.points = [Point(x=p[0], y=p[1], z=p[2]) for p in self.trail]
        return marker

    def make_text(self, position, now):
        marker = self.base_marker(2, Marker.TEXT_VIEW_FACING, now)
        marker.pose.position.x = position[0]
        marker.pose.position.y = position[1]
        marker.pose.position.z = position[2] + 0.08
        marker.scale.z = 0.045
        marker.color.r = 0.1
        marker.color.g = 0.9
        marker.color.b = 1.0
        marker.color.a = 1.0
        marker.text = f"EE ({position[0]:+.3f}, {position[1]:+.3f}, {position[2]:+.3f}) m"
        return marker


def main():
    rclpy.init()
    node = EEMarkerPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
