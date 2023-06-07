import unittest
import scipy.ndimage.morphology as morphology

from main import *

# Import the functions you want to test


class TestCode(unittest.TestCase):
    def test_generate_array(self):
        # Test the generate_array function
        # Create expected output
        lat_size = abs(int((LAT_LON_BOUNDS[1][0] - LAT_LON_BOUNDS[0][0]) / PIXEL_SIZE_DEG_LAT))
        lon_size = abs(int((LAT_LON_BOUNDS[1][1] - LAT_LON_BOUNDS[0][1]) / PIXEL_SIZE_DEG_LON))
        expected_output = np.zeros([lat_size, lon_size, 2])

        # Call the function and compare the output
        output = generate_array()
        self.assertEqual(output.shape, expected_output.shape)
        self.assertTrue(np.allclose(output, expected_output))

    def test_fill_array(self):
        # Test the fill_array function
        arr = np.zeros([10, 10, 2])
        lat = LAT_LON_BOUNDS[0][0] + PIXEL_SIZE_DEG_LAT
        lon = LAT_LON_BOUNDS[0][1] + PIXEL_SIZE_DEG_LON
        sound = 1.0

        # Call the function
        fill_array(arr, lat, lon, sound)

        # Check if the array was filled correctly
        lat_offset_px = int((lat - LAT_LON_BOUNDS[0][0]) / PIXEL_SIZE_DEG_LAT)
        lon_offset_px = int((lon - LAT_LON_BOUNDS[0][1]) / PIXEL_SIZE_DEG_LON)
        expected_output = np.zeros([10, 10, 2])
        expected_output[lat_offset_px, lon_offset_px, 0] = sound
        expected_output[lat_offset_px, lon_offset_px, 1] = 1
        self.assertTrue(np.allclose(arr, expected_output))

    def test_generate_image_from_array(self):
        # Test the generate_image_from_array function
        arr = np.zeros([10, 10, 2])
        arr[5, 5, 0] = 10.0
        arr[5, 5, 1] = 1

        # Call the function
        generate_image_from_array(arr)

        # Check if the image was generated correctly
        expected_output = np.zeros([10, 10, 2])
        expected_output[5, 5, 0] = 1.0
        expected_output[5, 5, 1] = 1.0
        expected_output[..., 0] = morphology.grey_dilation(expected_output[..., 0], size=(3, 3))
        expected_output[..., 1] = morphology.grey_dilation(expected_output[..., 1], size=(3, 3),
                                                            structure=[[0.25, 0.5, 0.25],
                                                                       [0.5, 0.5, 0.5],
                                                                       [0.25, 0.5, 0.25]]) - 0.5
        expected_output[..., 0][expected_output[..., 0] > MAX_NOISE_RANGE] = MAX_NOISE_RANGE
        expected_output[..., 0] -= np.min(expected_output[..., 0])
        expected_output[..., 0] /= np.max(expected_output[..., 0])

        self.assertTrue(np.allclose(arr, expected_output))

    def test_measurements_list_to_field_value(self):
        # Test the measurements_list_to_field_value function
        measurements = [
            {"lat": 1, "lon": 2, "sound": 3},
            {"lat": 4, "lon": 5, "sound": 6},
            {"lat": 7, "lon": 8, "sound": 9},
        ]
        field_key = "sound"
        expected_output = [3, 6, 9]

        # Call the function and compare the output
        output = measurements_list_to_field_value(measurements, field_key)
        self.assertEqual(output, expected_output)

    # Add more test methods for the remaining functions


if __name__ == '__main__':
    unittest.main()