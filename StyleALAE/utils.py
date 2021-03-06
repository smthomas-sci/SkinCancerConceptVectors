"""

Various utilities used in training.

Author: Simon Thomas
Date: Jul-24-2020

"""
import numpy as np
import matplotlib.pyplot as plt
import os

import skimage.io as io
import yaml

import tensorflow as tf

from skimage.transform import resize

from tensorflow.keras.callbacks import TensorBoard, Callback
from tensorflow.keras import backend as K

from scipy.spatial.distance import cdist
from lapjv import lapjv


class Summary(TensorBoard):
    """
    A standard tensorboard call back but includes
    a visualisation call at the end of each epoch
    """
    def __init__(self, test_z, test_batch, img_dir, n, weight_dir, save_all_weights=False, **kwargs):
        """
        :param log_dir - the log directory (including the run name),
        :param write_graph - include the graph?
        :param update_freq - "epoch" "batch" or int(n) batches
        :param test_z: the z vector to test on
        :param test_batch: the x, noise and constant vectors to test on
        :param out_dir: where to save the images (path)
        :param n: how many images to show
        :param weight_dir: where to save the weights (every epoch)
        :param kwargs: kwargs relating to TensorBoard class
        """
        super(Summary, self).__init__(**kwargs)
        self.test_z = test_z
        self.test_batch = test_batch
        self.img_dir = img_dir
        self.n = n
        self.weight_dir = weight_dir
        self.save_all = save_all_weights

    def on_epoch_end(self, epoch, logs=None):
        super().on_epoch_end(epoch, logs)
        print()
        self.visualise_progress(self.test_z, self.test_batch, epoch, self.n)

        self.save_weights(epoch)

        # Reset metrics
        self.model.d_loss_tracker.reset_states()
        self.model.g_loss_tracker.reset_states()
        self.model.r_loss_tracker.reset_states()
        self.model.gp_loss_tracker.reset_states()

    def visualise_progress(self, z_test, test_batch, epoch, n):
        # Generate Random Samples
        samples = self.model.generator([z_test[:n]] + [test_batch[1][:n]] + [test_batch[2][:n]]).numpy()
        # Reconstruction Inputs
        recons = self.model.inference(test_batch).numpy()

        samples = np.clip(samples, 0, 1)
        recons = np.clip(recons, 0, 1)

        dim = test_batch[0].shape[1]
        # Show progress
        fig, ax = plt.subplots(3, n, figsize=(n, 3))
        for i in range(n):
            ax[0, i].imshow(test_batch[0][i])
            ax[0, i].axis("off")
            ax[1, i].imshow(recons[i])
            ax[1, i].axis("off")
            ax[2, i].imshow(samples[i])
            ax[2, i].axis("off")

        plt.text(-0.8, 0.4, "Orig.", transform=ax[0, 0].transAxes)
        plt.text(-1, 0.4, "Recon.", transform=ax[1, 0].transAxes)
        plt.text(-1.1, 0.4, "Sample", transform=ax[2, 0].transAxes)

        if self.model.fade:
            alpha = self.model.G.get_layer('Fade_G').alpha.value().numpy()
            m = f" - alpha: {alpha:.3}"
        else:
            m = ""
        plt.text(0, 1.2, f"{dim}x{dim}: {epoch:04d}{m}", transform=ax[0, 0].transAxes)

        if self.model.fade:
            suffix = "_merge"
        else:
            suffix = ""

        fname = os.path.join(self.img_dir, f"progress_{dim:04d}{suffix}_{epoch:04d}.jpg")
        plt.savefig(fname)
        print("Plot saved at", fname)
        plt.close()

    def save_weights(self, epoch):
        if not self.save_all:
            epoch = -1

        if self.model.fade:
            suffix = "_merge_weights"
        else:
            suffix = "_weights"

        out_dir = os.path.join(self.weight_dir, f"Epoch_{epoch:03d}")
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        # Save weights and losses
        DIM = self.model.x_dim
        self.model.G.save_weights(os.path.join(out_dir, f"G_{DIM}x{DIM}{suffix}.h5"))
        self.model.E.save_weights(os.path.join(out_dir, f"E_{DIM}x{DIM}{suffix}.h5"))
        self.model.F.save_weights(os.path.join(out_dir, f"F_{DIM}x{DIM}{suffix}.h5"))
        self.model.D.save_weights(os.path.join(out_dir, f"D_{DIM}x{DIM}{suffix}.h5"))
        print("Weights Saved. - ", out_dir)


