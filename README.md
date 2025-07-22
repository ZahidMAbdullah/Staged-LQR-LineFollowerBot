# 🤖 Staged-LQR-LineFollowerBot

A two-wheeled, self-balancing, line-following robot built using the **Staged Linear Quadratic Regulator (LQR)** control technique. It dynamically maintains balance, follows a line, and avoids obstacles using smart sensors and real-time communication.

---

## 🔧 Hardware Overview

- **Microcontroller:** ESP32 DevKit C3  
- **Motors:** DC motors for wheel movement  
- **IMU Sensor:** 9-axis **BNO055** for pitch angle estimation  
- **Sensors:**
  - **IR Sensors** for line detection (white line on black track)
  - **Ultrasonic Sensor** for obstacle avoidance  

---

## 🧩 Mechanical Design

We designed a **custom 3D model** of the robot’s chassis to:
- Optimize **compactness** and **balance**
- Ensure proper placement of components
- Enhance **sensor accessibility**  
The result is a sleek, efficient robot frame built for high stability.

---

## 🧠 Control Algorithm: Staged LQR

We implemented a **Staged LQR** controller to keep the robot balanced like an inverted pendulum.

### Process:

1. **Pitch angle** is continuously read from the BNO055 IMU.
2. A **reference pitch value** is defined for perfect vertical balance.
3. The **pitch error** (θ) is calculated.
4. The error is fed into the **LQR controller**.

### Staged Gains Strategy:

- Different **LQR gains (K1, K2)** are applied depending on the pitch deviation:
  - **High deviation → Stronger correction**
  - **Small deviation → Smoother correction**

This staged approach leads to:
- **More stable balancing**
- **Adaptive response** in dynamic environments
- **Energy-efficient control**

---

## 💻 Software & Communication

We leveraged the **Wi-Fi capabilities** of the ESP32 for real-time control:

- **UDP communication** used for runtime tuning
- Built a **Python Tkinter GUI** to:
  - Dynamically send **Staged LQR values** to the robot
  - **Accelerate tuning** without needing code re-uploading

---

## 📷 Media (Optional)

> Add images or videos of your robot in action here if available:
```markdown
![Robot Front View](./media/robot_front.jpg)
![Tkinter Interface](./media/gui_tuning.png)
