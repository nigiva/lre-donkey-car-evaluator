import pandas as pd
import re
from tqdm import tqdm

class LogParser:
    def __init__(self, log_path):
        """
        Log Parser

        :param log_path: the path of log
        """
        # Regex
        self.log_line_regex = r"^[^|\n]+\| *[A-Z]+ *\|[^|]+$"
        self.arg_regex = r"\[([^\[=\"'\]]+)\]"
        self.kwarg_regex = r"\[([^\[=\"'\]]+)=\"([^\"]*)\"\]"

        self.data = self.load(log_path)
    
    def load(self, log_path):
        """
        Load log file
        
        Store the result in `data` attribute

        :param log_path: the path of log
        :return: DataFrame containing the lines of log file
        """
        rows = []
        columns = ["datetime", "level", "position", "args", "kwargs"]
        with open(log_path, "r") as f:
            for line in tqdm(f):
                # Check if this line is a log line or not
                if re.match(self.log_line_regex, line):
                    # Split "DATE | LEVEL | FILE:FUNC:LINE - MESSAGE" with "|" separator
                    splited_line = line.split("|")

                    # We remove space and `\n` before and after the string in each cell
                    cleaned_splited_line = [s.strip() for s in splited_line]

                    # Split "FILE:FUNC:LINE - MESSAGE" with " - " separator
                    position_and_message = cleaned_splited_line.pop(2)
                    # So, we have : `[ "DATE", "LEVEL" ]`
                    
                    position, message = position_and_message.split(" - ")

                    # Append `position` into `cleaned_splited_line`
                    # To get this : `[ "DATE", "LEVEL", "FILE:FUNC:LINE" ]`
                    cleaned_splited_line.append(position)

                    # Parse args : "[TAG1][TAG2]" ==> `[ "TAG1", "TAG2" ]`
                    args = re.findall(self.arg_regex, message)
                    cleaned_splited_line.append(args)

                    # Parse kwargs : '[NAME1="VAL1"][NAME2="VAL2"]' ==> `{ NAME1 :"VAL1", NAME2 :"VAL2" }`
                    kwarg = dict()
                    for match in re.finditer(self.kwarg_regex, message, re.S):
                        kwarg[match.group(1)] = match.group(2)
                    cleaned_splited_line.append(kwarg)

                    rows.append(cleaned_splited_line)
        self.data = pd.DataFrame(rows, columns = columns)
        return self.data
    
    def find_evaluator_line(self):
        """
        Find begin/end lines of the evaluator

        :return: DataFrame containing the lines
        """
        return self.data[self.data.apply(lambda r: "Donkey Car Evaluator" in r.args, axis = 1)]