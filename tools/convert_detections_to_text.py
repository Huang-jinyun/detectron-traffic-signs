#!/usr/bin/env python2

# Copyright (c) 2017-present, Facebook, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################
#
# Based on:
# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""Reval = re-eval. Re-evaluate saved detections."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import cPickle as pickle
import os
import sys
import numpy as np
import scipy.io as scio

from core.config import assert_and_infer_cfg
from core.config import cfg
from core.config import merge_cfg_from_file
from core.config import merge_cfg_from_list
from core.config import get_output_dir
from datasets.json_dataset import JsonDataset


def parse_args():
    parser = argparse.ArgumentParser(description='Convert results to text format that can be read by matlab scripts')

    parser.add_argument(
        '--dataset',
        dest='dataset_name',
        help='dataset to re-evaluate',
        default='voc_2007_test',
        type=str
    )
    parser.add_argument(
        '--detection_folder',
        dest='detection_folder',
        help='folder with detection files',
        type=str
    )
    parser.add_argument(
        '--output_dir',
        dest='output_path',
        help='results directory',
        default=None,
        type=str
    )
    parser.add_argument(
        'opts',
        help='See lib/core/config.py for all options',
        default=None,
        nargs=argparse.REMAINDER
    )
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    return args

def get_class_string(class_index, score, dataset):
    class_text = dataset.classes[class_index] if dataset is not None else \
        'id{:d}'.format(class_index)
    return class_text


def convert_from_cls_format(cls_boxes, cls_segms, cls_keyps):
    """Convert from the class boxes/segms/keyps format generated by the testing
    code.
    """
    box_list = [b for b in cls_boxes if len(b) > 0]
    if len(box_list) > 0:
        boxes = np.concatenate(box_list)
    else:
        boxes = None
    if cls_segms is not None:
        segms = [s for slist in cls_segms for s in slist]
    else:
        segms = None
    if cls_keyps is not None:
        keyps = [k for klist in cls_keyps for k in klist]
    else:
        keyps = None
    classes = []
    for j in range(len(cls_boxes)):
        classes += [j] * len(cls_boxes[j])
    return boxes, segms, keyps, classes


def export_txt(dataset, detections_folder, output_path, limit = -1):

    if output_path is None:
        output_path = detections_folder

    ds = JsonDataset(dataset)
    #detections_folder = get_output_dir(training=False)

    # convert region proposals from pkl to mat format if exist
    region_proposals_pkl = os.path.join(detections_folder, 'rpn_proposals.pkl')

    if os.path.exists(region_proposals_pkl):
        with open(region_proposals_pkl, 'r') as f:
            region_proposals = pickle.load(f)

            scio.savemat(os.path.join(output_path,'rpn_proposals.mat'), region_proposals)


    detections_pkl = os.path.join(detections_folder, 'detections.pkl')

    roidb = ds.get_roidb()

    with open(detections_pkl, 'r') as f:
        dets = pickle.load(f)

    all_boxes = dets['all_boxes']

    def id_or_index(ix, val):
        if len(val) == 0:
            return val
        else:
            return val[ix]


    output_file = os.path.join(output_path,'detections.txt')

    with open(output_file, 'w') as fn:
        for ix, entry in enumerate(roidb):
            if limit > 0 and ix >= limit:
                break

            if (ix + 1) % 250 == 0:
                print('{:d}/{:d}'.format(ix + 1, len(roidb)))

            cls_boxes_i = [
                id_or_index(ix, all_boxes[j]) for j in range(len(all_boxes))
            ]

            if isinstance(cls_boxes_i, list):
                boxes, segms, keypoints, classes = convert_from_cls_format(
                    cls_boxes_i, None, None)

            fn.write(str(entry['id']))
            fn.write('\n')

            if boxes is not None:
                for i, box in enumerate(boxes):
                    bbox = box[:4]
                    score = box[-1]

                    fn.write(get_class_string(classes[i], score, ds)+' '+str(score)+' ')
                    fn.write(str(bbox[0])+' '+str(bbox[1])+' '+str(bbox[2])+' '+str(bbox[3]))
                    fn.write('\n')


if __name__ == '__main__':

    opts = parse_args()

    #dataset = 'dfg_e5_coordBased_test'
    #pkl_path = '/opt/workspace/volume_data/DFG-database/domen-results-detectron/test/dfg_e5_coordBased_test/generalized_rcnn/detections.pkl'
    #limit = -1

    export_txt(opts.dataset_name, opts.detection_folder, opts.output_path)
