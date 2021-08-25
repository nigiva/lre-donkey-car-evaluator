import os
from loguru import logger
from dcevaluator.utils.inspector import load_source
from dcevaluator.utils.utils import build_log_tag

class DCModelWrapper:
    def input_transformer(self, request):
        raise Exception("Unimplemented function !")

    def input_preprocessing(self, inputs_tensor, num_parallel_calls=1):
        raise Exception("Unimplemented function !")

    def predict(self, request):
        raise Exception("Unimplemented function !")

    def output_transformer(self, output):
        raise Exception("Unimplemented function !")

    def save(self, path):
        raise Exception("Unimplemented function !")

    def compile_model(self):
        raise Exception("Unimplemented function !")

    def load_model(self, model_path):
        raise Exception("Unimplemented function !")

    @staticmethod
    def load(path, wrapper_filename="wrapper.code"):
        logger.info(build_log_tag("LOAD WRAPPER AND MODEL", path=path))
        wrapper_path = os.path.join(path, wrapper_filename)
        LoadedBrain = load_source(wrapper_path, class_name_to_load="Brain")
        loaded_brain_instance = LoadedBrain()
        loaded_brain_instance.load_model(LoadedBrain.get_model_path(path))
        loaded_brain_instance.load_wrapper_code_path = path
        return loaded_brain_instance