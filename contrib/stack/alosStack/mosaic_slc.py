#!/usr/bin/env python3

# Modified by Michlle Yip based on mosaic_interferogram.py
# Modified on 09/05/2023
# Author of mosaic_interferogram.py : Cunren Liang 
# Copyright 2015-present, NASA-JPL/Caltech
# This script has to be run in the directory dates_resampled/YYMMDD/f1_0000/

import os
import glob
import shutil
import datetime
import numpy as np
import xml.etree.ElementTree as ET

import isce, isceobj
from isceobj.Alos2Proc.Alos2ProcPublic import create_xml
from isceobj.Alos2Proc.runSwathOffset import swathOffset
from isceobj.Alos2Proc.runFrameOffset import frameOffset
from isceobj.Alos2Proc.runSwathMosaic import swathMosaic
from isceobj.Alos2Proc.runFrameMosaic import frameMosaic

from StackPulic import acquisitionModesAlos2
from StackPulic import loadTrack

def cmdLineParse():
    '''
    command line parser.
    '''
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='form interferogram')
    parser.add_argument('-ref_date_stack', dest='ref_date_stack', type=str, required=True,
            help = 'reference date of stack. format: YYMMDD')
    parser.add_argument('-ref_date', dest='ref_date', type=str, required=True,
            help = 'reference date of this pair. format: YYMMDD')
    parser.add_argument('-sec_date', dest='sec_date', type=str, required=True,
            help = 'reference date of this pair. format: YYMMDD')
    parser.add_argument('-nrlks1', dest='nrlks1', type=int, default=1,
            help = 'number of range looks 1. default: 1')
    parser.add_argument('-nalks1', dest='nalks1', type=int, default=1,
            help = 'number of azimuth looks 1. default: 1')

    if len(sys.argv) <= 1:
        print('')
        parser.print_help()
        sys.exit(1)
    else:
        return parser.parse_args()


if __name__ == '__main__':

    inps = cmdLineParse()


    #get user parameters from input
    dateReferenceStack = inps.ref_date_stack # 180829(.track.xml)
    dateReference = inps.ref_date # 180829
    dateSecondary = inps.sec_date 
    numberRangeLooks1 = inps.nrlks1
    numberAzimuthLooks1 = inps.nalks1
    #######################################################

    logFile = 'process_merge_slc.log'
    interferogram = dateSecondary + '.slc'
    
    spotlightModes, stripmapModes, scansarNominalModes, scansarWideModes, scansarModes = acquisitionModesAlos2()
    
    frames = sorted([x[-4:] for x in glob.glob(os.path.join('../', 'f*_*'))])
    swaths = sorted([int(x[-1]) for x in glob.glob(os.path.join('../', 'f1_*', 's*'))])

    nframe = len(frames)
    nswath = len(swaths)
    
    
    trackReferenceStack = loadTrack(os.path.join('../../',dateReference), dateReferenceStack)

    fullpath = os.getcwd()
    ##mosaic swaths
    for i, frameNumber in enumerate(frames):
    
        mosaicDir = 'mosaic'
        os.makedirs(mosaicDir, exist_ok=True)
        os.chdir(mosaicDir)

       
         #compute swath offset using reference stack
         #geometrical offset is enough now
    offsetReferenceStack = swathOffset(trackReferenceStack.frames[i],dateReferenceStack+'.slc', 'swath_offset_' + dateReferenceStack + '.txt', crossCorrelation=False, numberOfAzimuthLooks=10)
         #we can faithfully make it integer.
         #this can also reduce the error due to floating point computation
    rangeOffsets = [float(round(x)) for x in offsetReferenceStack[0]]
    azimuthOffsets = [float(round(x)) for x in offsetReferenceStack[1]]

         #list of input files
    inputInterferograms = []

    for j, swathNumber in enumerate(range(swaths[0], swaths[-1] + 1)):
              swathDir = 's{}'.format(swathNumber)
              inputInterferograms.append(os.path.join(fullpath, swathDir, interferogram))
    #print(fullpath)
    #print(inputInterferograms)
    
   
    #note that frame parameters do not need to be updated after mosaicking

    #mosaic SLCs
    swathMosaic(trackReferenceStack.frames[i], inputInterferograms, interferogram, 
                rangeOffsets, azimuthOffsets, numberRangeLooks1, numberAzimuthLooks1, resamplingMethod=1)

    create_xml(interferogram, trackReferenceStack.frames[i].numberOfSamples, trackReferenceStack.frames[i].numberOfLines, 'int')
