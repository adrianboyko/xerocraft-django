#include <rdm630.h>
#include <Keyboard.h>

rdm630 rfid(9, 0);  // TX pin of RDM6300 is connected to Arduino pin 9

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    rfid.begin();
    Keyboard.begin();
}

void blinkLED() {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW); 
}

unsigned long calcCardNum(byte *data) {
    return
        ((unsigned long)data[1]<<24) + 
        ((unsigned long)data[2]<<16) + 
        ((unsigned long)data[3]<<8) + 
        ((unsigned long)data[4]<<0);
}

void loop() {
    byte data[6];
    byte length;

    if(rfid.available()) {
        blinkLED();
        rfid.getData(data, length);
        unsigned long result = calcCardNum(data);
        Keyboard.write('[');
        Keyboard.print(result);
        Keyboard.write(']');
    }
}

