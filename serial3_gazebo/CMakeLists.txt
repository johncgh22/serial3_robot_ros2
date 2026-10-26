cmake_minimum_required(VERSION 3.16)
project(serial3_gazebo)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
