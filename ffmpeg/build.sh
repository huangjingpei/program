
#!/bin/bash

gcc -o scanh264 scanh264.c  -I/home/jphuang/myprojects/GVC3200/avs_mcu/avs_mcu/avs/contrib/include/ -D__STDC_CONSTANT_MACROS  -L/home/jphuang/myprojects/GVC3200/avs_mcu/avs_mcu/avs/contrib/lib -lavformat -lavcodec  -lswresample -lavutil -lm -lz -lx264 -lpthread -ldl  -lrt

