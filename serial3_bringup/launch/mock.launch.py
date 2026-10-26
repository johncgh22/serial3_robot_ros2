"""Arranca ros2_control con hardware mock (sin simulador) para probar los controladores."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description_share = FindPackageShare('serial3_description')
    bringup_share = FindPackageShare('serial3_bringup')

    rviz = LaunchConfiguration('rviz')

    controllers_file = PathJoinSubstitution([bringup_share, 'config', 'serial3_controllers.yaml'])
    mock_overrides = PathJoinSubstitution([bringup_share, 'config', 'serial3_controllers_mock.yaml'])

    robot_description = ParameterValue(
        Command([
            'xacro ', PathJoinSubstitution([description_share, 'urdf', 'serial3.urdf.xacro']),
            ' hw:=mock',
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    # El controller_manager lee el robot_description del tópico de robot_state_publisher
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[controllers_file, mock_overrides],
        output='screen',
    )

    spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster', 'arm_controller',
            '--param-file', controllers_file,
            '--param-file', mock_overrides,
        ],
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([description_share, 'rviz', 'serial3.rviz'])],
        condition=IfCondition(rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true', description='Abre RViz2'),
        robot_state_publisher,
        controller_manager,
        spawner,
        rviz_node,
    ])
