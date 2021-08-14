import numpy as np
import tensorflow as tf
from tensorflow import keras
import os
from dcevaluator.controller.saver import ModelSaver
import shutil

class Brain:
    def __init__(self, model_path):
        self.model = None
        self.model_path = model_path
        self.load(model_path)
    
    def load(self, model_path, lr = 0.001):
        """
        Load a model from model_path
        :param model_path: directory path
        """
        # self.model = keras.models.load_model(model_path)
        self.model_path = model_path
        DCModel = ModelSaver.load(os.path.join(model_path, "model.code"))
        self.model = DCModel()
        self.model.load_weights(os.path.join(model_path, "weights.data"))
        optimizer = keras.optimizers.Adam(learning_rate=lr)
        self.model.compile(optimizer=optimizer,loss=keras.losses.MSE, metrics=["mse"])

    def save(self, model_path):
        """
        Save the brain like a SaveModel, weights.data and model.code
        :param path: directory path where we want save (directory already created)
        """
        if self.model_path is not None:
            shutil.copy(os.path.join(self.model_path, "model.code"), os.path.join(model_path, "model.code"))
        self.model.save_weights(os.path.join(model_path, "weights.data"))

    def predict(self, img, speed, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):#TODO Change to a better shape
        """
        Predict actions
        :return (angle, throttle, brake)
        """
        transformed_img, transformed_speed_accel_gyro = self.input_transformer(img, speed, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
        output = self.model.predict({'input' : transformed_img, 'speed_accel_gyro':transformed_speed_accel_gyro})#TODO Change to a better shape
        transformed_output = self.output_transformer(output)
        return transformed_output
    
    def input_transformer(self, img, speed, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):
        """
        Transform input before passing in arguments to predict/train function
        :return Tensor
        """
        img = np.array(img)
        img = np.array([img])
        img_tensor = tf.convert_to_tensor(img, dtype=tf.float32)
        img_tensor = (img_tensor/127.5) - 1
        speed_accel_gyro_tensor = tf.convert_to_tensor([[speed, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z]], dtype=tf.float32)#TODO Change to a better shape
        return img_tensor, speed_accel_gyro_tensor
    
    def output_transformer(self, output):
        """
        Transform output from predict function
        :return (angle, throttle, brake)
        """
        angle = output['angle'][0][0] #TODO Change to a better shape
        angle_satured = 0.4 if abs(angle) > 0.4 else abs(angle)
        throttle = 0.6 - angle_satured
        return (angle, throttle, 0)#TODO Change to a better shape
    