import sys
import scipy.signal
import numpy as np

sys.path.append("..")
import main
import matplotlib.pyplot as plt
import folium


def test_generate_image_from_array():
    import pdb;
    pdb.set_trace()
    noise_sample_coords = [41.405039, 2.147645]
    noise_value = 2
    arr = main.generate_array()
    lat = main.LAT_LON_BOUNDS[0][0]
    coin = False
    while True:
        lon = main.LAT_LON_BOUNDS[0][1]
        while True:
            if coin:
                # try:
                #     main.fill_array(arr, lat, lon, 1)
                # except Exception as err:
                #     import pdb; pdb.set_trace()
                coin = False
            else:
                coin = True
            lon += main.PIXEL_SIZE_DEG_LON
            if lon >= main.LAT_LON_BOUNDS[1][1]:
                break
        lat += main.PIXEL_SIZE_DEG_LAT
        if lat >= main.LAT_LON_BOUNDS[1][0]:
            break

    # main.get_offset_px(arr,
    #                    main.LAT_LON_BOUNDS[0][0] - main.PIXEL_SIZE_DEG_LAT,
    #                    main.LAT_LON_BOUNDS[0][1] - main.PIXEL_SIZE_DEG_LON)

    main.fill_array(arr, noise_sample_coords[0], noise_sample_coords[1], noise_value)
    main.fill_array(arr,
                    main.LAT_LON_BOUNDS[1][0] - main.PIXEL_SIZE_DEG_LAT,
                    main.LAT_LON_BOUNDS[1][1] - main.PIXEL_SIZE_DEG_LON,
                    noise_value)
    # main.fill_array(arr,
    #                 main.LAT_LON_BOUNDS[0][0],
    #                 main.LAT_LON_BOUNDS[0][1],
    #                 noise_value)
    # main.fill_array(arr,
    #                 main.LAT_LON_BOUNDS[1][0] - main.PIXEL_SIZE_DEG_LAT,
    #                 main.LAT_LON_BOUNDS[1][1] - main.PIXEL_SIZE_DEG_LON,
    #                 5)
    import pdb;
    pdb.set_trace()
    main.generate_image_from_array(arr)
    import numpy as np
    new_arr = np.rollaxis(np.array([arr[..., 0], arr[..., 0], arr[..., 0], arr[..., 1]]), 0, 3)
    import pdb;
    pdb.set_trace()
    img = folium.raster_layers.ImageOverlay(
        name="",
        # image="/home/toni/Pictures/Lenna_test_image.png",
        image=new_arr,
        mercator_project=True,
        bounds=main.LAT_LON_BOUNDS,
        # origin="upper",
        origin="lower",
        # opacity=1,
        # opacity=0.6,
        # interactive=True,
        # cross_origin=False,
        colormap=plt.cm.get_cmap("jet"),
        zindex=1,
    )
    m = folium.Map(location=[noise_sample_coords[0], noise_sample_coords[1]], zoom_start=main.ZOOM_LEVEL_START)
    img.add_to(m)
    folium.Marker(noise_sample_coords).add_to(m)
    folium.Marker(main.LAT_LON_BOUNDS[0]).add_to(m)
    folium.Marker(main.LAT_LON_BOUNDS[1]).add_to(m)
    m.save("index.html")


def test_dilations():
    arr = np.zeros([10, 10])
    arr[5, 5] = 1

    filter_kernel = [[0, 0.5, 0],
                     [0.5, 0.5, 0.5],
                     [0, 0.5, 0]]
    arr_new = scipy.ndimage.morphology.grey_dilation(arr, size=(3, 3) , structure=filter_kernel) - 0.5
    import matplotlib.pyplot as plt
    plt.figure()
    plt.subplot(121)
    plt.imshow(arr)
    plt.subplot(122)
    plt.imshow(arr_new)
    plt.show()


if __name__ == "__main__":
    # test_generate_image_from_array()
    test_dilations()
