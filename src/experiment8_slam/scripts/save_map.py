#!/usr/bin/env python3
"""Request the mapper's configured output path and report failures."""
import rclpy
from std_srvs.srv import Trigger


def main():
    rclpy.init();node=rclpy.create_node('experiment8_save_map')
    try:
        client=node.create_client(Trigger,'/map_save')
        if not client.wait_for_service(timeout_sec=10):raise RuntimeError('未找到/map_save，请先启动实验8。')
        future=client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(node,future,timeout_sec=20)
        if not future.done():raise RuntimeError('保存地图超时。')
        response=future.result()
        if not response.success:raise RuntimeError(response.message)
        print('地图已保存到启动时 map_path 指定的文件。')
    finally:
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()


if __name__=='__main__':main()
