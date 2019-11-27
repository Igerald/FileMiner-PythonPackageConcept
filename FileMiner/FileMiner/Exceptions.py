############## Module for Specific Error Handling #####################

class SequenceError(Exception):
    
    def __init__(self, expression, message=""):
        self.expression = expression
        self.message = message

class InvalidError(Exception):
    
    def __init__(self, expression, message=""):
        self.expression = expression
        self.message = message

class InvalidInputError(Exception):
    
    def __init__(self, expression, message=""):
        self.expression = expression
        self.message = message                                     

class EmptySetError(Exception):

    def __init__(self, expression, message=""):
        self.expression = expression
        self.message = message
    
class Err(Exception):

    def __init__(self, expression, message=""):
        self.expression = expression
        self.message = message

    def __store__(self):
        pass

    def Log(self):
        pass
