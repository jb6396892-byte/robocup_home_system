cmake_minimum_required(VERSION 3.8)
project(robocup_home_description)

find_package(ament_cmake REQUIRED)
install(DIRECTORY config rviz urdf DESTINATION share/${PROJECT_NAME})
ament_package()
