import os
import socket
import sys

import rclpy
from rclpy.node import Node


class SafetyCheck(Node):
    def __init__(self):
        super().__init__("dobot_me6_safety_check")
        self.declare_parameter("robot_ip", os.getenv("DOBOT_ME6_IP", "192.168.5.1"))
        self.declare_parameter(
            "dashboard_port", int(os.getenv("DOBOT_ME6_DASHBOARD_PORT", "29999"))
        )
        self.declare_parameter("timeout", 2.0)

    def run(self) -> int:
        host = self.get_parameter("robot_ip").value
        port = self.get_parameter("dashboard_port").value
        timeout = self.get_parameter("timeout").value
        self.get_logger().info(f"Checking TCP connectivity to {host}:{port}")
        try:
            with socket.create_connection((host, port), timeout=timeout):
                self.get_logger().info("TCP connection succeeded. No motion command was sent.")
                return 0
        except OSError as exc:
            self.get_logger().error(f"TCP connection failed: {exc}")
            return 1


def main():
    rclpy.init()
    node = SafetyCheck()
    rc = node.run()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(rc)
