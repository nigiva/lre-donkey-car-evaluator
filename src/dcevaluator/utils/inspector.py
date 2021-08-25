import inspect
from IPython.core.magics.code import extract_symbols
import sys

import os
import numpy as np
import pandas as pd
from PIL import Image
import base64
from io import BytesIO
import tensorflow as tf
from tensorflow import keras
from loguru import logger
import shutil

"""
CC BY-SA 4.0
Inspired by Evann Courdier and Nikita Kitaev
https://stackoverflow.com/a/65806216
"""

def get_file_from_object(object, old_get_file=inspect.getfile):
    """
    Get __file__ from an object
    Specially when it is not defined in using Jupyter notebook

    :param object: the object
    :param old_get_file: the old get_file function used by `inspect` lib
    """
    if not inspect.isclass(object):
        return old_get_file(object)
    
    # Lookup by parent module (as in current inspect)
    if hasattr(object, '__module__'):
        object_ = sys.modules.get(object.__module__)
        if hasattr(object_, '__file__'):
            return object_.__file__
    
    # If parent module is __main__, lookup by methods (NEW)
    for name, member in inspect.getmembers(object):
        if inspect.isfunction(member) and object.__qualname__ + '.' + member.__name__ == member.__qualname__:
            return inspect.getfile(member)
    else:
        raise TypeError('Source for {!r} not found'.format(object))

inspect.getfile = get_file_from_object

def save_source(source_class, path):
  """
  Save the source code of a class

  :param source_class: class to save
  :param path: filepath where the code will be saved
  """
  cell_code = "".join(inspect.linecache.getlines(get_file_from_object(source_class)))
  class_code = extract_symbols(cell_code, source_class.__name__)[0][0]
  with open(path, "w") as f:
    f.write(class_code)

def load_source(path, class_name_to_load="DCModel"):
  """
  Load the source code stored in a file
  :param path: the code filepath
  :param class_name_to_load: the name of the class to load (and return)
  :return: the class entity of `class_name_to_load` loaded
  """
  g = dict(locals(), **globals())
  with open(path, "r") as f:
      exec(f.read(), g, g)
  return g[class_name_to_load]
