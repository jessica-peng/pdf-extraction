import datetime


class Token:
    def __init__(self):
        self.token = [{
                "name": "Basic symbol",
                "checked": False
            }, {
                "name": "Number",
                "checked": False
            }, {
                "name": "Duplicate characters",
                "checked": False
            }, {
                "name": "Limit pattern length",
                "checked": False
            }]

    def getTokenFormat(self):
        return self.token


class Schema:
    def __init__(self):
        self.schema = {
            "schema_id": "",
            "schema_name": "",
            "ignore_token": [],
            "minimum_support": 0,
            "pattern_list": [],
            "attributes": [],
            "dtd": "",
            "files_path": "",
            "update_time": datetime.datetime.utcnow()
        }

    def getCollectionFormat(self):
        return self.schema
