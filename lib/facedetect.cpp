#include "opencv2/objdetect.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/imgproc.hpp"

#include <iostream>

typedef struct {
    cv::Mat frame;
    cv::CascadeClassifier face_cascade;
    cv::CascadeClassifier eyes_cascade;
} ImageInput;

static cv::Point detect_weightiest_face(ImageInput& input)
{
    cv::Mat frame_gray = input.frame;
    equalizeHist(frame_gray, frame_gray);

    //-- Detect faces
    std::vector<cv::Rect> faces;
    input.face_cascade.detectMultiScale(frame_gray, faces);

    size_t max_score = 0;
    int max_index = -1;
    for (int i = 0; i < faces.size(); i++) {
        const auto face = faces[i];
        size_t face_score = face.width * face.height;
        cv::Mat faceROI = frame_gray(faces[i]);

        //-- In each face, detect eyes
        std::vector<cv::Rect> eyes;
        input.eyes_cascade.detectMultiScale(faceROI, eyes);
        face_score *= (1 + eyes.size());

        if (face_score > max_score) {
            max_score = face_score;
            max_index = i;
        }
    }
    if (max_index == -1) {
        return {input.frame.size().width / 2, input.frame.size().height / 2};
    }
    const auto max_face = faces[max_index];
    return {max_face.x + max_face.width/2, max_face.y + max_face.height/2};
}

int main( int argc, const char** argv )
{
    cv::CommandLineParser parser(
        argc, argv,
        "{help h||}"
        "{image|<none>|Image file.}"
        "{face_cascade|haarcascade_frontalface_alt.xml|Path to face cascade.}"
        "{eyes_cascade|haarcascade_eye_tree_eyeglasses.xml|Path to eyes cascade.}"
        );

    parser.about( "\nThis program demonstrates using the cv::CascadeClassifier class to detect objects (Face + eyes) in a video stream.\n"
                  "You can use Haar or LBP features.\n\n" );

    const auto face_cascade_name = parser.get<cv::String>("face_cascade");
    const auto eyes_cascade_name = parser.get<cv::String>("eyes_cascade");
    const auto image_name = parser.get<cv::String>("image");

    cv::CascadeClassifier face_cascade;
    if (!face_cascade.load(face_cascade_name))
    {
        std::cerr << "Error loading face cascade from " << face_cascade_name << "\n";
        return EXIT_FAILURE;
    };
    cv::CascadeClassifier eyes_cascade;
    if( !eyes_cascade.load( eyes_cascade_name ) )
    {
        std::cerr << "Error loading eyes cascade from " << eyes_cascade_name << "\n";
        return EXIT_FAILURE;
    };

    auto image = cv::imread(image_name, cv::IMREAD_GRAYSCALE);
    if (image.data == NULL) {
        std::cerr << "Failed to read image from " << image_name << "\n";
        return EXIT_FAILURE;
    }

    ImageInput input{image, face_cascade, eyes_cascade};
    const auto face_center = detect_weightiest_face(input);
    std::cout
        << image.size().width << " "
        << image.size().height << " "
        << face_center.x << " "
        << face_center.y << "\n";
    return EXIT_SUCCESS;
}

