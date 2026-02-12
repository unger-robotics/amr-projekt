import os
from glob import glob
from setuptools import setup

package_name = 'my_bot'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jan',
    maintainer_email='student@university.de',
    description='AMR navigation and control package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'aruco_docking = my_bot.aruco_docking:main',
            'encoder_test = my_bot.encoder_test:main',
            'motor_test = my_bot.motor_test:main',
            'pid_tuning = my_bot.pid_tuning:main',
            'kinematic_test = my_bot.kinematic_test:main',
            'slam_validation = my_bot.slam_validation:main',
            'nav_test = my_bot.nav_test:main',
            'docking_test = my_bot.docking_test:main',
        ],
    },
)
