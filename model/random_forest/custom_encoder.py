import json
import numpy as np
import pandas as pd

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

        else:
            return super(CustomEncoder).default(obj)