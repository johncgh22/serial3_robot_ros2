"""Visualiza el robot serial3 en RViz2 con deslizadores para cada junta."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('serial3_description')

    gui = LaunchConfiguration('gui')
    model = LaunchConfiguration('model')
    rviz_config = LaunchConfiguration('rviz_config')

    declare_args = [
        DeclareLaunchArgument(
            'gui', default_value='true',
            description='Muestra los deslizadores de joint_state_publisher_gui'),
        DeclareLaunchArgument(
            'model',
            default_value=PathJoinSubstitution([pkg_share, 'urdf', 'serial3.urdf.xacro']),
            description='Ruta al archivo Xacro/URDF del robot'),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=PathJoinSubstitution([pkg_share, 'rviz', 'serial3.rviz']),
            description='Configuración de RViz2'),
    ]

    # Generamos el URDF a partir del Xacro
    robot_description = ParameterValue(Command(['xacro ', model]), value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    # Con gui:=true usamos los deslizadores; con gui:=false todas las juntas quedan en 0
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        condition=IfCondition(gui),
    )
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        condition=UnlessCondition(gui),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
    )

    return LaunchDescription(declare_args + [
        robot_state_publisher,
        joint_state_publisher_gui,
        joint_state_publisher,
        rviz,
    ])
