#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// ================== Motor Pins ==================
// Motor A pins (right)
#define A_IN1 6
#define A_IN2 7

// Motor B pins (left)
#define B_IN1 4
#define B_IN2 5

#define PITCH_REFERENCE 90       // Balanced pitch value of the robot (degrees)
const float FALL_LIMIT = 30.0;   // Angle beyond which robot is considered fallen (degrees)

uint16_t BNO055_SAMPLERATE_DELAY_MS = 1;

// ========== Staged LQR Gains ==========
// Stage 1: Small angles (0-5 degrees) - Smooth control
float K1_stage1 = 5.8;   // Angle gain
float K2_stage1 = 0.59;   // Angular velocity gain

// Stage 2: Medium angles (5-15 degrees) - Moderate control
float K1_stage2 = 9.6;
float K2_stage2 = 1.32;

// Stage 3: Large angles (15-30 degrees) - Aggressive control
float K1_stage3 = 13.8;
float K2_stage3 = 1.48;

// Transition smoothing factor (0-1, higher = smoother transitions)
const float transition_smoothing = 0.35;

// ========== Variables for LQR ==========
float previous_theta = 0;
unsigned long previous_time = 0;
float output = 0;

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28, &Wire);

void setup() {
  Serial.begin(115200);
  Wire.begin(8, 9);  // SDA=8, SCL=9 for ESP32

  Serial.println("Starting BNO055...");

  if (!bno.begin()) {
    Serial.println("BNO055 not detected. Check wiring!");
    while (1);
  }

  pinMode(A_IN1, OUTPUT);
  pinMode(A_IN2, OUTPUT);
  pinMode(B_IN1, OUTPUT);
  pinMode(B_IN2, OUTPUT);

  delay(1000);  // Give the sensor time to initialize
  previous_time = millis();
  previous_theta = 0;
}

void loop() {
  // ====== Get Sensor Data ======
  sensors_event_t orientationData;
  bno.getEvent(&orientationData, Adafruit_BNO055::VECTOR_EULER);

  float raw_pitch = orientationData.orientation.z;
  float filtered_pitch = -raw_pitch;  // Invert sign to align with reference
  float theta = filtered_pitch - PITCH_REFERENCE-9.2;  // error angle in degrees (current angle wrt balanced)

  // ====== Calculate angular velocity (theta_dot) ======
  unsigned long current_time = millis();
  float dt = (current_time - previous_time) / 1000.0;  // convert ms to seconds
  if (dt <= 0) dt = 0.001;  // avoid div by zero

  // Get gyro Y-axis reading directly from BNO055
  imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
  float gyroY = gyro.y();  // adjust axis if needed

  // Compute angular velocity from angle difference
  float theta_diff = (theta - previous_theta) / dt;

  // Combine both using weighted average or filter
  static float filtered_theta_dot = 0;
  float alpha = 0.6;  // adjust for smoothness
  float combined_theta_dot = 0.5 * theta_diff + 0.5 * gyroY;  // simple average
  filtered_theta_dot = alpha * filtered_theta_dot + (1 - alpha) * combined_theta_dot;

  float theta_dot = filtered_theta_dot;
  previous_theta = theta;
  previous_time = current_time;

  // ====== Staged LQR control ======
  float K1, K2;
  float abs_theta = abs(theta);
  
  // Determine which stage we're in and interpolate between them for smooth transitions
  if (abs_theta < 5.0 && abs(theta) > 0.5) {
    // Stage 1 - Small angles
    K1 = K1_stage1;
    K2 = K2_stage1;
  } 
  else if (abs_theta < 12.0) {
    // Stage 2 - Medium angles
    if (abs_theta < 7.0) {  // Transition zone between stage 1 and 2
      float blend = (abs_theta - 5.0) / 5.0 * transition_smoothing;
      K1 = K1_stage1 + (K1_stage2 - K1_stage1) * blend;
      K2 = K2_stage1 + (K2_stage2 - K2_stage1) * blend;
    } else {
      K1 = K1_stage2;
      K2 = K2_stage2;
    }
  } 
  else if (abs_theta <= FALL_LIMIT) {
    // Stage 3 - Large angles
    if (abs_theta < 20.0) {  // Transition zone between stage 2 and 3
      float blend = (abs_theta - 12.0) / 5.0 * transition_smoothing;
      K1 = K1_stage2 + (K1_stage3 - K1_stage2) * blend;
      K2 = K2_stage2 + (K2_stage3 - K2_stage2) * blend;
    } else {
      K1 = K1_stage3;
      K2 = K2_stage3;
    }
  } 
  else {
    // Beyond fall limit - stop motors
    stopMotors();
    return;
  }

  // Calculate control output
  float raw_output = -(K1 * theta + K2 * theta_dot);

  // Map output to avoid motor deadzone with different forward/backward mappings
  if (raw_output > 0) {
    output = map(raw_output, 0, 255, 90, 255); // Backward
  }
  else if (raw_output < 0) {
    output = map(raw_output, 0, -255, -90, -255); // Forward
  } 
  else {
    output = 0;
  }

  // ====== Debugging ======
  Serial.print("Theta: ");
  Serial.print(theta);
  Serial.print("\tTheta_dot: ");
  Serial.print(theta_dot);
  Serial.print("\tK1: ");
  Serial.print(K1);
  Serial.print("\tK2: ");
  Serial.print(K2);
  Serial.print("\tOutput: ");
  Serial.println(output);

  // ====== Apply control to motors ======
  if (abs(theta) <= FALL_LIMIT && abs(theta) > 1.5) {
    int speed = constrain(output, -255, 255);
    stopMotors();
    delay(2);  // Brief delay to prevent motor driver issues
    setMotorSpeeds(-speed, -speed);
  } 
  else {
    stopMotors();
  }

  delay(BNO055_SAMPLERATE_DELAY_MS);
}

// ========== Motor Control ==========
void motorA(int speed) {  // Right Motor
  speed = constrain(speed, -255, 255);
  if (speed > 0) {
    analogWrite(A_IN1, speed);
    analogWrite(A_IN2, 0);
  } else {
    analogWrite(A_IN1, 0);
    analogWrite(A_IN2, -speed);
  }
}

void motorB(int speed) {  // Left Motor
  speed = constrain(speed, -255, 255);
  if (speed > 0) {
    analogWrite(B_IN1, 0);
    analogWrite(B_IN2, speed - 13);  // Slight tuning for left side
  } else {
    analogWrite(B_IN1, -speed + 13);
    analogWrite(B_IN2, 0);
  }
}

void setMotorSpeeds(int left, int right) {
  motorA(right);  // Right motor
  motorB(left);   // Left motor
}

void stopMotors() {
  motorA(0);
  motorB(0);
}