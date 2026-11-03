#!/usr/bin/env python3
"""Bounded simulation motion, measured on /clock rather than wall time."""
import argparse
import math
import time
import rclpy
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vx', type=float, default=0.)
    parser.add_argument('--yaw-rate', type=float, default=0.)
    parser.add_argument('--seconds', type=float, default=1.)
    args = parser.parse_args()
    if (not all(math.isfinite(x) for x in (args.vx, args.yaw_rate, args.seconds))
            or abs(args.vx) > .2 or abs(args.yaw_rate) > .4 or not 0 <= args.seconds <= 10):
        parser.error('limits: |vx|<=0.2, |yaw-rate|<=0.4, seconds 0..10')
    rclpy.init()
    node = rclpy.create_node('experiment8_drive_for', parameter_overrides=[
        Parameter('use_sim_time', Parameter.Type.BOOL, True)])
    publisher = node.create_publisher(Twist, '/r1/cmd_vel', 10)
    try:
        deadline = time.monotonic()+10
        while publisher.get_subscription_count() == 0 or node.get_clock().now().nanoseconds == 0:
            if time.monotonic() >= deadline:
                raise RuntimeError('No simulation subscriber or /clock; start Experiment8 first')
            rclpy.spin_once(node, timeout_sec=.02)
        command = Twist()
        command.linear.x, command.angular.z = args.vx, args.yaw_rate
        start = previous = node.get_clock().now().nanoseconds
        end = start+round(args.seconds*1e9)
        last_progress = time.monotonic()
        deadline = time.monotonic()+max(20., args.seconds*8.+10.)
        while node.get_clock().now().nanoseconds < end:
            now = node.get_clock().now().nanoseconds
            if now < previous:
                raise RuntimeError('Simulation clock reset during motion')
            if now > previous:
                last_progress = time.monotonic()
            if time.monotonic()-last_progress > 3 or time.monotonic() > deadline:
                raise RuntimeError('Simulation clock stalled or motion watchdog expired')
            publisher.publish(command)
            previous = now
            rclpy.spin_once(node, timeout_sec=.02)
    except KeyboardInterrupt:
        pass
    finally:
        for _ in range(10):
            publisher.publish(Twist())
            rclpy.spin_once(node, timeout_sec=.02)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
