#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2016 Jérémie DECOCK (http://www.jdhp.org)

# This script is provided under the terms and conditions of the MIT license:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Denoise FITS and PNG images with the "Null" algorithm (actually does nothing).

Example usages:
  ./datapipe/denoising/null.py -h
  ./datapipe/denoising/null.py ./test.fits
  ipython3 -- ./datapipe/denoising/null.py ./test.fits
"""

import argparse
import datetime
import json
import os
import numpy as np
import time

from datapipe.benchmark import assess
from datapipe.io import images


def null(img):

    return img


def main():

    # PARSE OPTIONS ###########################################################

    parser = argparse.ArgumentParser(description='Denoise FITS images with the "null" algorithm.')

    parser.add_argument("--benchmark", "-b", metavar="STRING", 
                        help="The benchmark method to use to assess the algorithm for the"
                             "given images")

    parser.add_argument("--hdu", "-H", type=int, default=0, metavar="INTEGER", 
                        help="The index of the HDU image to use for FITS input files")

    parser.add_argument("--output", "-o", default=None,
                        metavar="FILE",
                        help="The output file path (JSON)")

    parser.add_argument("fileargs", nargs="+", metavar="FILE",
                        help="The files image to process (FITS)."
                             "If fileargs is a directory,"
                             "all FITS files it contains are processed.")

    args = parser.parse_args()

    benchmark_method = args.benchmark
    hdu_index = args.hdu
    input_file_or_dir_path_list = args.fileargs

    if benchmark_method is not None:
        file_path_list = []
        score_list = []
        execution_time_list = []

    for input_file_or_dir_path in input_file_or_dir_path_list:

        if os.path.isdir(input_file_or_dir_path):
            input_file_path_list = []
            for dir_item in os.listdir(input_file_or_dir_path):
                dir_item_path = os.path.join(input_file_or_dir_path, dir_item)
                if dir_item_path.lower().endswith('.fits') and os.path.isfile(dir_item_path):
                    input_file_path_list.append(dir_item_path)
        else:
            input_file_path_list = [input_file_or_dir_path]

        for input_file_path in input_file_path_list:

            # READ THE INPUT FILE ##################################################

            input_img = images.load(input_file_path, hdu_index)

            if input_img.ndim != 2:
                raise Exception("Unexpected error: the input FITS file should contain a 2D array.")


            # NULL FILTER #########################################################

            base_file_path = os.path.basename(input_file_path)
            base_file_path = os.path.splitext(base_file_path)[0]

            initial_time = time.perf_counter()
            cleaned_img = null(input_img)
            execution_time = time.perf_counter() - initial_time

            # GET THE REFERENCE IMAGE #############################################

            reference_img = images.load(input_file_path, 1)

            # ASSESS OR PRINT THE CLEANED IMAGE ###################################

            try:
                if benchmark_method is None:
                    image_list = [input_img, reference_img, cleaned_img] 
                    title_list = ["Input image", "Reference image", "Cleaned image"] 
                    output = "{}_null.pdf".format(base_file_path)

                    images.plot_list(image_list, title_list)
                    images.mpl_save_list(image_list, output, title_list)
                else:
                    score_tuple = assess.assess_image_cleaning(input_img, cleaned_img, reference_img, benchmark_method)

                    file_path_list.append(input_file_path)
                    score_list.append(score_tuple)
                    execution_time_list.append(execution_time)
            except assess.EmptyReferenceImageError:
                print("Empty reference image error")
            except assess.EmptyOutputImageError:
                # TODO: if only the output is zero then this is ackward: this
                #       is an algorithm mistake but it cannot be assessed...
                print("Empty output image error")

    if benchmark_method is not None:
        print(score_list)

        output_dict = {}
        output_dict["algo"] = __file__
        output_dict["label"] = "Null"
        output_dict["algo_params"] = {}
        output_dict["benchmark_method"] = benchmark_method
        output_dict["date_time"] = str(datetime.datetime.now())
        output_dict["hdu_index"] = hdu_index
        output_dict["system"] = " ".join(os.uname())
        output_dict["input_file_path_list"] = file_path_list
        output_dict["score_list"] = score_list
        output_dict["execution_time_list"] = execution_time_list

        if args.output is None:
            output_file_path = "score_null_benchmark_{}.json".format(benchmark_method)
        else:
            output_file_path = args.output

        with open(output_file_path, "w") as fd:
            #json.dump(data, fd)                                 # no pretty print
            json.dump(output_dict, fd, sort_keys=True, indent=4)  # pretty print format


if __name__ == "__main__":
    main()

