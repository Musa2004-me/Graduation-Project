#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32
 
class FullFuzzyYawVelocityController(Node):
    def __init__(self):
        super().__init__('full_fuzzy_yaw_velocity_controller')
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
        self.error_pub = self.create_publisher(Float32, '/controller/error', 10)
        self.delta_error_pub = self.create_publisher(Float32, '/controller/delta_error', 10)
        
        # ==========================
        # Controller State
        # ==========================
        self.current_yaw = 0.0  
        self.current_w = 0.0    
        self.prev_error = 0.0
        self.desired_yaw = 0.0
        self.is_going_straight = False
        
        # --- NEW STATE VARIABLES FOR INCREMENTAL SPEED ---
        self.v_left = 0.0
        self.v_right = 0.0
        self.prev_v_base = 0.0
        
        # Time tracking for accurate derivative calculation
        self.prev_time = self.get_clock().now()

        self.get_logger().info(f"Full Fuzzy Controller Started | Accumulating Mode (Fixed Sign Logic)")

    def imu_callback(self, msg):
        self.current_w = msg.angular_velocity.z
        q = msg.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def normalize_angle(self, a):
        while a > math.pi:  a -= 2.0 * math.pi
        while a < -math.pi: a += 2.0 * math.pi
        return a

    # ==========================
    # Main Control Loop (Callback)
    # ==========================
    def cmd_callback(self, msg):
        V_cmd = msg.linear.x   
        W_cmd = msg.angular.z  
        v_base = V_cmd 
        
        # --- CALCULATE DELTA TIME (dt) ---
        current_time = self.get_clock().now()
        dt = (current_time - self.prev_time).nanoseconds / 1e9
        if dt <= 0.0: 
            dt = 0.05
        self.prev_time = current_time

        # --- STEP 1: INITIALIZE WITH v_base ---
        if v_base != self.prev_v_base:
            self.v_left = v_base
            self.v_right = v_base
            self.prev_v_base = v_base
            
        e = 0.0
        if V_cmd != 0.0 and W_cmd == 0.0:
            if not self.is_going_straight:
                self.desired_yaw = self.current_yaw
                self.is_going_straight = True
            e = self.normalize_angle(self.desired_yaw - self.current_yaw)
        elif W_cmd != 0.0:
            self.is_going_straight = False
            e = W_cmd - self.current_w
        else:
            self.is_going_straight = False
            self.prev_error = 0.0
            
        # True Derivative rate (Error change per second)
        de = (e - self.prev_error) / dt
        self.prev_error = e
        
        # Publish raw diagnostic errors
        err_msg = Float32()
        derr_msg = Float32()
        err_msg.data = float(e)
        derr_msg.data = float(de)
        self.error_pub.publish(err_msg)
        self.delta_error_pub.publish(derr_msg)
        
        e_deg = math.degrees(e)
        de_deg = math.degrees(de)
        
        # Compute Mamdani continuous fuzzy output
        fuzzy_output = self.fuzzy_rule_base(e_deg, de_deg)
        
        # --- STEP 2: UPDATE SPEEDS INCREMENTALLY (FIXED LOGIC) ---
        # We trust the sign of the fuzzy_output directly. 
        # No abs(), no if/else conditions based on error direction.
        # This naturally handles counter-steering and braking (Derivative action).
        if e > 0:

        # محتاج تصحيح لليسار -> ثبت الشمال وزود اليمين

            v_right = v_right + abs(fuzzy_output)

            v_left = v_left - abs(fuzzy_output)/4

        elif e < 0:

        # محتاج تصحيح لليمين -> ثبت اليمين وزود الشمال

            v_left = v_left + abs(fuzzy_output)

            v_right = v_right - abs(fuzzy_output)/4



        else:

            v_left = v_left

            v_right = v_right
                # Optional Safety Clamp: Prevent speeds from accumulating endlessly
        max_v = 1.5 
        self.v_left = max(0.1, min(self.v_left, max_v))
        self.v_right = max(0.1, min(self.v_right, max_v))
        
        # --- STEP 3: CONVERT TO RPM & PUBLISH ---
        left_rpm = (self.v_left * 60.0) / (2.0 * math.pi * self.R)
        right_rpm = (self.v_right * 60.0) / (2.0 * math.pi * self.R)
        
        left_rpm = max(0.0, left_rpm)
        right_rpm = max(0.0, right_rpm)
        
        left_msg = Float32()
        right_msg = Float32()
        left_msg.data = float(left_rpm)
        right_msg.data = float(right_rpm)
        
        self.left_pub.publish(left_msg)
        self.right_pub.publish(right_msg)

    # ==========================
    # MEMBERSHIP FUNCTION EVALUATOR
    # ==========================
    def evaluate_mf(self, x, a, b, c, d):
        if a == b == c: 
            if x <= a: return 1.0
            if x >= d: return 0.0
            return (d - x) / (d - c)
        if b == c == d: 
            if x <= a: return 0.0
            if x >= d: return 1.0
            return (x - a) / (b - a)
        
        if x <= a or x >= d: return 0.0
        if b <= x <= c: return 1.0
        if a < x < b: return (x - a) / (b - a)
        if c < x < d: return (d - x) / (d - c)
        return 0.0

    # ==========================
    # TRUE MAMDANI FUZZY INFERENCE ENGINE
    # ==========================
    def fuzzy_rule_base(self, e, de):
        e_sets = {
            'NB': self.evaluate_mf(e, -40.0, -40.0, -40.0, -5.0),
            'NS': self.evaluate_mf(e, -20.0, -5.0, -5.0, 0.0),   
            'Z' : self.evaluate_mf(e, -5.0, 0.0, 0.0, 5.0),      
            'PS': self.evaluate_mf(e, 0.0, 5.0, 5.0, 20.0),      
            'PB': self.evaluate_mf(e, 5.0, 40.0, 40.0, 40.0)     
        }
        
        # Note: Since we added 'dt', 'de' is now in degrees/second.
        # If the robot oscillates, you might need to increase these threshold values slightly.
        de_sets = {
            'NB': self.evaluate_mf(de, -20.0, -20.0, -20.0, -5.0),
            'NS': self.evaluate_mf(de, -10.0, -5.0, -5.0, 0.0),
            'Z' : self.evaluate_mf(de, -5.0, 0.0, 0.0, 5.0),
            'PS': self.evaluate_mf(de, 0.0, 5.0, 5.0, 10.0),
            'PB': self.evaluate_mf(de, 5.0, 20.0, 20.0, 20.0) 
        }
        
        rules = {
            ('NB', 'NB'): 'NB', ('NB', 'NS'): 'NB', ('NB', 'Z'): 'NB', ('NB', 'PS'): 'NS', ('NB', 'PB'): 'Z',
            ('NS', 'NB'): 'NB', ('NS', 'NS'): 'NB', ('NS', 'Z'): 'NS', ('NS', 'PS'): 'Z',  ('NS', 'PB'): 'PS',
            ('Z',  'NB'): 'NB', ('Z',  'NS'): 'NS', ('Z',  'Z'): 'Z',  ('Z',  'PS'): 'PS', ('Z',  'PB'): 'PB',
            ('PS', 'NB'): 'NS', ('PS', 'NS'): 'Z',  ('PS', 'Z'): 'PS', ('PS', 'PS'): 'PB', ('PS', 'PB'): 'PB',
            ('PB', 'NB'): 'Z',  ('PB', 'NS'): 'PS', ('PB', 'Z'): 'PB', ('PB', 'PS'): 'PB', ('PB', 'PB'): 'PB'
        }
        
        outputs_activation = {'NB': 0.0, 'NS': 0.0, 'Z': 0.0, 'PS': 0.0, 'PB': 0.0}
        
        for (e_key, de_key), out_key in rules.items():
            activation = min(e_sets[e_key], de_sets[de_key])
            if activation > outputs_activation[out_key]:
                outputs_activation[out_key] = activation
                
        out_mfs = {
            'NB': (-0.7, -0.3, -0.3, -0.1),
            'NS': (-0.2, -0.1, -0.1, 0.0),
            'Z':  (-0.02, 0.0, 0.0, 0.02),
            'PS': (0.0, 0.1, 0.1, 0.2),
            'PB': (0.1, 0.3, 0.3, 0.7)
        }
        
        numerator = 0.0
        denominator = 0.0
        num_samples = 50 
        
        for i in range(num_samples + 1):
            out_val = -0.3 + (i * (0.6 / num_samples))
            aggregated_height = 0.0
            
            for out_key, act_level in outputs_activation.items():
                if act_level > 0:
                    a, b, c, d = out_mfs[out_key]
                    mf_value = self.evaluate_mf(out_val, a, b, c, d)
                    clipped_value = min(act_level, mf_value)
                    if clipped_value > aggregated_height:
                        aggregated_height = clipped_value
            
            numerator += out_val * aggregated_height
            denominator += aggregated_height
            
        return (numerator / denominator) if denominator > 0.0 else 0.0

def main(args=None):
    rclpy.init(args=args)
    node = FullFuzzyYawVelocityController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()