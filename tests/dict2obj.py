import json


class Dict2Obj:
    def __init__(self, json_data):
        self.convert(json_data)

    def convert(self, json_data):
        if not isinstance(json_data, dict):
            return
        for key in json_data:
            if not isinstance(json_data[key], dict):
                self.__dict__.update({key: json_data[key]})
            else:
                self.__dict__.update({key: Dict2Obj(json_data[key])})


class DictionaryUtility:
    """
    Utility methods for dealing with dictionaries.
    """
    @staticmethod
    def to_object(item):
        """
        Convert a dictionary to an object (recursive).
        """
        def convert(item):
            if isinstance(item, dict):
                return type('jo', (), {k: convert(v) for k, v in item.iteritems()})
            if isinstance(item, list):
                def yield_convert(item):
                    for index, value in enumerate(item):
                        yield convert(value)
                return list(yield_convert(item))
            else:
                return item

        return convert(item)

