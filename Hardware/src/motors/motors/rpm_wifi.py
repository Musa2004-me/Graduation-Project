#!/usr/bin/env python3

import threading

from flask import Flask, request

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


app = Flask(__name__)


class RPMCommander(Node):

    def __init__(self):
        super().__init__('rpm_web_commander')

        self.left_pub = self.create_publisher(
            Float32,
            '/left_rpm_setpoint',
            10
        )

        self.right_pub = self.create_publisher(
            Float32,
            '/right_rpm_setpoint',
            10
        )

    def send_rpm(self, left, right):

        msg_l = Float32()
        msg_l.data = float(left)

        msg_r = Float32()
        msg_r.data = float(right)

        self.left_pub.publish(msg_l)
        self.right_pub.publish(msg_r)

        self.get_logger().info(
            f'Left={left} Right={right}'
        )


node = None


@app.route('/')
def home():

    return """
    <h2>RPM Control</h2>

    <form action="/send" method="post">
      Left RPM:
      <input name="left"><br><br>

      Right RPM:
      <input name="right"><br><br>

      <button type="submit">Send</button>
    </form>

    <br>

    <form action="/stop" method="post">
      <button type="submit">STOP</button>
    </form>
    """


@app.route('/send', methods=['POST'])
def send():

    left = float(request.form['left'])
    right = float(request.form['right'])

    node.send_rpm(left, right)

    return f"Sent {left}, {right}"


@app.route('/stop', methods=['POST'])
def stop():

    node.send_rpm(0, 0)

    return "STOP SENT"


def ros_spin():

    rclpy.spin(node)


def main():

    global node

    rclpy.init()

    node = RPMCommander()

    threading.Thread(
        target=ros_spin,
        daemon=True
    ).start()

    app.run(
        host='0.0.0.0',
        port=5000
    )


if __name__ == '__main__':
    main()