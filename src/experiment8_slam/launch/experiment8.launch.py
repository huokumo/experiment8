import os
from pathlib import Path
import shlex
import tempfile
import xml.etree.ElementTree as ET
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from experiment8_core.scene import generate


def setup(context):
    value=lambda key:LaunchConfiguration(key).perform(context)
    share=Path(get_package_share_directory('experiment8_slam'))
    exp7=Path(get_package_share_directory('experiment7_lidar'))
    exp5=Path(get_package_share_directory('experiment5_depth'))
    runtime=Path(tempfile.mkdtemp(prefix='experiment8_'))
    world=generate(exp5,runtime/'experiment8.sdf',str(exp7/'vendor/livox/mid360.csv'))
    robot_description=ET.tostring(ET.parse(exp5/'description/r1_depth.urdf').getroot(),encoding='unicode')
    gui=value('gui').lower()
    if gui not in ('true','false'):raise ValueError('gui must be true or false')
    path=Path(value('map_path')).expanduser().resolve();path.parent.mkdir(parents=True,exist_ok=True)
    actions=[SetEnvironmentVariable('PYTHONNOUSERSITE','1'),SetEnvironmentVariable('LIBGL_ALWAYS_SOFTWARE','1'),
        SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH',str(exp5/'models')+os.pathsep+os.environ.get('IGN_GAZEBO_RESOURCE_PATH','')),
        SetEnvironmentVariable('IGN_GAZEBO_SYSTEM_PLUGIN_PATH',str(Path(get_package_prefix('experiment7_lidar'))/'lib')+os.pathsep+os.environ.get('IGN_GAZEBO_SYSTEM_PLUGIN_PATH','')),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(Path(get_package_share_directory('ros_gz_sim'))/'launch/gz_sim.launch.py')),
            launch_arguments={'gz_args':('-r -v 2 ' if gui=='true' else '-s -r -v 2 ')+shlex.quote(world),
                              'gz_version':'6','on_exit_shutdown':'true'}.items()),
        Node(package='ros_gz_bridge',executable='parameter_bridge',name='experiment8_bridge',
             parameters=[{'config_file':str(exp7/'config/bridge.yaml'),'use_sim_time':True}],output='screen'),
        Node(package='robot_state_publisher',executable='robot_state_publisher',
             parameters=[{'use_sim_time':True,'robot_description':ParameterValue(robot_description,value_type=str)}]),
        Node(package='experiment7_lidar',executable='state_node.py',
             parameters=[{'use_sim_time':True,'publish_truth_tf':False}]),
        Node(package='experiment8_slam',executable='livox_adapter.py',parameters=[{'use_sim_time':True}],output='screen'),
        Node(package='fast_lio',executable='fastlio_mapping',parameters=[str(share/'config/fastlio_sim.yaml'),
            {'use_sim_time':True,'map_file_path':str(path)}],output='screen'),
        Node(package='experiment8_slam',executable='pose_bridge.py',parameters=[{'use_sim_time':True}])]
    rviz=value('rviz').lower()
    if rviz not in ('true','false'):raise ValueError('rviz must be true or false')
    if rviz=='true':
        actions.append(Node(package='rviz2',executable='rviz2',arguments=['-d',str(share/'config/experiment8.rviz')],parameters=[{'use_sim_time':True}]))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gui',default_value='true'),
        DeclareLaunchArgument('rviz',default_value='true'),
        DeclareLaunchArgument('map_path',default_value=str(Path.home()/'experiment8_maps/map.pcd')),
        OpaqueFunction(function=setup)])
