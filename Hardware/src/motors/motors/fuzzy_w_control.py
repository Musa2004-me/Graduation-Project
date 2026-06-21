#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32

class GeneralFuzzyAngularController(Node):

    def __init__(self):
        super().__init__('general_fuzzy_angular_controller')

        # ==========================
        # Robot Parameters
        # ==========================
        self.declare_parameter('wheel_radius', 0.3683 / 2.0) # m 
        self.declare_parameter('track_width', 0.405) # m

        self.R = self.get_parameter('wheel_radius').value
        self.TW = self.get_parameter('track_width').value

        # ==========================
        # ROS Subscribers & Publishers
        # ==========================
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        
        self.left_pub = self.create_publisher(Float32, '/left_rpm_setpoint', 10)
        self.right_pub = self.create_publisher(Float32, '/right_rpm_setpoint', 10)

        # ==========================
        # Controller State
        # ==========================
        self.current_w = 0.0  # السرعة الزاوية الحالية من الـ IMU
        self.prev_error = 0.0

        self.get_logger().info(f"General Fuzzy Angular Controller Started | R={self.R}m, TW={self.TW}m")

    # ==========================
    # IMU Callback (قراءة السرعة الزاوية مباشرة)
    # ==========================
    def imu_callback(self, msg):
        # بناخد سرعة الدوران حول محور Z مباشرة بالـ rad/s
        self.current_w = msg.angular_velocity.z

    # ==========================
    # Main Control Loop
    # ==========================
    def cmd_callback(self, msg):
        V_cmd = msg.linear.x   # السرعة الخطية المطلوبة (m/s)
        W_cmd = msg.angular.z  # السرعة الزاوية المطلوبة (rad/s)

        # السرعة الأساسية للعجلتين بناءً على الحركة الطولية
        v_base = V_cmd 

        # 1. حساب الخطأ في السرعة الزاوية (المطلوب - الحالي)
        e = W_cmd - self.current_w
        
        # 2. حساب معدل تغير الخطأ
        de = e - self.prev_error
        self.prev_error = e

        # 3. حساب قيمة التصحيح من الفازي 
        fuzzy_output = self.fuzzy_rule_base(e, de)

        # 4. تطبيق منطقك (تثبيت عجلة وزيادة التانية) بناءً على إشارة الخطأ
        # الـ fuzzy_output هنا بيمثل سرعة خطية إضافية (m/s) لتسريع العجلة المناسبة
        if e > 0:
            # الروبوت محتاج يلف شمال أكتر (أو انحرف يمين ومحتاج يصحح شمال)
            # بنثبت العجلة الشمال، ونزود سرعة العجلة اليمين عشان تدفعه للشمال
            v_left = v_base
            v_right = v_base + abs(fuzzy_output)
        elif e < 0:
            # الروبوت محتاج يلف يمين أكتر (أو انحرف شمال ومحتاج يصحح يمين)
            # بنثبت العجلة اليمين، ونزود سرعة العجلة الشمال عشان تدفعه لليمين
            v_right = v_base
            v_left = v_base + abs(fuzzy_output)
        else:
            # الخطأ صفر تماماً، العجلتين يمشوا بنفس السرعة الأساسية
            v_left = v_base
            v_right = v_base

        # ==========================
        # تحويل السرعات الخطية إلى RPM
        # ==========================
        left_rpm = (v_left * 60.0) / (2.0 * math.pi * self.R)
        right_rpm = (v_right * 60.0) / (2.0 * math.pi * self.R)

        # حماية المواتير: منع القيم السالبة تماماً (دوران للأمام فقط)
        left_rpm = max(0.0, left_rpm)
        right_rpm = max(0.0, right_rpm)

        # نشر القيم للمواتير
        left_msg = Float32()
        right_msg = Float32()
        left_msg.data = float(left_rpm)
        right_msg.data = float(right_rpm)

        self.left_pub.publish(left_msg)
        self.right_pub.publish(right_msg)

    # ==========================
    # FUZZY RULE BASE (الجدول الخاص بك)
    # ==========================
    def fuzzy_rule_base(self, e, de):
        e_set = self.fuzzify(e)
        de_set = self.fuzzify(de)

        rules = {
            'NB': {'NB': 'NB', 'NS': 'NB', 'Z': 'NB', 'PS': 'NS', 'PB': 'Z'},
            'NS': {'NB': 'NB', 'NS': 'NB', 'Z': 'NS', 'PS': 'Z',  'PB': 'PS'},
            'Z':  {'NB': 'NB', 'NS': 'NS', 'Z': 'Z',  'PS': 'PS', 'PB': 'PB'},
            'PS': {'NB': 'NS', 'NS': 'Z',  'Z': 'PS', 'PS': 'PB', 'PB': 'PB'},
            'PB': {'NB': 'Z',  'NS': 'PS', 'Z': 'PB', 'PS': 'PB', 'PB': 'PB'}
        }

        output_set = rules[e_set][de_set]
        return self.defuzzify(output_set)

    # ==========================
    # FUZZIFICATION 
    # ==========================
    def fuzzify(self, x):
        # بما إننا بنقيس سرعة زاوية (rad/s)، يفضل نشتغل بالـ rad/s علطول في الشروط
        # القيم دي (0.5 و 0.1) بتمثل حدود الخطأ في سرعة الدوران راديان/ثانية
        if x < -0.5:    return 'NB'
        elif x < -0.1:   return 'NS'
        elif x < 0.1:    return 'Z'
        elif x < 0.5:    return 'PS'
        else:            return 'PB'

    # ==========================
    # DEFUZZIFICATION (الخارج بالمتر/ثانية)
    # ==========================
    def defuzzify(self, label):
        # القيم دي هي السرعة الإضافية اللي هتتزود على العجلة السريعة
        # لو الروبوت استجابته بطيئة في الدوران أو تعديل المسار، كبّر الأرقام دي (مثلاً خلي الـ PB بـ 0.3)
        mapping = {
            'NB': -0.2,
            'NS': -0.05,
            'Z':   0.0,
            'PS':  0.05,
            'PB':  0.2
        }
        return mapping[label]


def main(args=None):
    rclpy.init(args=args)
    node = GeneralFuzzyAngularController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()