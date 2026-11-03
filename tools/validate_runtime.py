#!/usr/bin/env python3
"""Validate a running Experiment8 simulator; drives a short, bounded indoor route."""
import argparse
from collections import Counter, deque
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry, Path as RosPath
from sensor_msgs.msg import Imu, PointCloud2
from tf2_msgs.msg import TFMessage
from livox_ros_driver2.msg import CustomMsg
from experiment7_core.cloud import records, xyz_array
from experiment8_core.scene import BOXES


def stamp(msg):
    return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9


def pose(msg):
    p, q = msg.pose.pose.position, msg.pose.pose.orientation
    yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
    return np.array([p.x, p.y, p.z, yaw])


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='/root/exp8/data/validation_20261103/runtime.json')
    args = parser.parse_args()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = rclpy.create_node('experiment8_runtime_validation')
    counts = Counter()
    raw, custom = {}, {}
    imu_times, scans, pairs = deque(maxlen=30000), [], []
    truth, odom, edges, phases = [], [], set(), []
    latest = {}
    cloud_sizes = {'raw': [], 'registered': [], 'map': []}
    failures = []
    report = {'scope': 'Experiment2 teaching VM, idealized indoor simulation', 'checks': {}}

    def check(name, condition, details):
        report['checks'][name] = {'passed': bool(condition), 'details': details}
        if not condition:
            failures.append(name)

    def receive(name, msg):
        counts[name] += 1
        latest[name] = msg
        if name in cloud_sizes:
            cloud_sizes[name].append(int(msg.width*msg.height))

    def match(key):
        if key not in raw or key not in custom or len(pairs) >= 40:
            return
        a, b = raw.pop(key), custom.pop(key)
        points = records(a)
        xyz = np.array([[p.x, p.y, p.z] for p in b.points])
        same = (len(points) == b.point_num == len(b.points)
                and a.header == b.header
                and b.timebase == a.header.stamp.sec*1_000_000_000+a.header.stamp.nanosec
                and np.array_equal(xyz, xyz_array(points))
                and np.array_equal([p.offset_time for p in b.points], points['offset_time'])
                and np.array_equal([p.line for p in b.points], points['line'])
                and np.array_equal([p.tag for p in b.points], points['tag'])
                and np.array_equal([p.reflectivity for p in b.points], points['intensity']))
        pairs.append({'stamp': key, 'points': len(points), 'all_fields_preserved': bool(same)})
        offsets = points['offset_time'].astype(np.float64)*1e-9
        scans.append((key, key+float(offsets[-1])))

    def cloud_cb(msg):
        receive('raw', msg)
        if len(pairs) < 40:
            raw[stamp(msg)] = msg
            match(stamp(msg))

    def custom_cb(msg):
        receive('custom', msg)
        if len(pairs) < 40:
            custom[stamp(msg)] = msg
            match(stamp(msg))

    def imu_cb(msg):
        receive('imu', msg)
        imu_times.append(stamp(msg))

    def truth_cb(msg):
        receive('truth', msg)
        truth.append((stamp(msg), pose(msg)))

    def odom_cb(msg):
        receive('odom', msg)
        odom.append((stamp(msg), pose(msg)))

    def tf_cb(msg):
        for t in msg.transforms:
            edges.add((t.header.frame_id, t.child_frame_id))

    for topic, typ, cb, qos in [
        ('/livox/points', PointCloud2, cloud_cb, qos_profile_sensor_data),
        ('/livox/lidar', CustomMsg, custom_cb, 20),
        ('/livox/imu', Imu, imu_cb, QoSProfile(depth=500, reliability=ReliabilityPolicy.BEST_EFFORT)),
        ('/r1/ground_truth', Odometry, truth_cb, qos_profile_sensor_data),
        ('/Odometry', Odometry, odom_cb, 50),
        ('/Laser_map', PointCloud2, lambda m: receive('map', m), 10),
        ('/cloud_registered', PointCloud2, lambda m: receive('registered', m), 10),
        ('/path', RosPath, lambda m: receive('path', m), 10),
        ('/r1/cmd_vel', Twist, lambda m: receive('command', m), 10),
        ('/tf', TFMessage, tf_cb, 100),
        ('/tf_static', TFMessage, tf_cb, QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)),
    ]:
        node.create_subscription(typ, topic, cb, qos)
    publisher = node.create_publisher(Twist, '/r1/cmd_vel', 10)

    def spin(seconds):
        end = time.monotonic()+seconds
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=.02)

    def snapshot(name):
        t, e = truth[-1][1], odom[-1][1]
        row = {'name': name, 'truth': t.tolist(), 'estimated': e.tolist(),
               'truth_stamp': truth[-1][0], 'odom_stamp': odom[-1][0]}
        phases.append(row)
        print(json.dumps(row), flush=True)

    def drive(name, *arguments):
        process = subprocess.Popen(['ros2', 'run', 'experiment8_slam', 'drive_for.py', *arguments])
        deadline = time.monotonic()+60
        while process.poll() is None and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.02)
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
            raise RuntimeError('Bounded drive timed out: '+name)
        if process.returncode:
            raise RuntimeError('Drive command failed: '+name)
        spin(2)
        snapshot(name)

    try:
        deadline = time.monotonic()+60
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.02)
            if len(odom) >= 15 and 'map' in latest and truth and len(pairs) >= 10:
                break
        if not odom or 'map' not in latest or not truth:
            raise RuntimeError('No initialized SLAM output within 60 seconds: '+str(counts))
        spin(3)
        snapshot('stationary')
        drive('forward', '--vx', '.15', '--seconds', '2')
        drive('turn_left', '--yaw-rate', '.3', '--seconds', '1')
        drive('forward_turned', '--vx', '.15', '--seconds', '4')
        drive('reverse_turned', '--vx', '-.15', '--seconds', '4')
        drive('turn_back', '--yaw-rate', '-.3', '--seconds', '1')
        drive('return', '--vx', '-.15', '--seconds', '2')
        spin(2)
        snapshot('stopped')
        check('raw_to_custom', len(pairs) >= 20 and all(p['all_fields_preserved'] for p in pairs), pairs)
        it = np.array(imu_times)
        coverage = []
        for start, end in scans:
            segment = it[(it >= start-.006) & (it <= end+.006)]
            good = len(segment) > 2 and segment[0] <= start and segment[-1] >= end
            gap = float(np.diff(segment).max()) if len(segment) > 1 else None
            coverage.append({'start': start, 'end': end, 'covered': bool(good), 'max_gap': gap})
        warmup_end = scans[0][0]+2.
        eligible = [x for x in coverage if x['start'] >= warmup_end-1e-9]
        startup = [x for x in coverage if x['start'] < warmup_end-1e-9]
        check('imu_coverage', len(eligible) >= 20 and all(x['covered'] and x['max_gap'] <= .015+1e-9 for x in eligible),
              {'steady_scans': eligible, 'startup_partial_scans': startup,
               'warmup_sim_seconds': 2.,
               'note': 'Report discovery/render startup separately; validate IMU coverage after a fixed 2 s simulation warmup.'})

        a0 = np.array(phases[0]['estimated'])
        t0 = np.array(phases[0]['truth'])
        yaw_offset = t0[3]-a0[3]
        rotation = np.array([[math.cos(yaw_offset), -math.sin(yaw_offset)],
                             [math.sin(yaw_offset), math.cos(yaw_offset)]])
        errors = []
        for row in phases:
            est, tr = np.array(row['estimated']), np.array(row['truth'])
            xy = rotation @ (est[:2]-a0[:2]) + t0[:2]
            errors.append({'phase': row['name'], 'xy_m': float(np.linalg.norm(xy-tr[:2])),
                           'yaw_rad': abs(wrap(est[3]+yaw_offset-tr[3]))})
        check('pose_against_truth', all(x['xy_m'] < .10 and x['yaw_rad'] < .08 for x in errors),
              {'alignment': 'one initial planar alignment; never refit during motion', 'errors': errors})
        odom_values = np.array([p for _, p in odom])
        steps = np.linalg.norm(np.diff(odom_values[:, :3], axis=0), axis=1)
        dt = np.diff([t for t, _ in odom])
        check('continuous_odometry', np.isfinite(odom_values).all() and np.all(dt > 0) and steps.max() < .15,
              {'messages': len(odom), 'max_step_m': float(steps.max()), 'max_gap_s': float(dt.max())})
        truth_times = np.array([t for t, _ in truth])
        tracking = []
        for t, estimated in odom:
            if t < phases[0]['odom_stamp']:
                continue
            index = int(np.argmin(np.abs(truth_times-t)))
            if abs(truth_times[index]-t) > .02:
                continue
            reference = truth[index][1]
            xy = rotation @ (estimated[:2]-a0[:2])+t0[:2]
            tracking.append((float(np.linalg.norm(xy-reference[:2])),
                             abs(wrap(estimated[3]+yaw_offset-reference[3])),
                             abs((estimated[2]-a0[2])-(reference[2]-t0[2]))))
        tracking = np.array(tracking)
        check('tracking_at_matched_timestamps', len(tracking) > 100
              and tracking[:, 0].max() < .10 and tracking[:, 1].max() < .08 and tracking[:, 2].max() < .15,
              {'matched_samples': len(tracking), 'matching_tolerance_s': .02,
               'xy_rmse_m': float(np.sqrt(np.mean(tracking[:, 0]**2))),
               'xy_max_m': float(tracking[:, 0].max()), 'yaw_max_rad': float(tracking[:, 1].max()),
               'relative_z_max_m': float(tracking[:, 2].max())})
        check('height_stability', np.max(np.abs(odom_values[:, 2])) < .10,
              {'max_abs_z_m': float(np.max(np.abs(odom_values[:, 2]))),
               'reference': 'camera_init starts at the stationary IMU height; robot moves in a horizontal plane'})
        check('motion_observed', np.linalg.norm(np.array(phases[1]['truth'])[:2]-t0[:2]) > .15
              and abs(wrap(phases[2]['truth'][3]-phases[1]['truth'][3])) > .15, phases)
        check('stopped_command', 'command' in latest and abs(latest['command'].linear.x) < 1e-9
              and abs(latest['command'].angular.z) < 1e-9, {'count': counts['command']})
        wanted = {('camera_init', 'body'), ('body', 'base_link'), ('base_link', 'lidar_frame'), ('lidar_frame', 'imu_frame')}
        check('tf_chain', wanted.issubset(edges) and ('world', 'base_link') not in edges, sorted(edges))
        subscriptions = node.get_subscriber_names_and_types_by_node('laser_mapping', '/')
        check('no_truth_input_to_fastlio', '/r1/ground_truth' not in dict(subscriptions)
              and '/livox/lidar' in dict(subscriptions) and '/livox/imu' in dict(subscriptions), subscriptions)
        cloud = latest['map']
        xyz = xyz_array(records(cloud))
        world = xyz.copy()
        world[:, :2] = (rotation @ (xyz[:, :2]-a0[:2]).T).T+t0[:2]
        world[:, 2] += 1.3+t0[2]-a0[2]
        distances = []
        for _, center, size in BOXES:
            q = np.abs(world-np.array(center))-np.array(size)/2
            distance = np.linalg.norm(np.maximum(q, 0), axis=1)+np.minimum(np.max(q, axis=1), 0)
            distances.append(np.abs(distance))
        nearest = np.min(distances, axis=0)
        check('map_geometry', cloud.header.frame_id == 'camera_init' and len(xyz) > 1000
              and np.isfinite(xyz).all() and np.percentile(nearest, 95) < .10,
              {'points': len(xyz), 'frame': cloud.header.frame_id,
               'bounds': [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()],
               'surface_error_p50_m': float(np.percentile(nearest, 50)),
               'surface_error_p95_m': float(np.percentile(nearest, 95))})
        path = latest.get('path')
        check('path_and_registered_scan', path is not None and len(path.poses) >= 5
              and counts['registered'] >= 20, {'path_poses': len(path.poses) if path else 0, 'registered': counts['registered']})
        process = subprocess.Popen(['ros2', 'run', 'experiment8_slam', 'save_map.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        end = time.monotonic()+30
        while process.poll() is None and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=.02)
        if process.poll() is None:
            process.terminate()
        output, _ = process.communicate(timeout=5)
        pcd = Path('/root/exp8/maps/map.pcd')
        check('save_map_command', process.returncode == 0 and pcd.exists() and pcd.stat().st_size > 1000,
              {'exit': process.returncode, 'output': output.decode(errors='replace'),
               'path': str(pcd), 'bytes': pcd.stat().st_size if pcd.exists() else 0})
        np.savez_compressed(target.with_suffix('.npz'), map_xyz=xyz,
                            odom=np.array([[t, *p] for t, p in odom]), truth=np.array([[t, *p] for t, p in truth]))
    except Exception as exc:
        report['exception'] = repr(exc)
        failures.append('exception')
    finally:
        for _ in range(10):
            publisher.publish(Twist())
            rclpy.spin_once(node, timeout_sec=.02)
        report.update(status='PASS' if not failures else 'FAIL', failed_checks=failures,
                      message_counts=dict(counts), phases=phases,
                      cloud_sizes={name: {'samples': len(values), 'min': min(values), 'max': max(values),
                                          'median': float(np.median(values))}
                                   for name, values in cloud_sizes.items() if values})
        target.write_text(json.dumps(report, indent=2))
        print(json.dumps({'status': report['status'], 'failed_checks': failures, 'output': str(target)}), flush=True)
        node.destroy_node()
        rclpy.shutdown()
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
