# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
from PIL import Image

NUM_CLASS = 7
IMAGE_HEIGHT = 256
IMAGE_WIDTH = 256

class ImageNotExistException(Exception):
    def __init__(self, img_name):
        self.img_name = img_name
        
    def __str__(self):
        # 图像的对应预测标签图不存在: %s
        return "Image not exist: %s" % self.img_name
    
        
class ImageIOException(Exception):
    def __init__(self, img_name):
        self.img_name = img_name
        
    def __str__(self):
        # 预测标签图读取失败: %s
        return "Image read fail: %s" % self.img_name

class ImageShapeException(Exception):
    def __init__(self, img_name):
        self.img_name = img_name
    
    def __str__(self):
        # 预测标签图的尺寸和图像不匹配（应该为 %dx%d): %s
        return "Image shape is not match (%d, %d): %s" % (IMAGE_HEIGHT, IMAGE_WIDTH, self.img_name)
    
class ImageValueException(Exception):
    def __init__(self, img_name):
        self.img_name = img_name
    
    def __str__(self):
        # 预测标签图的像素值应该在[0, %d]区间内: %s
        return "Pixel value should in [0, %d]: %s" % (NUM_CLASS-1, self.img_name)

class ImageChannelException(Exception):
    def __init__(self, img_name):
        self.img_name = img_name
    
    def __str__(self):
        # 预测标签图应该是单通道png图像: %s
        return "Image should be one channle: %s" % self.img_name

class ImageNumException(Exception):
    def __init__(self, num, gt_num):
        self.num = num
        self.gt_num = gt_num
    
    def __str__(self):
        # 预测标签图的数量和测试图像数量不匹配（数量应该为 %d): %s
        return "The number of predicted images is incorrect: %d (should be %d)" % (self.num, self.gt_num)
        
class ConfusionMatrix(object):
    def __init__(self, num_classes=7):
        self.confusion_matrix = np.zeros((num_classes, num_classes), dtype=np.int32)
        self.num_classes = num_classes

    def calculate(self, pred, grt):
        valid_idx = (grt >= 0) & (grt < self.num_classes)
        sub_cm = np.bincount(pred[valid_idx] * self.num_classes + grt[valid_idx],
                             minlength=self.num_classes ** 2).reshape(self.num_classes, self.num_classes)
        self.confusion_matrix += sub_cm

    def _iou(self):
        cm_diag = np.diag(self.confusion_matrix)
        iou = cm_diag / (np.sum(self.confusion_matrix, axis=1) + np.sum(self.confusion_matrix, axis=0) - cm_diag)
        return iou

    def miou(self):
        iou = self._iou()
        return np.nanmean(iou)

def evaluate(pred_path, grt_path):
    file_list = [name for name in os.listdir(grt_path) if name.endswith('.png')]
    pred_list = [name for name in os.listdir(pred_path) if name.endswith('.png')]
    
    if len(pred_list) != len(file_list):
        raise ImageNumException(len(pred_list), len(file_list))  # 输入图像数量不正确

    cm = ConfusionMatrix(NUM_CLASS)
    
    for file_name in file_list:
        
        pred_file = os.path.join(pred_path, file_name)
        if not os.path.exists(pred_file):
            raise ImageNotExistException(file_name)  # 没有找到对应的预测图像
        
        try:
            pred = Image.open(pred_file)
        except IOError:
            raise ImageIOException(file_name)  # 图像损坏，读取失败

        if pred.mode != 'L' and pred.mode != 'P':
            raise ImageChannelException(file_name)  # 图像必须是单通道

        if pred.height != IMAGE_HEIGHT or pred.width != IMAGE_WIDTH:
            raise ImageShapeException(file_name)  # 图像尺寸必须256x256

        pred = np.array(pred, dtype=np.int32)
        
        if pred.min() < 0 or pred.max() >= NUM_CLASS:
            raise ImageValueException(file_name)  # 图像像素预测值必须在[0, 6]范围内
        
        grt = np.array(Image.open(os.path.join(grt_path, file_name)), dtype=np.int32)
        cm.calculate(pred, grt)

    return cm.miou()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('python evaluation.py ${pred_dir} ${grt_dir}')
    pred_path = sys.argv[1]
    grt_path = sys.argv[2]
    result = evaluate(pred_path, grt_path)
    print(result)

