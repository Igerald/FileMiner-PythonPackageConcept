######################## Package Specific Functions ###########################

# Imports #

from datetime import datetime

def Vali_Date(string_Date):
    try:
            datetime.strptime(string_Date, '%m-%d-%Y')
            return True
    except ValueError:
            return False

class PyUtilities(object):
    
    def __init__(self):
        pass

