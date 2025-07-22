// ================== Motor Pins ==================
#define A_IN1 6  // Right motor control pin 1
#define A_IN2 7  // Right motor control pin 2
#define B_IN1 4  // Left motor control pin 1
#define B_IN2 5  // Left motor control pin 2

#define BASE_SPEED 12  // Lower base speed for better control

// ========== IR Sensor Pins ==========
const int irSensorPins[] = {10, 11, 12, 13, 14}; // L2, L1, C, R1, R2
const int numSensors = sizeof(irSensorPins) / sizeof(irSensorPins[0]);

// ========== Ultrasonic Pins ==========
const int trigPin = 16;
const int echoPin = 15;
const float soundSpeed = 0.0343; // cm/us

// ========== Constants ==========
const int obstacleThreshold = 18; // cm
const int IR_BLACK = LOW;
const int IR_WHITE = HIGH;

int ir[5]; // Sensor readings (0 is L2, 4 is R2)
int irt[5];
bool key = true;
unsigned long lastCrossTime = 0;

// ========== Setup ==========
void setup() {
  Serial.begin(9600);

  for (int i = 0; i < numSensors; i++) {
    pinMode(irSensorPins[i], INPUT);
  }

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(A_IN1, OUTPUT);
  pinMode(A_IN2, OUTPUT);
  pinMode(B_IN1, OUTPUT);
  pinMode(B_IN2, OUTPUT);
  delay(1000);
}

// ========== Main Loop ==========
void loop() {
  float distance = measureDistance();
  
  // Obstacle avoidance
  if (distance < obstacleThreshold && distance > 0) {
    avoidObstacle();
    return;
  }

  readIRSensors();
  
  // Double line stop condition
  if (allSensorsWhite()) {
    handleDoubleLine();
    return;
  } else key = true;

  followLine();
}

// ========== Sensor Functions ==========
void readIRSensors() {
  Serial.print("IR: ");
  for (int i = 0; i < numSensors; i++) {
    irt[i] = ir[i];
    ir[i] = digitalRead(irSensorPins[i]);
    Serial.print(ir[i]);
    Serial.print(" ");
  }
  Serial.println();
}

bool allSensorsWhite() {
  for (int i = 0; i < numSensors; i++) {
    if (ir[i] != IR_WHITE) return false;
  }
  return true;
}

// ========== Line Following Logic ==========
void followLine() {
  // Center line following with anticipation from outer sensors
  if (ir[2] == IR_WHITE) {
    if (ir[1] == IR_WHITE) {
      // Line drifting left - gentle correction
      setMotorSpeeds(BASE_SPEED - 15, BASE_SPEED + 5);
    } 
    else if (ir[3] == IR_WHITE) {
      // Line drifting right - gentle correction
      setMotorSpeeds(BASE_SPEED + 5, BASE_SPEED - 15);
    } 
    else {
      // Perfectly centered
      setMotorSpeeds(BASE_SPEED, BASE_SPEED);
    }
  } 
  // Right turns with progressive steering
  else if (ir[3] == IR_WHITE || ir[4] == IR_WHITE) {
    handleRightTurn();
  } 
  // Left turns with progressive steering
  else if (ir[1] == IR_WHITE || ir[0] == IR_WHITE) {
    handleLeftTurn();
  } 
  // Lost line - recovery
  else {
    recoverLine();
  }
  delay(5); // Small delay to prevent motor overload
}

void handleRightTurn() {
  // Progressive right turn based on sensor activation
  if (ir[4] == IR_WHITE) {
    // Sharp right turn detected by outer sensor
    // Slow down left wheel while maintaining right wheel speed
    setMotorSpeeds(-BASE_SPEED+10,-BASE_SPEED+10);
    delay(140);
    setMotorSpeeds(0,0);
    delay(20);
    setMotorSpeeds(BASE_SPEED + 30, -BASE_SPEED + 17);
    delay(100);
  } 
  else if (ir[3] == IR_WHITE) {
    // Moderate right turn
    setMotorSpeeds(-BASE_SPEED+15,-BASE_SPEED+15);
    delay(60);
    setMotorSpeeds(0,0);
    delay(10);
    setMotorSpeeds(BASE_SPEED + 25, -BASE_SPEED+40);
    delay(15);
  }
  
  // After initial turn, check if we've realigned
  readIRSensors();
  if (ir[2] == IR_WHITE) {
    // Recenter after turn
    setMotorSpeeds(BASE_SPEED, BASE_SPEED);
  }
}

