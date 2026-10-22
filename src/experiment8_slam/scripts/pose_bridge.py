#!/usr/bin/env python3
"""FAST-LIO body is the co-located IMU; base_link is 1.3 m below it."""
import rclpy
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster


def main():
    rclpy.init();node=rclpy.create_node('experiment8_pose_bridge')
    broadcaster=StaticTransformBroadcaster(node)
    t=TransformStamped();t.header.stamp=node.get_clock().now().to_msg()
    t.header.frame_id='body';t.child_frame_id='base_link'
    t.transform.translation.z=-1.3;t.transform.rotation.w=1.
    broadcaster.sendTransform(t)
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()


if __name__=='__main__':main()
