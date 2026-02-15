#!/usr/bin/env python3
"""Bruecke: /odom (nav_msgs/Odometry) -> /tf (odom -> base_link)

micro-ROS publiziert nur die /odom-Nachricht, aber keinen TF.
SLAM/Nav2 benoetigen den dynamischen TF odom -> base_link.
Dieser Node abonniert /odom und sendet den entsprechenden TF-Broadcast.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class OdomToTf(Node):
    def __init__(self):
        super().__init__('odom_to_tf')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.sub = self.create_subscription(Odometry, 'odom', self.odom_cb, 10)

    def odom_cb(self, msg):
        t = TransformStamped()
        t.header = msg.header
        t.child_frame_id = msg.child_frame_id
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
