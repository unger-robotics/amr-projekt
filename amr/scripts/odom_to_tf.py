#!/usr/bin/env python3
"""Bruecke: /odom (nav_msgs/Odometry) -> /tf (odom -> base_link)

micro-ROS publiziert nur die /odom-Nachricht, aber keinen TF.
SLAM/Nav2 benoetigen den dynamischen TF odom -> base_link.
Dieser Node abonniert /odom und sendet den entsprechenden TF-Broadcast.
"""

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class OdomToTf(Node):
    def __init__(self):
        super().__init__("odom_to_tf")
        self.tf_broadcaster = TransformBroadcaster(self)
        self._odom_received = False
        self.sub = self.create_subscription(Odometry, "odom", self.odom_cb, 10)

        # Identity-Transform sofort publizieren, damit Nav2/SLAM keinen
        # Timeout beim Start bekommen, bevor die erste /odom-Nachricht eintrifft.
        self._publish_identity()
        self._init_timer = self.create_timer(0.5, self._publish_identity)

    def _publish_identity(self):
        """Publiziert Identity-TF odom->base_link bis echte Odometrie eintrifft."""
        if self._odom_received:
            self._init_timer.cancel()
            return
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)

    def odom_cb(self, msg):
        if not self._odom_received:
            self._odom_received = True
            self.get_logger().info("Erste /odom empfangen, Identity-TF abgeloest")
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


if __name__ == "__main__":
    main()
