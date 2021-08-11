import inspect
import tensorflow as tf
from tensorflow import keras

class ModelSaver:
    """
        Save the model into a file ('model.code') as source code
    """
    def __init__(self, activate = True):
        """
            Initialize the saver
            :param activate: capture or not the source code of decorated functions
        """
        self.is_activated = activate
        self.s_init = None
        self.s_call = None
    
    def init(self, funct):
        """
            Capture the source code of the init function
            ---
            Use as a decoration
            Such as :
            ```
                MODEL_SAVER = ModelSaver(True)
                ...
                @MODEL_SAVER.init
                def __init__(self, name = ""):
                    ...
            ```
        """
        def funct_with_params(*args, **kwargs):
            return funct(*args, **kwargs)
        if self.is_activated:
            self.s_init = inspect.getsource(funct)
        return funct_with_params

    def call(self, funct):
        """
            Capture the source code of the init function
            ---
            Use as a decoration
            Such as :
            ```
                MODEL_SAVER = ModelSaver(True)
                ...
                @MODEL_SAVER.call
                def call(self):
                    ...
            ```
        """
        def funct_with_params(*args, **kwargs):
            return funct(*args, **kwargs)
        if self.is_activated:
            self.s_call = inspect.getsource(funct)
        return funct_with_params

    def save(self, path):
        """
            Save the source code of the model as a file
            :param path: file path
        """
        if self.s_init is not None and self.s_call is not None:
            with open(path, "w") as s:
                s.write("class DCModel(keras.Model):\n")
                s.write("  MODEL_SAVER = ModelSaver(False)\n")
                s.write(self.s_init)
                s.write(self.s_call)
        else:
            raise Exception("init or call function are not saved")

    @staticmethod        
    def load(path):
        """
            Load the Model source code
            :param path: file path
        """
        d = dict(locals(), **globals())
        with open(path, "r") as s:
            exec(s.read(), d, d)
        return d['DCModel']