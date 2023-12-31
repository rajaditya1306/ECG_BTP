# -*- coding: utf-8 -*-
"""ST-CNN-GAP-5.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DRNS43KEExAwly4mtYiWiD2fiibKuzWm

##### Mount Google Drive (Optional)
"""

# from google.colab import drive
# drive.mount('/content/drive')

"""##### Import Libraries"""

from tensorflow.keras import layers, optimizers, losses, metrics, regularizers, callbacks
import tensorflow.keras.backend as K
import tensorflow as tf
from keras.models import Model
import numpy as np

"""##### Import Data"""

path = './data/'
x_train = np.load(path + 'x_train.npy', allow_pickle=True)
y_train = np.load(path + 'y_train.npy', allow_pickle=True)
x_test  = np.load(path + 'x_test.npy', allow_pickle=True)
y_test  = np.load(path + 'y_test.npy', allow_pickle=True)

# transpose matrix => records x 1000 x 12 -> records x 12 x 1000
x_train = x_train.transpose(0, 2, 1)
x_test  = x_test.transpose(0, 2, 1)

# add another channel in the end
# x_train = x_train.reshape(19634, 12, 1000, 1)
# x_test  = x_test.reshape(2203, 12, 1000, 1)

# print("x_train:", x_train.shape)
# print("y_train:", y_train.shape)
# print("x_test :", x_test.shape)
# print("y_test :", y_test.shape)
print('Data loaded')

# # apply Discrete Cosine Transformation (DCT)
# from scipy.fftpack import dct

# def DCT(x, vertical=False):
#   if vertical:
#     x = x.transpose(0, 2, 1)

#   n, r, c = x.shape
#   for i in range(n):
#     for j in range(r):
#       x[i][j] = dct(x[i][j], 2)

#   if vertical:
#     x = x.transpose(0, 2, 1)


# # apply Horizontal DCT
# DCT(x_train)
# DCT(x_test)

# # apply Vertical DCT
# DCT(x_train, True)
# DCT(x_test, True)

# add another channel
x_train = x_train.reshape(19634, 12, 1000, 1)
x_test  = x_test.reshape(2203, 12, 1000, 1)

print(x_train.shape, x_test.shape)

"""##### Model"""

# Main Version
input = layers.Input(shape=(12, 1000, 1))

X = layers.Conv2D(filters=32, kernel_size=(1, 5))(input)
X = layers.BatchNormalization()(X)
X = layers.ReLU()(X)
X = layers.MaxPooling2D(pool_size=(1, 2), strides=1)(X)

convC1 = layers.Conv2D(filters=64, kernel_size=(1, 7))(X)

X = layers.Conv2D(filters=32, kernel_size=(1, 5))(X)
X = layers.BatchNormalization()(X)
X = layers.ReLU()(X)
X = layers.MaxPooling2D(pool_size=(1, 4), strides=1)(X)

convC2 = layers.Conv2D(filters=64, kernel_size=(1, 6))(convC1)

X = layers.Conv2D(filters=64, kernel_size=(1, 5))(X)
X = layers.BatchNormalization()(X)
X = layers.Add()([convC2, X])           # skip Connection
X = layers.ReLU()(X)
X = layers.MaxPooling2D(pool_size=(1, 2), strides=1)(X)

convE1 = layers.Conv2D(filters=32, kernel_size=(1, 4))(X)

X = layers.Conv2D(filters=64, kernel_size=(1, 3))(X)
X = layers.BatchNormalization()(X)
X = layers.ReLU()(X)
X = layers.MaxPooling2D(pool_size=(1, 4), strides=1)(X)

convE2 = layers.Conv2D(filters=64, kernel_size=(1, 5))(convE1)

X = layers.Conv2D(filters=64, kernel_size=(1, 3))(X)
X = layers.BatchNormalization()(X)
X = layers.Add()([convE2, X])         # skip Connection
X = layers.ReLU()(X)
X = layers.MaxPooling2D(pool_size=(1, 2), strides=1)(X)
print('Added 5 layers for temporal analysis')

X = layers.Conv2D(filters=64, kernel_size=(12, 1))(X)
X = layers.BatchNormalization()(X)
X = layers.ReLU()(X)
X = layers.GlobalAveragePooling2D()(X)
print('Added 1 layer for spatial Analysis')

X = layers.Flatten()(X)
print(X.shape)

X = layers.Dense(units=128, kernel_regularizer=regularizers.L2(0.005))(X)
X = layers.BatchNormalization()(X)
X = layers.ReLU()(X)
X = layers.Dropout(rate=0.1)(X)

X = layers.Dense(units=64, kernel_regularizer=regularizers.L2(0.009))(X)
X = layers.BatchNormalization()(X)
X = layers.ReLU()(X)
X = layers.Dropout(rate=0.15)(X)
print('Added 2 fully connected layers')

output = layers.Dense(5, activation='sigmoid')(X)
model = Model(inputs=input, outputs=output)
print(model.summary())

# converting list type elements in numpy array to numpy arrays
# def convert_lists_to_arrays(data):
#     for i in range(len(data)):
#         if isinstance(data[i], list):
#             data[i] = np.array(data[i])
#     return data

# x_train = convert_lists_to_arrays(x_train)
# y_train = convert_lists_to_arrays(y_train)
# x_test = convert_lists_to_arrays(x_test)
# y_test = convert_lists_to_arrays(y_test)

