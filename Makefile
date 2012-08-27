all:
	mkdir -p build/
	${CXX} `pkg-config --cflags --libs opencv` facedetect.cpp -o build/facedetect
