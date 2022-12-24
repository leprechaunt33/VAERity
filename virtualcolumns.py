import math
import numpy as np
from datetime import datetime
from helperfunc import MAX_AGE, AGE_BINS

def parse_datetime(strtime):
    if strtime is None:
        return np.datetime64('NaT')
    else:
        try:
            dt64 = datetime.strptime(str(strtime), "%m/%d/%Y")
            dt64 = datetime(dt64.year, dt64.month, 1)
            return np.datetime64(dt64)
        except:
            print(f"{strtime} unable to be converted, returning NaT")
            return np.datetime64('NaT')

def year_datetime(strtime):
    if strtime is None:
        return np.datetime64('NaT')
    else:
        try:
            dt64 = datetime.strptime(str(strtime), "%m/%d/%Y")
            dt64 = datetime(dt64.year, 1, 1)
            return np.datetime64(dt64)
        except:
            print(f"{strtime} unable to be converted, returning NaT")
            return np.datetime64('NaT')

def age_bin(age):
    global AGE_BINS
    if age is None:
        return -1
    if math.isnan(age):
        return -1
    else:
        return (int(age/AGE_BINS)+1)*AGE_BINS
