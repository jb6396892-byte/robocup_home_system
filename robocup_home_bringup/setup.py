from glob import glob
from setuptools import find_packages, setup

package_name = 'robocup_home_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*') + ['../config/object_classes.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='smg',
    maintainer_email='smg@example.com',
    description='Unified Stage 0/1 bringup and diagnostics.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'twist_stamper = robocup_home_bringup.twist_stamper:main',
            'health_check = robocup_home_bringup.health_check:main',
            'stage1_smoke_test = robocup_home_bringup.stage1_smoke_test:main',
        ],
    },
)