class ExponentialMovingAverage(Callback):
    """
    Inspired by # https://gist.github.com/soheilb/c5bf0ba7197caa095acfcb69744df756
    """
    def __init__(self,  generator, weight_dir, fid_dir, save_images=False, k=10_000, decay=0.999):
        self.data = generator
        self.weight_dir = weight_dir
        self.fid_dir = fid_dir
        self.decay = decay
        self.save_images = save_images
        self.k = k
        super(ExponentialMovingAverage, self).__init__()

    def on_train_begin(self, logs={}):
        super().on_train_begin(logs)
        # Create a copy of the generator weights
        self.F_ema = {x.name: K.get_value(x) for x in self.model.??_F}
        self.G_ema = {x.name: K.get_value(x) for x in self.model.??_G}
        print('Created a copy of model weights to initialize moving averaged weights.')

    def on_batch_end(self, batch, logs={}):
        for weight in self.model.??_F:
            ema_t_minus_1 = self.F_ema[weight.name]
            self.F_ema[weight.name] -= (1.0 - self.decay) * (ema_t_minus_1 - K.get_value(weight))
        for weight in self.model.??_G:
            ema_t_minus_1 = self.G_ema[weight.name]
            self.G_ema[weight.name] -= (1.0 - self.decay) * (ema_t_minus_1 - K.get_value(weight))

    def on_epoch_end(self, epoch, logs={}):
        self.orig_F_weights = {x.name: K.get_value(x) for x in self.model.??_F}
        self.orig_G_weights = {x.name: K.get_value(x) for x in self.model.??_G}

        # Set weights and save model
        for weight in self.model.??_F:
            K.set_value(weight, self.F_ema[weight.name])
        for weight in self.model.??_G:
            K.set_value(weight, self.G_ema[weight.name])

        # Save Average model
        print("saving EMA weights...")
        DIM = self.model.x_dim
        self.model.F.save_weights(f"{self.weight_dir}/F_{DIM}x{DIM}_ema_{epoch}.h5")
        self.model.G.save_weights(f"{self.weight_dir}/G_{DIM}x{DIM}_ema_{epoch}.h5")

        # Epoch Output directory
        output_dir = os.path.join(self.fid_dir, f"EPOCH_{epoch}")
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # Predict stuff
        if self.save_images:
            # Save only 10th epoch
            if epoch % 10 == 0:
                print("Generating Images for FID...")
                progress = tf.keras.utils.Progbar(self.k)
                count = 0
                while count < self.k:
                    x, noise, constant = next(self.data.as_numpy_iterator())
                    preds = (self.model.inference([x, noise, constant]).numpy().clip(0, 1)*255.).astype("uint8")
                    for pred in preds:
                        fname = os.path.join(output_dir, f"{DIM}x{DIM}_{count:04}.jpg")
                        io.imsave(fname, pred)
                        count += 1
                        progress.update(count)

        print("Reloading original weights for next epoch")
        # Reload original weights
        for weight in self.model.??_F:
            K.set_value(weight, self.orig_F_weights[weight.name])
        for weight in self.model.??_G:
            K.set_value(weight, self.orig_G_weights[weight.name])


class ConfigParser(object):
    def __init__(self, config_file):
        """
        Parse the YAML config file for the run. All the keys
        :param config_file: path and name of config file
        """
        self._config = yaml.load(open(config_file, 'r').read(),
                                         Loader=yaml.FullLoader)
        # Add attributes
        for key in self._config:
            setattr(self, key, self._config[key])

    def __dir__(self):
        return list(self._config.keys())


def save_2d_projection_grid(img_collection, X_2d, out_res, out_dim):
    grid = np.dstack(np.meshgrid(np.linspace(0, 1, out_dim), np.linspace(0, 1, out_dim))).reshape(-1, 2)
    cost_matrix = cdist(grid, X_2d, "sqeuclidean").astype(np.float32)
    cost_matrix = cost_matrix * (100000 / cost_matrix.max())

    print(cost_matrix.shape)
    row_asses, col_asses, _ = lapjv(cost_matrix)
    grid_jv = grid[col_asses]
    out = np.ones((out_dim * out_res, out_dim * out_res, 3))

    for pos, img in zip(grid_jv, img_collection[0:np.square(out_dim)]):
        h_range = int(np.floor(pos[0] * (out_dim - 1) * out_res))
        w_range = int(np.floor(pos[1] * (out_dim - 1) * out_res))
        out[h_range:h_range + out_res, w_range:w_range + out_res] = img

    return out



if __name__ == "__main__":

    fname = "/home/simon/PycharmProjects/StyleALAE/StyleALAE/configs/celeba_hq_256.yaml"
    config = ConfigParser(fname)
    print(dir(config))




