import numpy as np


from vesper.tests.test_case import TestCase
import vesper.util.numpy_utils as numpy_utils


class NumPyUtilsTests(TestCase):
    
    
    def test_find(self):
        
        y = [2, 0, 1, 0, 1, 0, 2]
        
        cases = [
            
            # x in y
            ([0], y, [1, 3, 5]),
            ([2], y, [0, 6]),
            ([0, 1], y, [1, 3]),
            ([1, 0], y, [2, 4]),
            ([0, 1, 0], y, [1, 3]),
            ([1, 0, 1], y, [2]),
            ([1, 0, 1, 0], y, [2]),
            
            # x not in y
            ([3], y, []),
            ([0, 3], y, []),
            ([2, 3], y, []),
            ([2, 3, 4], y, [])
            
        ]
        
        for x, y, expected in cases:
            x = np.array(x)
            y = np.array(y)
            expected = np.array(expected)
            result = numpy_utils.find(x, y)
            self._assert_arrays_equal(result, expected)


    def test_tolerant_find(self):
        
        y = [4, 0, 2, 0, 2, 0, 4]
        
        cases = [
            
            # x in y
            ([0], y, [1, 3, 5]),
            ([0, 2], y, [1, 3]),
            ([1], y, [1, 2, 3, 4, 5]),
            ([0, 1], y, [1, 3]),
            ([1, 1], y, [1, 2, 3, 4]),
            ([5, 1], y, [0]),
            ([1, 5], y, [5]),
            
            # x not in y
            ([6], y, []),
            ([4, 2], y, [])
            
        ]
        
        for x, y, expected in cases:
            x = np.array(x)
            y = np.array(y)
            expected = np.array(expected)
            result = numpy_utils.find(x, y, tolerance=1)
            self._assert_arrays_equal(result, expected)