void handleLeftTurn() {
  // Progressive left turn based on sensor activation
  if (ir[0] == IR_WHITE) {
    // Sharp left turn detected by outer sensor
    // Slow down right wheel while maintaining left wheel speed
    setMotorSpeeds(-BASE_SPEED+10,-BASE_SPEED+10);
    delay(140);
    setMotorSpeeds(0,0);
    delay(20);
    setMotorSpeeds(-BASE_SPEED + 17, BASE_SPEED + 30);
    delay(100);
  } 
  else if (ir[1] == IR_WHITE) {
    // Moderate left turn
    setMotorSpeeds(-BASE_SPEED+15,-BASE_SPEED+15);
    delay(60);
    setMotorSpeeds(0,0);
    delay(10);
    setMotorSpeeds(-BASE_SPEED+40, BASE_SPEED + 25);
    delay(15);
  }
  
  // After initial turn, check if we've realigned
  readIRSensors();
  if (ir[2] == IR_WHITE) {
    // Recenter after turn
    setMotorSpeeds(BASE_SPEED, BASE_SPEED);
  }
}

void recoverLine() {
  int dir = 0;

  if (irt[0] == IR_WHITE) dir = 1;
  if (irt[4] == IR_WHITE) dir = 2;
  
  if (dir == 1) {
    // Rotate slowly to find the line
    setMotorSpeeds(-BASE_SPEED,-BASE_SPEED);
    delay(200);
    setMotorSpeeds(-BASE_SPEED+15, BASE_SPEED+20); // Rotate right
    delay(200);
  } else if (dir == 2) {
    // Rotate slowly to find the line
    setMotorSpeeds(-BASE_SPEED,-BASE_SPEED);
    delay(200);
    setMotorSpeeds(BASE_SPEED+20, -BASE_SPEED+15); // Rotate right
    delay(200);
    }
  else {
    // Continue forward slowly while searching
    setMotorSpeeds(BASE_SPEED-4, BASE_SPEED-10);
  }
}

bool lastTurnWasRight() {
  // Simple heuristic - check which outer sensor last saw the line
  return (ir[3] == IR_WHITE || ir[4] == IR_WHITE);
}

// ========== Obstacle Avoidance ==========
void avoidObstacle() {
  Serial.println("Obstacle detected!");
  stopMotors();
  delay(1000);
  
  // Back up slightly
  setMotorSpeeds(-BASE_SPEED, -BASE_SPEED);
  delay(200);
  setMotorSpeeds(0,0);
  delay(300);
  
  // Turn left
  setMotorSpeeds(-BASE_SPEED, BASE_SPEED);
  delay(400);
  setMotorSpeeds(0,0);
  delay(30);
  
  // Find line again
  while (ir[2] != IR_BLACK) {
    readIRSensors();
    setMotorSpeeds(BASE_SPEED+75, BASE_SPEED-10);
  }
  while (ir[2] == IR_BLACK) {
    readIRSensors();
    setMotorSpeeds(BASE_SPEED+75, BASE_SPEED-10);
  }
  // Turn left
  setMotorSpeeds(0,0);
  delay(600);
  setMotorSpeeds(-BASE_SPEED+10,-BASE_SPEED+10);
  delay(400);
  setMotorSpeeds(0,0);
  delay(700);
  setMotorSpeeds(-BASE_SPEED, BASE_SPEED);
  delay(400);
}

// ========== Double Line Handling ==========
void handleDoubleLine() {
  if (key) {
    key = false;
    unsigned long currentTime = millis();
    
    if (currentTime - lastCrossTime < 1200) {
      // Double line detected within short time
      stopMotors();
      delay(3000);
    }
    lastCrossTime = currentTime;
  } 
}

// ========== Ultrasonic Distance ==========
float measureDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) return -1;
  return (duration * soundSpeed) / 2;
}

// ========== Motor Control ==========
void motorA(int speed) { // Right Motor
  speed = constrain(speed, -255, 255);
  if (speed > 0) {
    analogWrite(A_IN1, speed);
    analogWrite(A_IN2, 0);
  } else {
    analogWrite(A_IN1, 0);
    analogWrite(A_IN2, -speed);
  }
}

void motorB(int speed) { // Left Motor
  speed = constrain(speed, -255, 255);
  if (speed > 0) {
    analogWrite(B_IN1, 0);
    analogWrite(B_IN2, speed);
  } else {
    analogWrite(B_IN1, -speed);
    analogWrite(B_IN2, 0);
  }
}

void setMotorSpeeds(int left, int right) {
  motorA(right);
  motorB(left);
}

void stopMotors() {
  motorA(0);
  motorB(0);
}