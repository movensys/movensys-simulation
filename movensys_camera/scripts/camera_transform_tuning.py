#!/usr/bin/env python3
"""
Camera Transform Tuner - Interactive sliders for tuning camera_top transform
Publishes to /tf_static for real-time tuning
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import tkinter as tk
from tkinter import ttk
import threading
import math


class CameraTransformTuner(Node):
    def __init__(self):
        super().__init__('camera_transform_tuner')

        # Declare parameters with current values from camera_top_transform.launch.py
        self.declare_parameter('parent_frame', 'world_manipulator')
        self.declare_parameter('child_frame', 'camera_top')
        self.declare_parameter('x', -0.7)
        self.declare_parameter('y', -0.7)
        self.declare_parameter('z', 0.8318)
        self.declare_parameter('roll', -2.078)
        self.declare_parameter('pitch', -0.0121)
        self.declare_parameter('yaw', -0.7338)

        self.parent_frame = self.get_parameter('parent_frame').value
        self.child_frame = self.get_parameter('child_frame').value

        # Current transform values
        self.x = self.get_parameter('x').value
        self.y = self.get_parameter('y').value
        self.z = self.get_parameter('z').value
        self.roll = self.get_parameter('roll').value
        self.pitch = self.get_parameter('pitch').value
        self.yaw = self.get_parameter('yaw').value

        # Dynamic broadcaster → publishes to /tf, supports real-time updates.
        # StaticTransformBroadcaster (/tf_static) is for immutable transforms only
        # and RViz does not reliably re-render when the same frame pair is updated.
        self.tf_broadcaster = TransformBroadcaster(self)

        # Protect shared values written by GUI thread, read by timer (spin thread).
        self._lock = threading.Lock()

        # Timer runs inside the spin thread — the only thread safe to call publishers.
        # Publishes continuously at 20 Hz so RViz always has a fresh transform.
        self._timer = self.create_timer(0.05, self.publish_transform)

        self.get_logger().info(f'Camera Transform Tuner started')
        self.get_logger().info(f'Parent: {self.parent_frame}, Child: {self.child_frame}')

    def publish_transform(self):
        # Called by the 20 Hz timer — always runs in the spin thread, safe to publish.
        with self._lock:
            x, y, z = self.x, self.y, self.z
            roll, pitch, yaw = self.roll, self.pitch, self.yaw

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.parent_frame
        t.child_frame_id = self.child_frame

        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = z

        # Convert RPY to quaternion
        qx, qy, qz, qw = self.euler_to_quaternion(roll, pitch, yaw)
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw

        self.tf_broadcaster.sendTransform(t)

    def euler_to_quaternion(self, roll, pitch, yaw):
        """Convert Euler angles (roll, pitch, yaw) to quaternion (x, y, z, w)"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy

        return qx, qy, qz, qw

    def update_transform(self, x, y, z, roll, pitch, yaw):
        # Called from the GUI thread — only update values; the timer publishes them.
        with self._lock:
            self.x = x
            self.y = y
            self.z = z
            self.roll = roll
            self.pitch = pitch
            self.yaw = yaw


