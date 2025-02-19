# coding=utf-8
import ee
from . import utils
from ..utils import makeName
from .. import tools


def toDrive(collection, folder, namePattern='{id}', scale=30,
            dataType="float", region=None, datePattern=None, **kwargs):
    """ Upload all images from one collection to Google Drive. You can use
    the same arguments as the original function
    ee.batch.export.image.toDrive

    :param collection: Collection to upload
    :type collection: ee.ImageCollection
    :param folder: Google Drive folder to export the images to
    :type folder: str
    :param namePattern: pattern for the name. See make_name function
    :type namePattern: str
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
        (Landsat resolution)
    :type scale: int
    :param maxImgs: maximum number of images inside the collection
    :type maxImgs: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :param datePattern: pattern for date if specified in namePattern.
        Defaults to 'yyyyMMdd'
    :type datePattern: str
    :return: list of tasks
    :rtype: list
    """
    # empty tasks list
    tasklist = []
    # get region
    region = tools.geometry.getRegion(region)
    # Make a list of images
    img_list = collection.toList(collection.size())

    n = 0
    while True:
        try:
            img = ee.Image(img_list.get(n))

            name = makeName(img, namePattern, datePattern)

            # convert data type
            img = utils.convertDataType(dataType)(img)

            task = ee.batch.Export.image.toDrive(image=img,
                                                 description=name,
                                                 folder=folder,
                                                 fileNamePrefix=name,
                                                 region=region,
                                                 scale=scale, **kwargs)
            task.start()
            tasklist.append(task)
            n += 1
        except Exception as e:
            error = str(e).split(':')
            if error[0] == 'List.get':
                break
            else:
                raise e


def toAsset(col, assetPath, scale=30, region=None, create=True,
            verbose=False, **kwargs):
    """ Upload all images from one collection to a Earth Engine Asset.
    You can use the same arguments as the original function
    ee.batch.export.image.toDrive

    :param col: Collection to upload
    :type col: ee.ImageCollection
    :param assetPath: path of the asset where images will go
    :type assetPath: str
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
        (Landsat resolution)
    :type scale: int
    :param maxImgs: maximum number of images inside the collection
    :type maxImgs: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :return: list of tasks
    :rtype: list
    """
    size = col.size().getInfo()
    alist = col.toList(size)
    tasklist = []

    if create:
        utils.createAssets([assetPath], 'ImageCollection', True)

    if region is None:
        first_img = ee.Image(alist.get(0))
        region = tools.geometry.getRegion(first_img)
    else:
        region = tools.geometry.getRegion(region)

    for idx in range(0, size):
        img = alist.get(idx)
        img = ee.Image(img)
        name = img.id().getInfo().split("/")[-1]

        assetId = assetPath+"/"+name

        task = ee.batch.Export.image.toAsset(image=img,
                                             assetId=assetId,
                                             description=name,
                                             region=region,
                                             scale=scale, **kwargs)
        task.start()

        if verbose:
            print('Exporting {} to {}'.format(name, assetId))

        tasklist.append(task)

    return tasklist