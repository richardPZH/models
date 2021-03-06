import numpy as np
import datareader as reader
import paddle.fluid as fluid
from metrics import calculate_order_dist_matrix
from metrics import get_gpu_num

class quadrupletloss():
    def __init__(self, 
                 train_batch_size = 80, 
                 samples_each_class = 2,
                 margin=0.1):
        self.margin = margin
        num_gpus = get_gpu_num()
        self.samples_each_class = samples_each_class
        self.train_batch_size = train_batch_size
        assert(train_batch_size % num_gpus == 0)
        self.cal_loss_batch_size = train_batch_size / num_gpus
        assert(self.cal_loss_batch_size % samples_each_class == 0)
        class_num = train_batch_size / samples_each_class
        self.train_reader = reader.quadruplet_train(class_num, samples_each_class)
        self.test_reader = reader.test()

    def loss(self, input):
        feature = fluid.layers.l2_normalize(input, axis=1)
        samples_each_class = self.samples_each_class
        batch_size = self.cal_loss_batch_size
        margin = self.margin
        d = calculate_order_dist_matrix(feature, self.cal_loss_batch_size, self.samples_each_class)
        ignore, pos, neg = fluid.layers.split(d, num_or_sections= [1, 
            samples_each_class-1, batch_size-samples_each_class], dim=1)
        ignore.stop_gradient = True
        pos_max = fluid.layers.reduce_max(pos)
        neg_min = fluid.layers.reduce_min(neg)
        pos_max = fluid.layers.sqrt(pos_max)
        neg_min = fluid.layers.sqrt(neg_min)
        loss = fluid.layers.relu(pos_max - neg_min + margin)
        return loss
    
