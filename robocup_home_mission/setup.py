from setuptools import find_packages, setup

package_name = 'robocup_home_mission'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='SEU RoboCup Home Team',
    maintainer_email='jb6396892-byte@users.noreply.github.com',
    description='目标输入、任务状态机、时间控制和结果冻结。',
    license='Apache-2.0',
)
