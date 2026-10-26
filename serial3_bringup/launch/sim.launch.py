"""Simula el robot serial3 en Gazebo Sim con sus controladores de ros2_control."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, OpaqueFunction)
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def gazebo(context):
    """Incluye Gazebo Sim; con gui:=false solo arranca el servidor (sin ventana)."""
    world = LaunchConfiguration('world').perform(context)
    gui = LaunchConfiguration('gui').perform(context).lower() == 'true'
    gz_args = f'-r -v 3 {world}' if gui else f'-r -s -v 3 {world}'
    return [IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
        launch_arguments={'gz_args': gz_args, 'on_exit_shutdown': 'true'}.items(),
    )]


def generate_launch_description():
    description_share = FindPackageShare('serial3_description')
    bringup_share = FindPackageShare('serial3_bringup')

    rviz = LaunchConfiguration('rviz')
    controllers_file = PathJoinSubstitution([bringup_share, 'config', 'serial3_controllers.yaml'])

    declare_args = [
        DeclareLaunchArgument('gui', default_value='true', description='Muestra la ventana de Gazebo'),
        DeclareLaunchArgument('rviz', default_value='false', description='Abre RViz2'),
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [FindPackageShare('serial3_gazebo'), 'worlds', 'serial3_empty.sdf']),
            description='Mundo SDF de Gazebo'),
    ]

    # Gazebo resuelve package://serial3_description/... buscando en esta ruta
    resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(get_package_share_directory('serial3_description')),
    )

    robot_description = ParameterValue(
        Command([
            'xacro ', PathJoinSubstitution([description_share, 'urdf', 'serial3.urdf.xacro']),
            ' hw:=gazebo controllers_file:=', controllers_file,
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen',
    )

    # Coloca el robot en Gazebo a partir del tópico /robot_description
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'serial3'],
        output='screen',
    )

    # Pasa el reloj de la simulación a ROS
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    # El controller_manager lo crea el plugin gz_ros2_control al aparecer el robot
    spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster', 'arm_controller',
            '--param-file', controllers_file,
            '--controller-manager-timeout', '60',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([description_share, 'rviz', 'serial3.rviz'])],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(rviz),
    )

    return LaunchDescription(declare_args + [
        resource_path,
        OpaqueFunction(function=gazebo),
        robot_state_publisher,
        clock_bridge,
        spawn_robot,
        spawner,
        rviz_node,
    ])
