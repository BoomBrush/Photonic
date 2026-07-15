#include <SpeedyStepper.h>

const int YAW_MOTOR_STEP_PIN = A0;
const int YAW_MOTOR_DIRECTION_PIN = A1;
const int YAW_MOTOR_ENABLE = 38;

const int CURRENT_PIN = A3;

SpeedyStepper yaw;
long yaw_angle;

String content = "";
char character;

void setup() {
  Serial.begin(1000000);
  Serial.println("Started");
  Serial.setTimeout(1);
  
  yaw.connectToPins(YAW_MOTOR_STEP_PIN, YAW_MOTOR_DIRECTION_PIN);
  
  pinMode(YAW_MOTOR_ENABLE, OUTPUT);
  digitalWrite(YAW_MOTOR_ENABLE, HIGH);
  yaw.setSpeedInStepsPerSecond(5000*16);
  yaw.setAccelerationInStepsPerSecondPerSecond(100*16);
}

void loop() {
  if (Serial.available()) {
    character = Serial.read();

    switch (character)
    {
      case '!':
        digitalWrite(YAW_MOTOR_ENABLE, LOW);
      break;

      case '*':
        digitalWrite(YAW_MOTOR_ENABLE, HIGH);
      break;
      
      case ';':
        yaw_angle = content.toInt();
        content = "";
        yaw.moveToPositionInSteps(yaw_angle);
      break;

      case '?':
        Serial.println(analogRead(CURRENT_PIN));

      default:
        content.concat(character);
      break;
    }
  }
}
