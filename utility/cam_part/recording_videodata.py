# run this with python option not python3
# this capture video for given period of time

import os
import argparse
import datetime
import time
import subprocess
import socket


class Rec(object):
    def __init__ (self):
        self.recordtime = None
        self.outputfilename = None
        #self.commandline = "ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 -preset faster -pix_fmt yuv420p"
        self.cmd = ['ffmpeg', '-f', 'v4l2', '-input_format', 'mjpeg', '-i', '/dev/video0', '-preset', 'faster', '-pix_fmt', 'yuv422p']
        self.resolution = None
        self.inputfps = 0

    def createcommandline(self):
        print('adding arguments...')
        fr = "-framerate" # frame rate
        ct = "-t" # capture time
        res = "-video_size" #resolution 
        bitrate = "-b:v" # bitrate
        ct_conv = str(datetime.timedelta(seconds=self.recordtime)) # converted time
        if(self.resolution == 1080):
            res_conv = "1920x1080"
            subprocess.call(['v4l2-ctl', '--set-fmt-video=width=1920,height=1080,pixelformat=YUV422p'])
        elif(self.resolution == 720):
            res_conv = "1280x720"
            subprocess.call(['v4l2-ctl', '--set-fmt-video=width=1280,height=720,pixelformat=YUV422p'])
        elif(self.resolution == 480):
            res_conv = "858x480"
            subprocess.call(['v4l2-ctl', '--set-fmt-video=width=858,height=480,pixelformat=YUV422p'])
        elif(self.resolution == 360):
            res_conv = "480x360"
            subprocess.call(['v4l2-ctl', '--set-fmt-video=width=480,height=360,pixelformat=YUV422p'])
        else:
            print ("invalid option")
        
        self.startrecord(fr, ct, res, ct_conv, res_conv, bitrate)

    def startrecord(self, fr, ct, res, ct_conv, res_conv, bitrate):
        print('running ffmpeg script...')
        self.cmd.append(bitrate)
        self.cmd.append(self.br_val)
        self.cmd.append(fr)
        self.cmd.append(str(self.inputfps))
        self.cmd.append(ct)
        self.cmd.append(ct_conv)
        self.cmd.append(res)
        self.cmd.append(res_conv)

        self.outputfilename = self.createoutfilename()
        self.cmd.append(self.outputfilename)
        print (self.cmd)
        subprocess.call(self.cmd)
        #print(self.commandline +" "+ fr +" "+ str(self.inputfps) +" "+ ct +" "+ ct_conv +" "+ res +" "+ res_conv +" "+ self.outputfilename)
        #os.system(self.commandline +" "+ fr +" "+ str(self.inputfps) +" "+ ct +" "+ ct_conv +" "+ res +" "+ res_conv +" "+ self.outputfilename)
            
    def createoutfilename(self):
        devicename = socket.gethostname()
        now = datetime.datetime.now()
        strnow = now.strftime("%H:%M")
        finalname = str(devicename) + "_" + strnow.replace(":", "") + "_" + str(self.resolution) + "_" + str(self.recordtime) +".mp4"
        print(finalname)
        return finalname



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="recording test videos.")
    parser.add_argument('-t', '--recordtime', type=int, default = 60, help = 'length of the recording video in seconds')
    parser.add_argument('-o', '--output', type=str, default = 'cam_vid.mkv', help = 'name of the output file')
    parser.add_argument('-fps', '--inputfps', type=int, default = 30, help = ' frame rate of the input video')
    parser.add_argument('-r', '--resolution', type=int, default = 720, help = ' video resolution. type in vertical metric 720 or 480 (e.g. 1080p --> 1920x1080, 720p --> 1280x720, 480p --> 858x480, 360p --> 480x360)')
    parser.add_argument('-b', '--bitrate_value', type=str, default = "1M", help = ' desired bitrate. ')
    
    ARGS = parser.parse_args()
    rec = Rec()
    rec.recordtime = ARGS.recordtime
    rec.outputfilename = ARGS.output
    rec.inputfps = ARGS.inputfps
    rec.resolution = ARGS.resolution
    rec.br_val = ARGS.bitrate_value
    rec.createcommandline()




