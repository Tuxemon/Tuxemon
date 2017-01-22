
from random import random
import numpy as np

class ClassificationData(object):
    """Handles random sampling from the data set to be used for prediction
    moves

    """

    @staticmethod
    def sample(proportion):
        # TODO: Test set?
        if proportion > 1.0:
            totalSamples = 2844828.
            count = float(proportion)
            proportion = (count/totalSamples) * 20
            print('selecting ' + str(count) + ' samples. Proportion is ' + str(proportion))
        else:
            proportion = proportion * 20

        #filename = 'resources/data/pam' + str(int(random() * 20)) + '.dat'
        filename = 'resources/data/pam10.dat'
        print('sampling from ' + filename)
        lines = [line for line in open(filename) if random() <= proportion]
        x = []
        y = []

        for line in lines:
            elements = line.split(' ')
            y.append(float(elements.pop(1)))
            x.append([float(element) for element in elements])

        print('selected ' + str(len(x)) + ' samples')
        print('number of features: ' + str(len(x[0])))

        x = np.array(x)
        return x, y
