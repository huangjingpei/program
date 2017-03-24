
#include <stdio.h>
#include <stdlib.h>
#include "/home/jphuang/myprojects/GVC3200/avs_mcu/avs_mcu/avs/contrib/include/libavformat/avformat.h"
#include "/home/jphuang/myprojects/GVC3200/avs_mcu/avs_mcu/avs/contrib/include/libavcodec/avcodec.h"
#include "/home/jphuang/myprojects/GVC3200/avs_mcu/avs_mcu/avs/contrib/include/libavutil/frame.h"


int main(int argc, char **argv)
{
	if (argc != 2) {
		printf("This tool is used to add the length for per frame and write to the given file.");
		printf("Usage:%s H264 file.\n", argv[0]);
		return 0;
	}
	int align_size = 0;
	FILE *fpOut = fopen("out.data","ab");
	if (!fpOut)
	  return 0;
	av_register_all();
	AVFormatContext* pFormat = NULL;
	if (avformat_open_input(&pFormat, argv[1], NULL, NULL) < 0)
	{
		return 0;
	}
	AVCodecContext* video_dec_ctx = NULL;
	AVCodec* video_dec = NULL;
	if (avformat_find_stream_info(pFormat, NULL) < 0)
	{
		return 0;
	}
	av_dump_format(pFormat,0,argv[1],0);
	printf("nb_streams %d\n", pFormat->nb_streams);
	video_dec_ctx = pFormat->streams[0]->codec;
	video_dec = avcodec_find_decoder(video_dec_ctx->codec_id);
	if (avcodec_open2(video_dec_ctx, video_dec, NULL) < 0)
	{
		return 0;
	}
	printf("begin ...\n");
	AVPacket *pkt = av_packet_alloc();
	av_init_packet(pkt);
	while (1)
	{
		if (av_read_frame(pFormat, pkt) < 0)
		{
			fclose(fpOut);
			av_packet_free(&pkt);
			return 0;
		}
		align_size = (pkt->size + 3) & (~0x3);
		fwrite(&pkt->size, 1, 4, fpOut);
		fwrite(pkt->data, 1, align_size, fpOut);
		printf("pkt size %d flag %d\n", pkt->size, pkt->flags);
		if (pkt->stream_index == 0)
		{
			AVFrame *pFrame = av_frame_alloc();
			int got_picture = 0,ret = 0;
			ret = avcodec_decode_video2(video_dec_ctx, pFrame, &got_picture, pkt);
			if (ret < 0)
			{
	            av_packet_free(&pkt);
				return 0;
			}
//			if (got_picture)
//			{
//				char* buf = new char[video_dec_ctx->height * video_dec_ctx->width * 3 / 2];
//				memset(buf, 0, video_dec_ctx->height * video_dec_ctx->width * 3 / 2);
//				int height = video_dec_ctx->height;
//				int width = video_dec_ctx->width;
//				printf("decode video ok\n");
//				int a = 0, i;
//				for (i = 0; i<height; i++)
//				{
//					memcpy(buf + a, pFrame->data[0] + i * pFrame->linesize[0], width);
//					a += width;
//				}
//				for (i = 0; i<height / 2; i++)
//				{
//					memcpy(buf + a, pFrame->data[1] + i * pFrame->linesize[1], width / 2);
//					a += width / 2;
//				}
//				for (i = 0; i<height / 2; i++)
//				{
//					memcpy(buf + a, pFrame->data[2] + i * pFrame->linesize[2], width / 2);
//					a += width / 2;
//				}
//				fwrite(buf, 1, video_dec_ctx->height * video_dec_ctx->width * 3 / 2, fpOut);
//				delete buf;
//				buf = NULL;
//			}
			av_frame_free(&pFrame);


		}
	}

	return 0;
}


