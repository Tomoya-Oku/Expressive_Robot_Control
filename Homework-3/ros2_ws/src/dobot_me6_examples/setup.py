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
            "ee_circle = dobot_me6_examples.ee_circle:main",
            "ee_figure8 = dobot_me6_examples.ee_figure8:main",
            "ee_kanji_bara = dobot_me6_examples.ee_kanji_bara:main",
            "ee_kanji_bi = dobot_me6_examples.ee_kanji_bi:main",
            "ee_kanji_biang = dobot_me6_examples.ee_kanji_biang:main",
            "ee_kanji_biang_biang_men = dobot_me6_examples.ee_kanji_biang_biang_men:main",
            "ee_kanji_men = dobot_me6_examples.ee_kanji_men:main",
            "ee_kanji_shou = dobot_me6_examples.ee_kanji_shou:main",
            "ee_keyboard = dobot_me6_examples.ee_keyboard:main",
            "ee_line = dobot_me6_examples.ee_line:main",
            "ee_marker = dobot_me6_examples.ee_marker:main",
            "ee_mocap_mimic = dobot_me6_examples.ee_mocap_mimic:main",
            "send_joint_goal = dobot_me6_examples.send_joint_goal:main",
        ],
    },
)
