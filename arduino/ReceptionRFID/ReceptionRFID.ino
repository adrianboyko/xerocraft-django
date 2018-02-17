#include <rdm630.h>
#include <Keyboard.h>

rdm630 rfid(9, 0);  // TX pin of RDM6300 is connected to Arduino pin 9

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    rfid.begin();
    Keyboard.begin();
}

void typeDigits(byte *data, byte length) {
    char message[20]={0};
    sprintf(message, ">%02X%02X%02X%02X", data[1], data[2], data[3], data[4]);

    // Write SLOWLY so as not to overrun the slow tablet.
    char* c = message;
    for (int i=0; i<9; i++) {
        delay(150);
        Keyboard.write(*c);
        c += 1;
    }
}

void loop() {
    byte data[6];
    byte length;

    if(rfid.available()) {
        digitalWrite(LED_BUILTIN, HIGH);

        // Read the first blob of data.
        rfid.getData(data, length);

        // Send it.
        typeDigits(data, length);

        // Ignore the rest in this cluster.
        for (int i=0; i<20000; i++) {
            if (rfid.available()) {
                rfid.getData(data, length);
            }
        }

        digitalWrite(LED_BUILTIN, LOW);
    }
}




