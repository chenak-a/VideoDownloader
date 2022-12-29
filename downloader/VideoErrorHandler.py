class VideoErrorhandler(Exception):
    
    def __init__(self, message: str="",reset : bool = False):                        
        self.message = message
        self.reset = reset
    