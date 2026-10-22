#!/usr/bin/env python3
"""Preserve scan start and per-point nanoseconds; do not filter or retime scans."""
import copy
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2
from livox_ros_driver2.msg import CustomMsg, CustomPoint
from experiment7_core.cloud import records, xyz_array


class Adapter(Node):
    def __init__(self):
        super().__init__('experiment8_livox_adapter')
        self.pub=self.create_publisher(CustomMsg,'/livox/lidar',20)
        self.create_subscription(PointCloud2,'/livox/points',self.convert,qos_profile_sensor_data)
        self.reported=False

    def convert(self,msg):
        try:
            points=records(msg)
            required={'x','y','z','intensity','offset_time','tag','line'}
            if not required.issubset(points.dtype.names):
                raise ValueError('Raw fields are missing: use /livox/points, not an XYZ-only filtered cloud')
            if len(points)==0 or not np.isfinite(xyz_array(points)).all():
                raise ValueError('Empty or nonfinite raw scan')
            offsets=points['offset_time'].astype(np.int64)
            if np.any(np.diff(offsets)<0) or offsets[-1]>=200_000_000:
                raise ValueError('Per-point nanoseconds are unordered or outside the 5 Hz scan')
            out=CustomMsg();out.header=copy.deepcopy(msg.header)
            out.timebase=msg.header.stamp.sec*1_000_000_000+msg.header.stamp.nanosec
            out.point_num=len(points);out.lidar_id=0
            for p in points:
                q=CustomPoint();q.x=float(p['x']);q.y=float(p['y']);q.z=float(p['z'])
                q.offset_time=int(p['offset_time']);q.reflectivity=int(np.clip(p['intensity'],0,255))
                q.tag=int(p['tag']);q.line=int(p['line']);out.points.append(q)
            self.pub.publish(out)
            if not self.reported:
                self.get_logger().info('Raw scan -> Livox CustomMsg; scan start and point nanoseconds preserved')
                self.reported=True
        except (ValueError,KeyError) as exc:
            self.get_logger().error(str(exc))


def main():
    rclpy.init();node=Adapter()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()


if __name__=='__main__':main()
