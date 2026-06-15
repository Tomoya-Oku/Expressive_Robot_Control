from setuptools import setup

package_name = "dobot_me6_driver"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/real_validation.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Homework-3",
    maintainer_email="student@example.com",
    description="Guarded TCP bridge utilities for DOBOT ME6 hardware validation.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "me6_trajectory_bridge = dobot_me6_driver.me6_trajectory_bridge:main",
            "safety_check = dobot_me6_driver.safety_check:main",
        ],
    },
)
