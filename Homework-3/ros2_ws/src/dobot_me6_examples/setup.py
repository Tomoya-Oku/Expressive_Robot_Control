from setuptools import setup

package_name = "dobot_me6_examples"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Homework-3",
    maintainer_email="student@example.com",
    description="Example ROS 2 clients for DOBOT ME6 homework validation.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "send_joint_goal = dobot_me6_examples.send_joint_goal:main",
        ],
    },
)
