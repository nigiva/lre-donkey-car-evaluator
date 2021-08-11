from threading import Thread
import re

def launch_func_in_thread(func):
    """
    Launch a function in a thread

    :param func: the function to launch
    :return: A function launching the `func` in the thread
    """
    def internal_func(*args, **kwargs):
        func_thread = Thread(target=func, args=args, kwargs=kwargs)
        func_thread.start()
    return internal_func

def build_log_tag(*args, **kwargs):
    """
    Generate a string as a tag to parse the logs more easily
    
    If you call `build_log_tag("arg1", "arg2", key1="value1", key2="value2")`
    This function generate this string in return :
    [arg1][arg2][key1="value1"][key2="value2"]
    """
    generated_string = ""
    for v in args:
        generated_string += "[" + str(v) + "]"
    
    for k,v in kwargs.items():
        generated_string += "[" + str(k) + "=" + "\"" + str(v) + "\"]"
    
    return generated_string

def replace_float_notation(string):
        """
        Replace unity float notation for languages like
        French or German that use comma instead of dot.
        This convert the json sent by Unity to a valid one.
        Ex: "test": 1,2, "key": 2 -> "test": 1.2, "key": 2

        :param string: (str) The incorrect json string
        :return: (str) Valid JSON string
        """
        regex_french_notation = r'"[a-zA-Z_]+":(?P<num>[0-9,E-]+),'
        regex_end = r'"[a-zA-Z_]+":(?P<num>[0-9,E-]+)}'

        for regex in [regex_french_notation, regex_end]:
            matches = re.finditer(regex, string, re.MULTILINE)

            for match in matches:
                num = match.group('num').replace(',', '.')
                string = string.replace(match.group('num'), num)
        return string