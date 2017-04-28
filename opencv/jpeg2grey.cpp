#include "stdio.h"
#include <opencv2/opencv.hpp>  

int main()
{  
	IplImage *src = cvLoadImage("test.jpg",1);  
	printf("src size %d nChannels %d depth %d imageSize %d\n", src->nSize, src->nChannels, src->depth, src->imageSize);
	//cvShowImage("test",src);  
	//cvWaitKey(0);  
	IplImage *dst = cvCloneImage(src);  
	cvZero(dst);  
	//cvShowImage("Zero",dst);  
	//cvWaitKey(0);  
	IplImage *dst_grey = cvCreateImage(cvGetSize(src),IPL_DEPTH_8U,1);  
	IplImage *dst_binary = cvCreateImage(cvGetSize(src),IPL_DEPTH_8U,1);  
	cvCvtColor(src,dst_grey,CV_BGR2GRAY);//转灰度  
	//cvShowImage("Grey_Image",dst_grey);   
	//cvWaitKey(0);
	//cvThreshold(dst_grey, dst_binary, 120, 255, CV_THRESH_OTSU);  //二值化   
	//cvShowImage("Binary_Image", dst_binary);  
	cvWaitKey(0);  

	cvReleaseImage (&src);   
	cvReleaseImage (&dst);   
	cvReleaseImage (&dst_grey);   
	cvReleaseImage (&dst_binary);    
	cvDestroyAllWindows();  
	return 0;  
}
