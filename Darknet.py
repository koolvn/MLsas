import glob
import os
from typing import List, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Detector:
    """Wrapper for Darknet detection model to perform inference
     with opencv dnn module"""

    def __init__(self, net_cfg_path: str, weights_path: str,
                 labels_path: str, verbose: bool = True, use_gpu: bool = True,
                 text_in_image_corner: bool = False):
        self._net_cfg_path = net_cfg_path
        self.weights_path = weights_path
        self._labels_path = labels_path
        self.verbose = verbose
        self.text_in_image_corner = text_in_image_corner
        with open(self._net_cfg_path, 'r') as f:
            cfg = f.readlines()
            cfg = dict([x.strip().split('=') for x in cfg if '=' in x and '#' not in x])
        self.cfg = {k: int(v) for k, v in cfg.items() if v.isnumeric()}

        self.labels = open(self._labels_path).read().strip().split("\n")
        self.class2label = dict(enumerate(self.labels))

        self.nn = cv2.dnn.readNetFromDarknet(self._net_cfg_path,
                                             self.weights_path)
        self.output_layers = self.nn.getUnconnectedOutLayersNames()
        if use_gpu:
            self.nn.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            self.nn.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        if self.verbose:
            print('GPU(s) is available' if cv2.cuda.getCudaEnabledDeviceCount()
                  else 'No GPU(s) found')

    def __repr__(self):
        return f"Net: {self._net_cfg_path}\nWeights:{self.weights_path}\n" \
               f"Labels: {self.class2label}\nVerbose: {self.verbose}"

    def prepare_input_image(self, image: np.ndarray, swapRB=True, crop=False):
        return cv2.dnn.blobFromImage(image,
                                     1 / 255,
                                     (int(self.cfg['width']),
                                      int(self.cfg['height'])
                                      ),
                                     swapRB=swapRB,
                                     crop=crop)

    def __call__(self, image: np.ndarray, threshold=0.5, nms_threshold=0.4,
                 return_raw=False, draw_bboxes=True,
                 extend_w_h: Tuple[float, float] = (1.0, 1.0),
                 filter_class_ids: List[int] = None, **prepare_image_kwargs
                 ) -> Tuple[np.ndarray, np.ndarray]:
        """Performs inference of the given detection model"""
        blob = self.prepare_input_image(image.copy(), **prepare_image_kwargs)
        self.nn.setInput(blob)
        predictions = self.nn.forward(self.output_layers)
        if return_raw:
            return predictions

        h, w = image.shape[:2]
        predictions = self.process_predictions(predictions, w, h,
                                               threshold, nms_threshold,
                                               extend_w_h,
                                               filter_class_ids)
        if draw_bboxes and len(predictions) > 0:
            for idx, pred in enumerate(predictions):
                x, y, w, h = pred[:4]
                x, y = int(x), int(y)
                xx, yy = int(x + w), int(y + h)
                cv2.rectangle(image, (x, y), (xx, yy), (0, 0, 255), 2)
                if self.text_in_image_corner:
                    cv2.putText(image,
                                f"{self.class2label.get(pred[5])}-{idx+1}",
                                # f" {round(pred[4] * 100)}%",
                                (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.85,
                                (0, 0, 255), 2,
                                cv2.LINE_AA)
                else:
                    cv2.putText(image,
                                f"{self.class2label.get(pred[5])}-{idx+1}",
                                # f" {round(pred[4] * 100)}%",
                                (x + 5, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.85,
                                (0, 0, 255), 2,
                                cv2.LINE_AA)
        return image, predictions

    @staticmethod
    def process_predictions(predictions, W, H,
                            threshold=0.5, nms_threshold=0.4,
                            extend_w_h: Tuple[float, float] = (1.0, 1.0),
                            filter_class_ids: List[int] = None):
        boxes = []
        confidences = []
        classIDs = []
        for pred in predictions:
            for detection in pred:
                scores = detection[5:]
                classID = np.argmax(scores)
                if filter_class_ids and classID not in filter_class_ids:
                    continue
                confidence = scores[classID]
                if confidence > threshold:
                    # scale the bounding box coordinates back relative to the
                    # size of the image, keeping in mind that YOLO actually
                    # returns the center (x, y)-coordinates of the bounding
                    # box followed by the boxes' width and height
                    box = detection[:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype(int)
                    # use the center (x, y)-coordinates to derive the top and
                    # and left corner of the bounding box
                    if extend_w_h is not None:
                        width *= extend_w_h[0]
                        height *= extend_w_h[1]
                    x = max(0, int(centerX - (width / 2)))
                    y = max(0, int(centerY - (height / 2)))
                    # update our list of bounding box coordinates, confidences,
                    # and class IDs
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)

        idxs = cv2.dnn.NMSBoxes(boxes, confidences, threshold, nms_threshold)
        boxes = np.array(boxes).reshape([-1, 4])
        confidences = np.array(confidences).reshape([-1, 1])
        classIDs = np.array(classIDs).reshape([-1, 1])

        result = np.concatenate([boxes, confidences, classIDs], axis=1)
        if len(idxs) > 0:
            return result[idxs.flatten()]
        else:
            return np.array([])


# TODO: Write docstrings
class ClassificationWeightsParser:
    def __init__(self, darknet_path='./darknet',
                 validation_images_dir='./Dataset/tmp/March-29/',
                 net_cfg='darknet.cfg', clf_data='spec_trans_clf.data',
                 show_errors=False, verbose=False,
                 image_mask='*.*g'):
        self._DARKNET_PATH = os.path.abspath(darknet_path)
        self._NET = net_cfg
        self._CLF_DATA = clf_data
        self._VAL_TXT_PATH = os.path.join(self._DARKNET_PATH, 'val.txt')
        self.OUTPUT_DIR = './'
        self.SHOW_ERRORS = show_errors
        self.VERBOSE = verbose
        self.make_val_txt(os.path.abspath(validation_images_dir),
                          output_dir=self._DARKNET_PATH,
                          image_ext_mask=image_mask)
        self.class2label = self._get_class2label_dict()
        self.labels = list(self.class2label.values())

    def __call__(self, weights_path, save_csv=False, show_errors=None):
        if show_errors:
            self.SHOW_ERRORS = show_errors
        self.run_classifier(weights_path)
        dataframe, accuracy = self.parse_results(weights_path,
                                                 save_csv=save_csv)
        return dataframe, accuracy

    @staticmethod
    def make_val_txt(path_to_images, output_dir, image_ext_mask='*.*g'):
        val = glob.glob(os.path.join(path_to_images, image_ext_mask))
        val = [x + '\n' for x in val]
        with open(os.path.join(output_dir, 'val.txt'), 'w') as f:
            f.writelines(val)

    def _get_class2label_dict(self):
        with open(os.path.join(self._DARKNET_PATH, self._CLF_DATA), 'r') as data:
            data = data.readlines()
            data = [x.strip().split('=')
                    for x in data if x.startswith('labels')][0][1].strip()

        with open(os.path.join(self._DARKNET_PATH, data), 'r') as labels:
            labels = labels.readlines()
            labels = [(cls, label.strip()) for cls, label in enumerate(labels)]
        return dict(labels)

    def run_classifier(self, weights_path: str):
        cmd = f'cd "{self._DARKNET_PATH}" && ' \
              f'./darknet classifier predict ' \
              f'"{self._CLF_DATA}" "{self._NET}" "{weights_path}" < ' \
              f'"{self._VAL_TXT_PATH}"  > ' \
              f'"{os.path.join(self._DARKNET_PATH, "val.results")}"'
        if self.VERBOSE:
            print(cmd)
        os.system(cmd)
        if self.VERBOSE:
            print(f'Finished parsing of {weights_path.split("/")[-1]}')

    def parse_results(self, weights_path, save_csv):
        with open(os.path.join(self._DARKNET_PATH, 'val.results'), 'r') as r:
            r = r.readlines()[8:]
            r = [x for x in r if 'Enter Image Path' not in x]

        with open(os.path.join(self._DARKNET_PATH,
                               self._CLF_DATA), 'r') as n_classes:
            n_classes = n_classes.readlines()
            topN = int([x.strip().split('=')[1] for x in n_classes
                        if 'top' in x][0])
            n_classes = int([x.strip().split('=')[1] for x in n_classes
                             if 'classes' in x][0])
            n_classes = min([topN, n_classes]) + 1

        top1 = [x.strip().split() for x in r[1::n_classes]]
        top1 = pd.DataFrame(top1, columns=['y_pred', 'proba'])
        top1['y_pred'] = top1['y_pred'].str.replace(':', '')

        fnames = [x.split()[0][:-1] for x in r[::n_classes]]
        results = pd.concat([pd.Series(fnames), top1], axis=1)
        results.columns = ['image_path', 'y_pred', 'proba']
        results['proba'] = results['proba'].astype(float)

        results['y_true'] = results['image_path'].str.split('/').str[-1].str.split('_').str[0]
        results['accurate'] = results['y_true'] == results['y_pred']
        accuracy = results['accurate'].sum() / len(results) * 100

        if self.VERBOSE:
            print(results.set_index('image_path'))
            print(f"Accuracy: {accuracy: .2f}%")
        if save_csv:
            out_filename = f'results_{weights_path.split("/")[-1]}.csv'
            results.set_index('image_path').to_csv(os.path.join(self.OUTPUT_DIR,
                                                                out_filename))
        if self.SHOW_ERRORS:
            i = 0
            for idx, r in results[results['accurate'].eq(False)].iterrows():
                i += 1
                plt.imshow(plt.imread(r['image_path']))
                plt.title(f"{r['y_pred']} - {r['proba'] * 100: .2f}%"
                          f"\nTrue label: {r['y_true']}")
                plt.show()
                print('Classified wrong:', r['image_path'].split('/')[-1])
            print('Total errors:', i)
        return results.set_index('image_path'), (weights_path.split('/')[-1],
                                                 round(accuracy, 2))
