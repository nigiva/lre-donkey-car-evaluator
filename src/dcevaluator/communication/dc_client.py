from loguru import logger
from dcevaluator.communication.basic_client import BasicClient
import json
import re

class DonkeyCarClient(BasicClient):

    @staticmethod
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

    def on_request_receive(self, request_string):
        super().on_request_receive(request_string)
        request = json.loads(self.replace_float_notation(request_string))
        if "msg_type" in request and request["msg_type"] != "telemetry":
            logger.info(request_string)
    
    def send_get_protocol_version_request(self):
        request = dict()
        request["msg_type"] = "get_protocol_version"
        self.send_message(json.dumps(request))