class TunerGUI:
    def __init__(self, node: CameraTransformTuner):
        self.node = node
        self.root = tk.Tk()
        self.root.title("Camera Transform Tuner")
        self.root.geometry("650x580")

        # Saved position storage
        self.saved_position = None

        # Step size variables
        self.step_pos = tk.StringVar(value="0.01")
        self.step_rot = tk.StringVar(value="0.01")

        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title = ttk.Label(main_frame, text="Camera Transform Tuner", font=('Helvetica', 14, 'bold'))
        title.grid(row=0, column=0, columnspan=5, pady=10)

        # Frame info
        frame_info = ttk.Label(main_frame, text=f"{node.parent_frame} → {node.child_frame}")
        frame_info.grid(row=1, column=0, columnspan=5, pady=5)

        # Step size configuration
        step_frame = ttk.Frame(main_frame)
        step_frame.grid(row=2, column=0, columnspan=5, pady=5)

        ttk.Label(step_frame, text="Step size - Position:").grid(row=0, column=0, padx=5)
        step_pos_entry = ttk.Entry(step_frame, textvariable=self.step_pos, width=8)
        step_pos_entry.grid(row=0, column=1, padx=5)

        ttk.Label(step_frame, text="Rotation:").grid(row=0, column=2, padx=5)
        step_rot_entry = ttk.Entry(step_frame, textvariable=self.step_rot, width=8)
        step_rot_entry.grid(row=0, column=3, padx=5)

        # Slider configurations: (name, min, max, resolution, initial, unit, is_rotation)
        self.sliders = {}
        slider_configs = [
            ('x', -3.0, 3.0, 0.01, node.x, 'm', False),
            ('y', -3.0, 3.0, 0.01, node.y, 'm', False),
            ('z', -1.0, 3.0, 0.01, node.z, 'm', False),
            ('roll', -3.14159, 3.14159, 0.01, node.roll, 'rad', True),
            ('pitch', -3.14159, 3.14159, 0.01, node.pitch, 'rad', True),
            ('yaw', -3.14159, 3.14159, 0.01, node.yaw, 'rad', True),
        ]

        for i, (name, min_val, max_val, resolution, initial, unit, is_rot) in enumerate(slider_configs):
            row = i + 3

            # Label
            label = ttk.Label(main_frame, text=f"{name} ({unit}):", width=10)
            label.grid(row=row, column=0, sticky=tk.W, pady=3)

            # Minus button
            minus_btn = ttk.Button(main_frame, text="-", width=3,
                                   command=lambda n=name, r=is_rot: self.on_step_minus(n, r))
            minus_btn.grid(row=row, column=1, sticky=tk.E, pady=3)

            # Slider
            var = tk.DoubleVar(value=initial)
            slider = ttk.Scale(main_frame, from_=min_val, to=max_val,
                             variable=var, orient=tk.HORIZONTAL, length=200,
                             command=lambda v, n=name: self.on_slider_change(n))
            slider.grid(row=row, column=2, sticky=(tk.W, tk.E), pady=3, padx=2)

            # Plus button
            plus_btn = ttk.Button(main_frame, text="+", width=3,
                                  command=lambda n=name, r=is_rot: self.on_step_plus(n, r))
            plus_btn.grid(row=row, column=3, sticky=tk.W, pady=3)

            # Entry for typing values
            entry_var = tk.StringVar(value=f"{initial:.4f}")
            entry = ttk.Entry(main_frame, textvariable=entry_var, width=10)
            entry.grid(row=row, column=4, sticky=tk.E, pady=3, padx=5)
            entry.bind('<Return>', lambda e, n=name: self.on_entry_change(n))
            entry.bind('<FocusOut>', lambda e, n=name: self.on_entry_change(n))

            self.sliders[name] = {
                'var': var,
                'entry_var': entry_var,
                'entry': entry,
                'slider': slider,
                'min': min_val,
                'max': max_val,
                'is_rotation': is_rot
            }

        # Buttons frame - row 1
        button_frame1 = ttk.Frame(main_frame)
        button_frame1.grid(row=9, column=0, columnspan=5, pady=5)

        # Reset button
        reset_btn = ttk.Button(button_frame1, text="Reset to Default", command=self.reset_values)
        reset_btn.grid(row=0, column=0, padx=5)

        # Print values button
        print_btn = ttk.Button(button_frame1, text="Print Values", command=self.print_values)
        print_btn.grid(row=0, column=1, padx=5)

        # Buttons frame - row 2 (save/load)
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.grid(row=10, column=0, columnspan=5, pady=5)

        # Save position button
        save_btn = ttk.Button(button_frame2, text="Save Position", command=self.save_position)
        save_btn.grid(row=0, column=0, padx=5)

        # Load saved position button
        self.load_btn = ttk.Button(button_frame2, text="Load Saved", command=self.load_saved_position, state=tk.DISABLED)
        self.load_btn.grid(row=0, column=1, padx=5)

        # Saved position indicator
        self.saved_label = ttk.Label(main_frame, text="No position saved", foreground="gray")
        self.saved_label.grid(row=11, column=0, columnspan=5, pady=5)

        # Output text
        self.output_text = tk.Text(main_frame, height=4, width=70)
        self.output_text.grid(row=12, column=0, columnspan=5, pady=10)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)

    def on_slider_change(self, name):
        # Update entry field
        value = self.sliders[name]['var'].get()
        self.sliders[name]['entry_var'].set(f"{value:.4f}")

        # Update transform
        self.node.update_transform(
            self.sliders['x']['var'].get(),
            self.sliders['y']['var'].get(),
            self.sliders['z']['var'].get(),
            self.sliders['roll']['var'].get(),
            self.sliders['pitch']['var'].get(),
            self.sliders['yaw']['var'].get()
        )

    def on_entry_change(self, name):
        try:
            value = float(self.sliders[name]['entry_var'].get())
            # Clamp to slider range
            min_val = self.sliders[name]['min']
            max_val = self.sliders[name]['max']
            value = max(min_val, min(max_val, value))
            # Update slider
            self.sliders[name]['var'].set(value)
            self.sliders[name]['entry_var'].set(f"{value:.4f}")
            # Update transform
            self.node.update_transform(
                self.sliders['x']['var'].get(),
                self.sliders['y']['var'].get(),
                self.sliders['z']['var'].get(),
                self.sliders['roll']['var'].get(),
                self.sliders['pitch']['var'].get(),
                self.sliders['yaw']['var'].get()
            )
        except ValueError:
            # Restore current slider value if invalid input
            value = self.sliders[name]['var'].get()
            self.sliders[name]['entry_var'].set(f"{value:.4f}")

    def get_step_size(self, is_rotation):
        try:
            if is_rotation:
                return float(self.step_rot.get())
            else:
                return float(self.step_pos.get())
        except ValueError:
            return 0.01

    def on_step_plus(self, name, is_rotation):
        step = self.get_step_size(is_rotation)
        current = self.sliders[name]['var'].get()
        new_val = current + step
        # Clamp to range
        new_val = max(self.sliders[name]['min'], min(self.sliders[name]['max'], new_val))
        self.sliders[name]['var'].set(new_val)
        self.sliders[name]['entry_var'].set(f"{new_val:.4f}")
        self.update_transform_from_sliders()

    def on_step_minus(self, name, is_rotation):
        step = self.get_step_size(is_rotation)
        current = self.sliders[name]['var'].get()
        new_val = current - step
        # Clamp to range
        new_val = max(self.sliders[name]['min'], min(self.sliders[name]['max'], new_val))
        self.sliders[name]['var'].set(new_val)
        self.sliders[name]['entry_var'].set(f"{new_val:.4f}")
        self.update_transform_from_sliders()

    def update_transform_from_sliders(self):
        self.node.update_transform(
            self.sliders['x']['var'].get(),
            self.sliders['y']['var'].get(),
            self.sliders['z']['var'].get(),
            self.sliders['roll']['var'].get(),
            self.sliders['pitch']['var'].get(),
            self.sliders['yaw']['var'].get()
        )

    def reset_values(self):
        defaults = {
            'x': -0.7, 'y': -0.7, 'z': 0.8,
            'roll': -0.785398, 'pitch': 1.91986, 'yaw': -1.57
        }
        for name, value in defaults.items():
            self.sliders[name]['var'].set(value)
            self.sliders[name]['entry_var'].set(f"{value:.4f}")

        self.node.update_transform(
            defaults['x'], defaults['y'], defaults['z'],
            defaults['roll'], defaults['pitch'], defaults['yaw']
        )

    def save_position(self):
        self.saved_position = {
            'x': self.sliders['x']['var'].get(),
            'y': self.sliders['y']['var'].get(),
            'z': self.sliders['z']['var'].get(),
            'roll': self.sliders['roll']['var'].get(),
            'pitch': self.sliders['pitch']['var'].get(),
            'yaw': self.sliders['yaw']['var'].get(),
        }
        self.load_btn.config(state=tk.NORMAL)
        self.saved_label.config(
            text=f"Saved: x={self.saved_position['x']:.2f}, y={self.saved_position['y']:.2f}, z={self.saved_position['z']:.2f}",
            foreground="green"
        )
        self.node.get_logger().info(f"Position saved: {self.saved_position}")

    def load_saved_position(self):
        if self.saved_position is None:
            return

        for name, value in self.saved_position.items():
            self.sliders[name]['var'].set(value)
            self.sliders[name]['entry_var'].set(f"{value:.4f}")

        self.node.update_transform(
            self.saved_position['x'],
            self.saved_position['y'],
            self.saved_position['z'],
            self.saved_position['roll'],
            self.saved_position['pitch'],
            self.saved_position['yaw']
        )
        self.node.get_logger().info("Loaded saved position")

    def print_values(self):
        x = self.sliders['x']['var'].get()
        y = self.sliders['y']['var'].get()
        z = self.sliders['z']['var'].get()
        roll = self.sliders['roll']['var'].get()
        pitch = self.sliders['pitch']['var'].get()
        yaw = self.sliders['yaw']['var'].get()

        output = f"""# Camera Transform Values
--x {x:.6f} --y {y:.6f} --z {z:.6f} \\
--roll {roll:.6f} --pitch {pitch:.6f} --yaw {yaw:.6f}"""

        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, output)

        self.node.get_logger().info(f'Transform: x={x:.4f}, y={y:.4f}, z={z:.4f}, '
                                    f'roll={roll:.4f}, pitch={pitch:.4f}, yaw={yaw:.4f}')

    def run(self):
        self.root.mainloop()


def main(args=None):
    rclpy.init(args=args)
    node = CameraTransformTuner()

    # Run ROS2 spinner in separate thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    # Run GUI in main thread
    gui = TunerGUI(node)
    gui.run()

    # Cleanup
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