print(y_test[:10])

class_mapping = {
    'NORM': 0,
    'MI': 1,
    'STTC': 2,
    'CD': 3,
    'HYP': 4
}

y_train_processed = np.zeros((len(y_train), 5))
for i in range(len(y_train)):
    for j in y_train[i]:
        y_train_processed[i, class_mapping[j]] = 1

y_test_processed = np.zeros((len(y_test), 5))
for i in range(len(y_test)):
    for j in y_test[i]:
        y_test_processed[i, class_mapping[j]] = 1

print(y_test_processed[:10, :])

from sklearn.utils.class_weight import compute_class_weight

# Calculate class weights for each class separately
class_weights = np.array([None]*5)
num_classes = 5

for i in range(num_classes):
    class_labels = y_train_processed[:, i]
    cw = compute_class_weight('balanced', classes=[0, 1], y=class_labels)
    class_weights_dict = np.array([cw[0], cw[1]])
    class_weights[i] = class_weights_dict

print(class_weights)

def weightedLoss(y_true, y_pred):
    epsilon = K.epsilon()
    y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)

    loss = 0
    for i in range(num_classes):
        loss -= (class_weights[i][1] * y_true[i] * K.log(y_pred[i] + epsilon)) + \
                (class_weights[i][0] * (1 - y_true[i]) * K.log(1 - y_pred[i] + epsilon))

    return loss

class FocalLoss(tf.keras.losses.Loss):
    def __init__(self, alpha=None, gamma=2.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    def call(self, y_true, y_pred):
        epsilon = K.epsilon()
        y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)

        loss = 0
        for i in range(num_classes):
            loss -= (self.alpha[i][1] * y_true[i] * K.pow(1 - y_pred[i], self.gamma) * K.log(y_pred[i] + epsilon)) + \
                    ((self.alpha[i][0]) * (1 - y_true[i]) * K.pow(y_pred[i], self.gamma) * K.log(1 - y_pred[i] + epsilon))

        return loss

"""#### Train Model"""

early    = callbacks.EarlyStopping(monitor="val_loss", patience=6, restore_best_weights=True)
reducelr = callbacks.ReduceLROnPlateau(monitor="val_loss", patience=3)
callback = [early, reducelr]

model.compile(optimizer = optimizers.Adam(learning_rate=0.0005),
              loss = FocalLoss(alpha=class_weights),
              metrics = [metrics.BinaryAccuracy(), metrics.AUC(curve='ROC', multi_label=True)])

history = model.fit(x_train, y_train_processed, validation_split=0.12, epochs=40, batch_size=64, callbacks=callback)

import matplotlib.pyplot as plt

# Plot the loss versus epoch for both training and validation
plt.figure(figsize=(10, 5))

# Plot training loss
plt.plot(history.history['loss'], label='Training Loss', color='blue')
# Plot validation loss
plt.plot(history.history['val_loss'], label='Validation Loss', color='red')

plt.title('Loss vs. Epoch')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

plt.show()

"""##### Save Model"""

# save_path = '../../models/'
# model.save(save_path + "ST-CNN-GAP-5-B32.h5")

"""Evaluate the model"""

from sklearn.metrics import precision_recall_curve, f1_score, roc_auc_score, accuracy_score, auc


def sklearn_metrics(y_true, y_pred):
    y_bin = np.copy(y_pred)
    y_bin[y_bin >= 0.6] = 1
    y_bin[y_bin < 0.6]  = 0

    # Compute area under precision-Recall curve
    auc_sum = 0
    for i in range(5):
      precision, recall, thresholds = precision_recall_curve(y_true[:, i], y_pred[:,i])
      auc_sum += auc(recall, precision)

    print("Accuracy        : {:.2f}".format(accuracy_score(y_true.flatten(), y_bin.flatten())* 100))
    print("Macro AUC score : {:.2f}".format(roc_auc_score(y_true, y_pred, average='macro') * 100))
    print('AUPRC           : {:.2f}'.format((auc_sum / 5) * 100))
    print("Micro F1 score  : {:.2f}".format(f1_score(y_true, y_bin, average='micro') * 100))

y_pred_train = model.predict(x_train)
y_pred_test  = model.predict(x_test)

print("Train")
sklearn_metrics(y_train_processed, y_pred_train)
print("\nTest")
sklearn_metrics(y_test_processed, y_pred_test)

print(y_pred_test[:5, :])

y_pred_test[y_pred_test >= 0.6] = 1
y_pred_test[y_pred_test < 0.6] = 0

print(y_pred_test[:5, :])

from sklearn.metrics import multilabel_confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

class_labels = ['NORM', 'MI', 'STTC', 'CD', 'HYP']

multilabel_cm = multilabel_confusion_matrix(y_test_processed, y_pred_test)

# for i, label in enumerate(class_labels):
#     print(f"Confusion Matrix for {label}:")
#     print(multilabel_cm[i])
#     print()
plt.figure(figsize=(15, 10))
for i, label in enumerate(class_labels):
    plt.subplot(2, 3, i + 1)  # 2 rows, 3 columns layout
    sns.heatmap(multilabel_cm[i], annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix for {label}')

plt.tight_layout()
plt.show()

print("Multilabel Classification Report:")
print(classification_report(y_test_processed, y_pred_test, target_names=class_labels))
