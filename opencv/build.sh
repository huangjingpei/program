export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
gcc -o jpeg2grey jpeg2grey.cpp -lopencv_core -lopencv_imgproc -lopencv_highgui

