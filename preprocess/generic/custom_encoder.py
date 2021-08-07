import json
import numpy as np
import pandas as pd
from pandas_profiling.model.base import Variable
from pandas_profiling.model.messages import Message, MessageType

class CustomEncoder(json.JSONEncoder):
    '''
    Convert some Numpy and Pandas objects to serializable equivalents.
    '''
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        
        if isinstance(obj, np.floating):
            return float(obj)

        if isinstance(obj, np.bool_):
            return bool(obj)

        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, pd.Series) or isinstance(obj, pd.DataFrame):
            return obj.to_dict()

        if isinstance(obj, Variable):
            return obj.value

        if isinstance(obj, MessageType):
            return obj.name

        if isinstance(obj, Message):
            return {"type": obj.message_type, "column": obj.column_name}

        else:
            return super(CustomEncoder).default(obj)