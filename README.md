###🧠 Project Description: Staged-LQR-LineFollowerBot
We developed a two-wheeled self-balancing line-following robot that uses a Staged LQR (Linear Quadratic Regulator) control strategy to maintain balance while following a line and avoiding obstacles.

##🔧 Hardware Overview
Microcontroller: ESP32 DevKit C3

Motors: DC motors for wheel movement

IMU: 9-axis BNO055 sensor for pitch angle estimation

Sensors:

IR sensors for line detection (white line on black track)

Ultrasonic sensor for obstacle avoidance

##🧩 Mechanical Design
We designed a custom 3D model of the robot’s chassis, carefully placing all components to achieve a compact and stable body structure optimized for balance and sensor accessibility.

##🧠 Control Algorithm: Staged LQR
We employed a Staged LQR approach to stabilize the robot like an inverted pendulum:

The system continuously reads the pitch angle from the BNO055.

A reference pitch is defined (i.e., the balanced vertical position).

Error in pitch (θ) is calculated and fed into the LQR controller.

Staged control: Different LQR gains (K1, K2) are applied depending on how far the robot is tilted — providing:

Stronger corrective forces for large deviations.

Smoother, less aggressive responses for minor disturbances.
This results in adaptive and energy-efficient balancing, especially useful in dynamic environments.

##💻 Software & Communication
We utilized the ESP32’s Wi-Fi capabilities to implement UDP communication for real-time tuning.

A custom Python interface (Tkinter GUI) was built to:

Dynamically send staged LQR gain values to the robot.

Accelerate the tuning and testing process without needing code re-uploading.
