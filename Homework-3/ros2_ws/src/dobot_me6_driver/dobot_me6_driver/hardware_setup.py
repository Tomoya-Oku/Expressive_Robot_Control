import argparse
import os
import socket
import sys

from .dobot_dashboard_client import DobotDashboardClient


DEFAULT_IP = os.getenv("DOBOT_ME6_IP", "192.168.5.1")
DEFAULT_DASHBOARD_PORT = int(os.getenv("DOBOT_ME6_DASHBOARD_PORT", "29999"))
DEFAULT_MOTION_PORT = int(os.getenv("DOBOT_ME6_MOTION_PORT", "30003"))
DEFAULT_FEEDBACK_PORT = int(os.getenv("DOBOT_ME6_FEEDBACK_PORT", "30004"))


def tcp_check(host: str, port: int, timeout: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "open"
    except OSError as exc:
        return False, str(exc)


def send_dashboard_sequence(
    host: str,
    dashboard_port: int,
    timeout: float,
    speed_ratio: float,
    enable: bool,
) -> bool:
    commands = ["RequestControl()", "ClearError()", f"SpeedFactor({speed_ratio:.1f})"]
    if enable:
        commands.append("EnableRobot()")

    ok = True
    with DobotDashboardClient(
        host,
        dashboard_port,
        timeout=timeout,
        dry_run=False,
    ) as client:
        for command in commands:
            response = client.send(command)
            print(f"{command} -> {response}")
            if response.startswith("-") or "refused" in response.lower():
                ok = False
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ME6 hardware setup helper for TCP/IP connection checks."
    )
    parser.add_argument("--robot-ip", default=DEFAULT_IP)
    parser.add_argument("--dashboard-port", type=int, default=DEFAULT_DASHBOARD_PORT)
    parser.add_argument("--motion-port", type=int, default=DEFAULT_MOTION_PORT)
    parser.add_argument("--feedback-port", type=int, default=DEFAULT_FEEDBACK_PORT)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--speed-ratio", type=float, default=10.0)
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Send RequestControl, ClearError, SpeedFactor, and optionally EnableRobot.",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Also send EnableRobot when --prepare is used.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    checks = [
        ("dashboard", args.dashboard_port),
        ("motion", args.motion_port),
        ("feedback", args.feedback_port),
    ]

    print(f"ME6 IP: {args.robot_ip}")
    all_open = True
    for label, port in checks:
        ok, message = tcp_check(args.robot_ip, port, args.timeout)
        status = "OK" if ok else "NG"
        print(f"{status}: {label} port {port}: {message}")
        all_open = all_open and ok

    if args.prepare:
        if not tcp_check(args.robot_ip, args.dashboard_port, args.timeout)[0]:
            print("NG: dashboard port is not reachable, so setup commands were not sent.")
            return 1
        command_ok = send_dashboard_sequence(
            args.robot_ip,
            args.dashboard_port,
            args.timeout,
            args.speed_ratio,
            args.enable,
        )
        if not command_ok:
            print("NG: one or more setup commands were refused by the robot controller.")
            return 1

    if not all_open:
        print(
            "Hint: If dashboard is open but motion/feedback is refused, enable TCP/IP "
            "remote mode on the robot controller or vendor app, then retry."
        )
        return 1

    print("OK: required TCP ports are reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
