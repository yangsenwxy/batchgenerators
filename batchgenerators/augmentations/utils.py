# Copyright 2017 Division of Medical Image Computing, German Cancer Research Center (DKFZ)
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

from __future__ import print_function
from builtins import range, zip
import random

import numpy as np
from copy import deepcopy
from scipy.ndimage import map_coordinates
from scipy.ndimage.filters import gaussian_filter, gaussian_gradient_magnitude
from scipy.ndimage.morphology import grey_dilation
from skimage.transform import resize
from scipy.ndimage.measurements import label as lb


def generate_elastic_transform_coordinates(shape, alpha, sigma):
    n_dim = len(shape)
    offsets = []
    for _ in range(n_dim):
        offsets.append(gaussian_filter((np.random.random(shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha)
    tmp = tuple([np.arange(i) for i in shape])
    coords = np.meshgrid(*tmp, indexing='ij')
    indices = [np.reshape(i + j, (-1, 1)) for i, j in zip(offsets, coords)]
    return indices


def create_zero_centered_coordinate_mesh(shape):
    tmp = tuple([np.arange(i) for i in shape])
    coords = np.array(np.meshgrid(*tmp, indexing='ij')).astype(float)
    for d in range(len(shape)):
        coords[d] -= ((np.array(shape).astype(float) - 1) / 2.)[d]
    return coords


def convert_seg_image_to_one_hot_encoding(image, classes=None):
    '''
    Takes as input an nd array of a label map (any dimension). Outputs a one hot encoding of the label map.
    Example (3D): if input is of shape (x, y, z), the output will ne of shape (n_classes, x, y, z)
    '''
    if classes is None:
        classes = np.unique(image)
    out_image = np.zeros([len(classes)]+list(image.shape), dtype=image.dtype)
    for i, c in enumerate(classes):
        out_image[i][image == c] = 1
    return out_image


def elastic_deform_coordinates(coordinates, alpha, sigma):
    n_dim = len(coordinates)
    offsets = []
    for _ in range(n_dim):
        offsets.append(
            gaussian_filter((np.random.random(coordinates.shape[1:]) * 2 - 1), sigma, mode="constant", cval=0) * alpha)
    offsets = np.array(offsets)
    indices = offsets + coordinates
    return indices


def rotate_coords_3d(coords, angle_x, angle_y, angle_z):
    rot_matrix = np.identity(len(coords))
    rot_matrix = create_matrix_rotation_x_3d(angle_x, rot_matrix)
    rot_matrix = create_matrix_rotation_y_3d(angle_y, rot_matrix)
    rot_matrix = create_matrix_rotation_z_3d(angle_z, rot_matrix)
    coords = np.dot(coords.reshape(len(coords), -1).transpose(), rot_matrix).transpose().reshape(coords.shape)
    return coords


def rotate_coords_2d(coords, angle):
    rot_matrix = create_matrix_rotation_2d(angle)
    coords = np.dot(coords.reshape(len(coords), -1).transpose(), rot_matrix).transpose().reshape(coords.shape)
    return coords


def scale_coords(coords, scale):
    return coords * scale


def uncenter_coords(coords):
    shp = coords.shape[1:]
    coords = deepcopy(coords)
    for d in range(coords.shape[0]):
        coords[d] += (shp[d] - 1) / 2.
    return coords


def interpolate_img(img, coords, order=3, mode='nearest', cval=0.0):
    return map_coordinates(img, coords, order=order, mode=mode, cval=cval)


def generate_noise(shape, alpha, sigma):
    noise = np.random.random(shape) * 2 - 1
    noise = gaussian_filter(noise, sigma, mode="constant", cval=0) * alpha
    return noise


def find_entries_in_array(entries, myarray):
    entries = np.array(entries)
    values = np.arange(np.max(myarray) + 1)
    lut = np.zeros(len(values), 'bool')
    lut[entries.astype("int")] = True
    return np.take(lut, myarray.astype(int))


def center_crop_3D_image(img, crop_size):
    center = np.array(img.shape) / 2.
    if type(crop_size) not in (tuple, list):
        center_crop = [int(crop_size)] * len(img.shape)
    else:
        center_crop = crop_size
        assert len(center_crop) == len(
            img.shape), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (3d)"
    return img[int(center[0] - center_crop[0] / 2.):int(center[0] + center_crop[0] / 2.),
           int(center[1] - center_crop[1] / 2.):int(center[1] + center_crop[1] / 2.),
           int(center[2] - center_crop[2] / 2.):int(center[2] + center_crop[2] / 2.)]


def center_crop_3D_image_batched(img, crop_size):
    # dim 0 is batch, dim 1 is channel, dim 2, 3 and 4 are x y z
    center = np.array(img.shape[2:]) / 2.
    if type(crop_size) not in (tuple, list):
        center_crop = [int(crop_size)] * (len(img.shape) - 2)
    else:
        center_crop = crop_size
        assert len(center_crop) == (len(
            img.shape) - 2), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (3d)"
    return img[:, :, int(center[0] - center_crop[0] / 2.):int(center[0] + center_crop[0] / 2.),
           int(center[1] - center_crop[1] / 2.):int(center[1] + center_crop[1] / 2.),
           int(center[2] - center_crop[2] / 2.):int(center[2] + center_crop[2] / 2.)]


def center_crop_2D_image(img, crop_size):
    center = np.array(img.shape) / 2.
    if type(crop_size) not in (tuple, list):
        center_crop = [int(crop_size)] * len(img.shape)
    else:
        center_crop = crop_size
        assert len(center_crop) == len(
            img.shape), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (2d)"
    return img[int(center[0] - center_crop[0] / 2.):int(center[0] + center_crop[0] / 2.),
           int(center[1] - center_crop[1] / 2.):int(center[1] + center_crop[1] / 2.)]


def center_crop_2D_image_batched(img, crop_size):
    # dim 0 is batch, dim 1 is channel, dim 2 and 3 are x y
    center = np.array(img.shape[2:]) / 2.
    if type(crop_size) not in (tuple, list):
        center_crop = [int(crop_size)] * (len(img.shape) - 2)
    else:
        center_crop = crop_size
        assert len(center_crop) == (len(
            img.shape) - 2), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (2d)"
    return img[:, :, int(center[0] - center_crop[0] / 2.):int(center[0] + center_crop[0] / 2.),
           int(center[1] - center_crop[1] / 2.):int(center[1] + center_crop[1] / 2.)]


def random_crop_3D_image(img, crop_size):
    if type(crop_size) not in (tuple, list):
        crop_size = [crop_size] * len(img.shape)
    else:
        assert len(crop_size) == len(
            img.shape), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (3d)"

    if crop_size[0] < img.shape[0]:
        lb_x = np.random.randint(0, img.shape[0] - crop_size[0])
    elif crop_size[0] == img.shape[0]:
        lb_x = 0
    else:
        raise ValueError("crop_size[0] must be smaller or equal to the images x dimension")

    if crop_size[1] < img.shape[1]:
        lb_y = np.random.randint(0, img.shape[1] - crop_size[1])
    elif crop_size[1] == img.shape[1]:
        lb_y = 0
    else:
        raise ValueError("crop_size[1] must be smaller or equal to the images y dimension")

    if crop_size[2] < img.shape[2]:
        lb_z = np.random.randint(0, img.shape[2] - crop_size[2])
    elif crop_size[2] == img.shape[2]:
        lb_z = 0
    else:
        raise ValueError("crop_size[2] must be smaller or equal to the images z dimension")

    return img[lb_x:lb_x + crop_size[0], lb_y:lb_y + crop_size[1], lb_z:lb_z + crop_size[2]]


def random_crop_3D_image_batched(img, crop_size):
    if type(crop_size) not in (tuple, list):
        crop_size = [crop_size] * (len(img.shape) - 2)
    else:
        assert len(crop_size) == (len(
            img.shape) - 2), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (3d)"

    if crop_size[0] < img.shape[2]:
        lb_x = np.random.randint(0, img.shape[2] - crop_size[0])
    elif crop_size[0] == img.shape[2]:
        lb_x = 0
    else:
        raise ValueError("crop_size[0] must be smaller or equal to the images x dimension")

    if crop_size[1] < img.shape[3]:
        lb_y = np.random.randint(0, img.shape[3] - crop_size[1])
    elif crop_size[1] == img.shape[3]:
        lb_y = 0
    else:
        raise ValueError("crop_size[1] must be smaller or equal to the images y dimension")

    if crop_size[2] < img.shape[4]:
        lb_z = np.random.randint(0, img.shape[4] - crop_size[2])
    elif crop_size[2] == img.shape[4]:
        lb_z = 0
    else:
        raise ValueError("crop_size[2] must be smaller or equal to the images z dimension")

    return img[:, :, lb_x:lb_x + crop_size[0], lb_y:lb_y + crop_size[1], lb_z:lb_z + crop_size[2]]


def random_crop_2D_image(img, crop_size):
    if type(crop_size) not in (tuple, list):
        crop_size = [crop_size] * len(img.shape)
    else:
        assert len(crop_size) == len(
            img.shape), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (2d)"

    if crop_size[0] < img.shape[0]:
        lb_x = np.random.randint(0, img.shape[0] - crop_size[0])
    elif crop_size[0] == img.shape[0]:
        lb_x = 0
    else:
        raise ValueError("crop_size[0] must be smaller or equal to the images x dimension")

    if crop_size[1] < img.shape[1]:
        lb_y = np.random.randint(0, img.shape[1] - crop_size[1])
    elif crop_size[1] == img.shape[1]:
        lb_y = 0
    else:
        raise ValueError("crop_size[1] must be smaller or equal to the images y dimension")

    return img[lb_x:lb_x + crop_size[0], lb_y:lb_y + crop_size[1]]


def random_crop_2D_image_batched(img, crop_size):
    if type(crop_size) not in (tuple, list):
        crop_size = [crop_size] * (len(img.shape) - 2)
    else:
        assert len(crop_size) == (len(
            img.shape) - 2), "If you provide a list/tuple as center crop make sure it has the same len as your data has dims (2d)"

    if crop_size[0] < img.shape[2]:
        lb_x = np.random.randint(0, img.shape[2] - crop_size[0])
    elif crop_size[0] == img.shape[2]:
        lb_x = 0
    else:
        raise ValueError("crop_size[0] must be smaller or equal to the images x dimension")

    if crop_size[1] < img.shape[3]:
        lb_y = np.random.randint(0, img.shape[3] - crop_size[1])
    elif crop_size[1] == img.shape[3]:
        lb_y = 0
    else:
        raise ValueError("crop_size[1] must be smaller or equal to the images y dimension")

    return img[:, :, lb_x:lb_x + crop_size[0], lb_y:lb_y + crop_size[1]]


def resize_image_by_padding(image, new_shape, pad_value=None):
    shape = tuple(list(image.shape))
    new_shape = tuple(np.max(np.concatenate((shape, new_shape)).reshape((2, len(shape))), axis=0))
    if pad_value is None:
        if len(shape) == 2:
            pad_value = image[0, 0]
        elif len(shape) == 3:
            pad_value = image[0, 0, 0]
        else:
            raise ValueError("Image must be either 2 or 3 dimensional")
    res = np.ones(list(new_shape), dtype=image.dtype) * pad_value
    start = np.array(new_shape) / 2. - np.array(shape) / 2.
    if len(shape) == 2:
        res[int(start[0]):int(start[0]) + int(shape[0]), int(start[1]):int(start[1]) + int(shape[1])] = image
    elif len(shape) == 3:
        res[int(start[0]):int(start[0]) + int(shape[0]), int(start[1]):int(start[1]) + int(shape[1]),
        int(start[2]):int(start[2]) + int(shape[2])] = image
    return res


def resize_image_by_padding_batched(image, new_shape, pad_value=None):
    shape = tuple(list(image.shape[2:]))
    new_shape = tuple(np.max(np.concatenate((shape, new_shape)).reshape((2, len(shape))), axis=0))
    if pad_value is None:
        if len(shape) == 2:
            pad_value = image[0, 0]
        elif len(shape) == 3:
            pad_value = image[0, 0, 0]
        else:
            raise ValueError("Image must be either 2 or 3 dimensional")
    start = np.array(new_shape) / 2. - np.array(shape) / 2.
    if len(shape) == 2:
        res = np.ones((image.shape[0], image.shape[1], new_shape[0], new_shape[1]), dtype=image.dtype) * pad_value
        res[:, :, int(start[0]):int(start[0]) + int(shape[0]), int(start[1]):int(start[1]) + int(shape[1])] = image[:,
                                                                                                              :]
    elif len(shape) == 3:
        res = np.ones((image.shape[0], image.shape[1], new_shape[0], new_shape[1], new_shape[2]),
                      dtype=image.dtype) * pad_value
        res[:, :, int(start[0]):int(start[0]) + int(shape[0]), int(start[1]):int(start[1]) + int(shape[1]),
        int(start[2]):int(start[2]) + int(shape[2])] = image[:, :]
    return res


def create_matrix_rotation_x_3d(angle, matrix=None):
    rotation_x = np.array([[1, 0, 0],
                           [0, np.cos(angle), -np.sin(angle)],
                           [0, np.sin(angle), np.cos(angle)]])
    if matrix is None:
        return rotation_x

    return np.dot(matrix, rotation_x)


def create_matrix_rotation_y_3d(angle, matrix=None):
    rotation_y = np.array([[np.cos(angle), 0, np.sin(angle)],
                           [0, 1, 0],
                           [-np.sin(angle), 0, np.cos(angle)]])
    if matrix is None:
        return rotation_y

    return np.dot(matrix, rotation_y)


def create_matrix_rotation_z_3d(angle, matrix=None):
    rotation_z = np.array([[np.cos(angle), -np.sin(angle), 0],
                           [np.sin(angle), np.cos(angle), 0],
                           [0, 0, 1]])
    if matrix is None:
        return rotation_z

    return np.dot(matrix, rotation_z)


def create_matrix_rotation_2d(angle, matrix=None):
    rotation = np.array([[np.cos(angle), -np.sin(angle)],
                         [np.sin(angle), np.cos(angle)]])
    if matrix is None:
        return rotation

    return np.dot(matrix, rotation)


def create_random_rotation(angle_x=(0, 2 * np.pi), angle_y=(0, 2 * np.pi), angle_z=(0, 2 * np.pi)):
    return create_matrix_rotation_x_3d(np.random.uniform(*angle_x),
                                       create_matrix_rotation_y_3d(np.random.uniform(*angle_y),
                                                                   create_matrix_rotation_z_3d(
                                                                       np.random.uniform(*angle_z))))


def illumination_jitter(img, u, s, sigma):
    # img must have shape [....., c] where c is the color channel
    alpha = np.random.normal(0, sigma, s.shape)
    jitter = np.dot(u, alpha * s)
    img2 = np.array(img)
    for c in range(img.shape[0]):
        img2[c] = img[c] + jitter[c]
    return img2


def general_cc_var_num_channels(img, diff_order=0, mink_norm=1, sigma=1, mask_im=None, saturation_threshold=255,
                                dilation_size=3, clip_range=True):
    # img must have first dim color channel! img[c, x, y(, z, ...)]
    dim_img = len(img.shape[1:])
    if clip_range:
        minm = img.min()
        maxm = img.max()
    img_internal = np.array(img)
    if mask_im is None:
        mask_im = np.zeros(img_internal.shape[1:], dtype=bool)
    img_dil = deepcopy(img_internal)
    for c in range(img.shape[0]):
        img_dil[c] = grey_dilation(img_internal[c], tuple([dilation_size] * dim_img))
    mask_im = mask_im | np.any(img_dil >= saturation_threshold, axis=0)
    if sigma != 0:
        mask_im[:sigma, :] = 1
        mask_im[mask_im.shape[0] - sigma:, :] = 1
        mask_im[:, mask_im.shape[1] - sigma:] = 1
        mask_im[:, :sigma] = 1
        if dim_img == 3:
            mask_im[:, :, mask_im.shape[2] - sigma:] = 1
            mask_im[:, :, :sigma] = 1

    output_img = deepcopy(img_internal)

    if diff_order == 0 and sigma != 0:
        for c in range(img_internal.shape[0]):
            img_internal[c] = gaussian_filter(img_internal[c], sigma, diff_order)
    elif diff_order == 1:
        for c in range(img_internal.shape[0]):
            img_internal[c] = gaussian_gradient_magnitude(img_internal[c], sigma)
    elif diff_order > 1:
        raise ValueError("diff_order can only be 0 or 1. 2 is not supported (ToDo, maybe)")

    img_internal = np.abs(img_internal)

    white_colors = []

    if mink_norm != -1:
        kleur = np.power(img_internal, mink_norm)
        for c in range(kleur.shape[0]):
            white_colors.append(np.power((kleur[c][mask_im != 1]).sum(), 1. / mink_norm))
    else:
        for c in range(img_internal.shape[0]):
            white_colors.append(np.max(img_internal[c][mask_im != 1]))

    som = np.sqrt(np.sum([i ** 2 for i in white_colors]))

    white_colors = [i / som for i in white_colors]

    for c in range(output_img.shape[0]):
        output_img[c] /= (white_colors[c] * np.sqrt(3.))

    if clip_range:
        output_img[output_img < minm] = minm
        output_img[output_img > maxm] = maxm
    return white_colors, output_img


def convert_seg_to_bounding_box_coordinates(seg, class_target, pid, dim, n_max_gt=3):

        bb_target = np.zeros((seg.shape[0], n_max_gt, dim*2)) #for whole batch or single patient?
        roi_masks = np.zeros((seg.shape[0], n_max_gt, *seg.shape[2:]))
        roi_class_ids = np.zeros((seg.shape[0], n_max_gt, 1))
        for b in range(seg.shape[0]):

            if np.sum(seg!=0) > 0:
                clusters, n_cands = lb(seg[b])
                rois = np.array([(clusters == ii) * 1 for ii in range(1, n_cands + 1)])  # separate clusters and concat
                rois = rois[:n_max_gt] #cut clutter out to save memory
                # print("Rois in transformer", rois.shape, pid[b])
                for rix, r in enumerate(rois):
                    seg_ixs = np.argwhere(r != 0)
                    coord_list = [np.min(seg_ixs[:, 2])-1, np.min(seg_ixs[:, 1])-1, np.max(seg_ixs[:, 2])+1,
                                     np.max(seg_ixs[:, 1])+1]
                    if dim == 3:

                        coord_list.extend([np.min(seg_ixs[:, 3])-1, np.max(seg_ixs[:, 3])+1])

                    bb_target[b, rix] = coord_list
                    roi_masks[b, rix] = r
                    roi_class_ids[b, rix] = class_target[b] + 1 # add background class

                # print("CHECK BBTARGET", bb_target[b], roi_masks[b].shape, roi_class_ids[b], pid[b])
            else:
                print("fail: bb kicked out of image by data augmentation", np.sum(seg!=0), pid[b], class_target)


        return bb_target, roi_masks, roi_class_ids


def transpose_channels(batch):
    if len(batch.shape) == 4:
        return np.transpose(batch, axes=[0, 2, 3, 1])
    elif len(batch.shape) == 5:
        return np.transpose(batch, axes=[0, 4, 2, 3, 1])
    else:
        raise ValueError("wrong dimensions in transpose_channel generator!")


def resize_segmentation(segmentation, new_shape, order=3):
    '''
    Resizes a segmentation map. Supports all orders (see skimage documentation). Will transform segmentation map to one
    hot encoding which is resized and transformed back to a segmentation map.
    This prevents interpolation artifacts ([0, 0, 2] -> [0, 1, 2])
    :param segmentation:
    :param new_shape:
    :param order:
    :return:
    '''
    unique_labels = np.unique(segmentation)
    assert len(segmentation.shape) == len(new_shape), "new shape must have same dimensionality as segmentation"
    if order == 0:
        return resize(segmentation, new_shape, order, mode="constant", cval=0, clip=True)
    else:
        reshaped_multihot = np.zeros([len(unique_labels)] + list(new_shape), dtype=float)
        for i, c in enumerate(unique_labels):
            reshaped_multihot[i] = np.round(
                resize((segmentation == c).astype(float), new_shape, order, mode="constant", cval=0, clip=True))
        reshaped = unique_labels[np.argmax(reshaped_multihot, 0)].astype(segmentation.dtype)
        return reshaped


def resize_softmax_output(softmax_output, new_shape, order=3):
    '''
    Resizes softmax output. Resizes each channel in c separately and fuses results back together

    :param softmax_output: c x x x y x z
    :param new_shape: x x y x z
    :param order:
    :return:
    '''
    new_shp = [softmax_output.shape[0]] + list(new_shape)
    result = np.zeros(new_shp, dtype=softmax_output.dtype)
    for i in range(softmax_output.shape[0]):
        result[i] = resize(softmax_output[i].astype(float), new_shape, order, "constant", 0, True)
    return result


def get_range_val(value, rnd_type="uniform"):
    if isinstance(value, (list, tuple, np.ndarray)):
        if len(value) == 2:
            if value[0] == value[1]:
                n_val = value[0]
            else:
                orig_type = type(value[0])
                if rnd_type == "uniform":
                    n_val = random.uniform(value[0], value[1])
                elif rnd_type == "normal":
                    n_val = random.normalvariate(value[0], value[1])
                n_val = orig_type(n_val)
        elif len(value) == 1:
            n_val = value[0]
        return n_val
    else:
        return value



