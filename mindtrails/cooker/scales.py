# meta class for scales
class Scale:
    def _init_(self,dataset):
        self.dataset = dataset
    def score(self):
        raise NotImplementedError("Subclass must implement abstract method")

class OA(Scale):
    def score(self):

        return dataset
