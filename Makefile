all:
	mkdir -p build/
	${CXX} `pkg-config --cflags --libs opencv` lib/facedetect.cpp -o build/facedetect
