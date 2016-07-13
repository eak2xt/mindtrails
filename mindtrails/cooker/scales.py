# meta class for scales
# Scales should have three component:
# 1\ name = name of the scale
# 2\ state = raw, scored, transformed
# 3\ dataset = the original dataset of the scale
# 4\ score function = if the target dataset is raw, scored it and return another scale object.
# 5\ trans function = if the target dataset is scored, transform it and return another scale object.

class Scale:
    def _init_(self,dataset):
        self.dataset = dataset
    def score(self):
        raise NotImplementedError("Subclass must implement abstract method")

class OA(Scale):
    def score(self):

        return dataset
