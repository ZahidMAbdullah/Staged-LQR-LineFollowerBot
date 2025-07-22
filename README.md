🦾 Staged-LQR-LineFollowerBot
A two-wheeled, self-balancing line-following robot built using an ESP32 DevKit C3, designed to demonstrate control systems, sensor fusion, and staged LQR balancing.

🧠 Overview
This robot combines two main capabilities:

Self-Balancing using a Staged Linear Quadratic Regulator (LQR) controller

Line Following using IR sensors on a black track with a white path

We use IR sensors to follow the line, ultrasonic sensors to avoid obstacles, and DC motors to drive the wheels. A BNO055 9-axis IMU provides real-time orientation data, allowing us to calculate the robot’s pitch angle and apply LQR-based correction.

🛠️ Core Features
ESP32 DevKit C3: Main microcontroller with Wi-Fi support

BNO055 IMU: Used to obtain the pitch angle for balancing

Staged LQR Control:
Instead of a single set of gains, we dynamically select between two gain sets:

K1 for larger pitch errors (stronger corrective action)

K2 for small pitch deviations (smoother response)

UDP Communication:
We use the ESP32's Wi-Fi to send and receive staged LQR values via UDP, allowing live tuning.

Tkinter Tuning GUI:
A Python GUI using Tkinter helps us adjust and send controller parameters to the robot in real time.

🔧 Hardware Components
2× DC Motors (with driver)

BNO055 IMU

IR Sensor Array (for line detection)

Ultrasonic Sensor (for obstacle detection)

Caster Wheel (used only in line-following mode)

ESP32 DevKit C3

