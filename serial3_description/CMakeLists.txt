cmake_minimum_required(VERSION 3.16)
project(serial3_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  # Comprobamos que el Xacro genera un URDF válido para cada tipo de hardware
  find_program(XACRO_EXE xacro REQUIRED)
  find_program(CHECK_URDF_EXE check_urdf REQUIRED)
  foreach(hw mock gazebo real)
    add_test(
      NAME check_urdf_${hw}
      COMMAND sh -c "${XACRO_EXE} ${CMAKE_CURRENT_SOURCE_DIR}/urdf/serial3.urdf.xacro hw:=${hw} > ${CMAKE_CURRENT_BINARY_DIR}/serial3_${hw}.urdf && ${CHECK_URDF_EXE} ${CMAKE_CURRENT_BINARY_DIR}/serial3_${hw}.urdf"
    )
  endforeach()
endif()

ament_package()
