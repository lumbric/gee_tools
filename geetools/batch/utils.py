# coding=utf-8
import ee
import os

GEOMETRY_TYPES = {
    'LineString': ee.geometry.Geometry.LineString,
    'LineRing': ee.geometry.Geometry.LinearRing,
    'MultiLineString': ee.geometry.Geometry.MultiLineString,
    'MultiPolygon': ee.geometry.Geometry.MultiPolygon,
    'MultiPoint': ee.geometry.Geometry.MultiPoint,
    'Point': ee.geometry.Geometry.Point,
    'Polygon': ee.geometry.Geometry.Polygon,
    'Rectangle': ee.geometry.Geometry.Rectangle,
    'GeometryCollection': ee.geometry.Geometry,
}


def getProjection(filename):
    """ Get EPSG from a shapefile using OGR

    :param filename: an ESRI shapefile (.shp)
    :type filename: str
    """
    try:
        from osgeo import ogr
    except:
        import ogr

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(filename)

    # from Layer
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()

    return spatialRef.GetAttrValue("AUTHORITY", 1)


def kmlToGeoJsonDict(kmlfile=None, data=None, encoding=None):
    """ Convert a KML file to a GeoJSON dict """
    import xml.dom.minidom as md
    from fastkml import kml
    import kml2geojson

    k = kml.KML()

    with open(kmlfile) as thefile:
        kmlf = thefile.read()

    # Handle encoding
    if not encoding:
        try:
            import re
            match = re.search('encoding=".+"', kmlf).group()
            encoding = match.split('=')[1][1:-1]
        except:
            encoding = 'utf-8'

    kmlf = kmlf.encode(encoding)
    k.from_string(kmlf)
    kmlStr = k.to_string()

    # force encoding
    kmlStr = kmlStr.encode(encoding, errors="ignore").decode()
    root = md.parseString(kmlStr)
    layers = kml2geojson.build_feature_collection(root)
    return layers


def isPoint(pointlist):
    """ Verify is a list is a list of points """
    if len(pointlist) in [2, 3]:
        if isinstance(pointlist[0], (int, float))\
                and isinstance(pointlist[1], (int, float)):
            return True
        else:
            return False
    else:
        return False


def removeZ(pointlist):
    """ Remove Z value of points if needed """
    for p in pointlist:
        if isPoint(p):
            if len(p) == 3:
                p.pop(2)
        else:
            removeZ(p)


def recrusiveDeleteAsset(assetId):
    info = ee.data.getInfo(assetId)
    if info:
        ty = info['type']
        if ty in ['Image', 'FeatureCollection']:
            # setting content to 0 will delete the assetId
            content = 0
        elif ty in ['Folder', 'ImageCollection']:
            try:
                content = ee.data.getList({'id':assetId})
            except Exception as e:
                print(str(e))
                return
        else:
            print("Can't handle {} type yet".format(ty))

        if content == 0:
            # delete empty colletion and/or folder
            ee.data.deleteAsset(assetId)
        else:
            for asset in content:
                path = asset['id']
                ty = asset['type']
                if ty == 'Image':
                    # print('deleting {}'.format(path))
                    ee.data.deleteAsset(path)
                else:
                    recrusiveDeleteAsset(path)
            # delete empty collection and/or folder
            ee.data.deleteAsset(assetId)
    else:
        print('{} does not exists or there is another problem'.format(assetId))


def convertDataType(newtype):
    """ Convert an image to the specified data type

    :param newtype: the data type. One of 'float', 'int', 'byte', 'double',
        'Uint8','int8','Uint16', 'int16', 'Uint32','int32'
    :type newtype: str
    :return: a function to map over a collection
    :rtype: function
    """
    def wrap(image):
        TYPES = {'float': image.toFloat,
                 'int': image.toInt,
                 'byte': image.toByte,
                 'double': image.toDouble,
                 'Uint8': image.toUint8,
                 'int8': image.toInt8,
                 'Uint16': image.toUint16,
                 'int16': image.toInt16,
                 'Uint32': image.toUint32,
                 'int32': image.toInt32}
        return TYPES[newtype]()
    return wrap


def createAssets(asset_ids, asset_type, mk_parents):
    """Creates the specified assets if they do not exist.
    This is a fork of the original function in 'ee.data' module with the
    difference that

    - If the asset already exists but the type is different that the one we
      want, raise an error
    - Starts the creation of folders since 'user/username/'

    Will be here until I can pull requests to the original repo

    :param asset_ids: list of paths
    :type asset_ids: list
    :param asset_type: the type of the assets. Options: "ImageCollection" or
        "Folder"
    :type asset_type: str
    :param mk_parents: make the parents?
    :type mk_parents: bool
    :return: A description of the saved asset, including a generated ID

    """
    for asset_id in asset_ids:
        already = ee.data.getInfo(asset_id)
        if already:
            ty = already['type']
            if ty != asset_type:
                raise ValueError("{} is a {}. Can't create asset".format(asset_id, ty))
            print('Asset %s already exists' % asset_id)
            continue
        if mk_parents:
            parts = asset_id.split('/')
            root = "/".join(parts[:2])
            root += "/"
            for part in parts[2:-1]:
                root += part
                if ee.data.getInfo(root) is None:
                    ee.data.createAsset({'type': 'Folder'}, root)
                root += '/'
        return ee.data.createAsset({'type': asset_type}, asset_id)


def downloadFile(url, name, extension, path=None):
    """ Download a file from a given url

    :param url: full url
    :type url: str
    :param name: name for the file (can contain a path)
    :type name: str
    :param extension: extension for the file
    :type extension: str
    :return: the created file (closed)
    :rtype: file
    """
    import requests
    response = requests.get(url, stream=True)
    code = response.status_code

    if path is None:
        path = os.getcwd()

    pathname = os.path.join(path, name)

    while code != 200:
        if code == 400:
            return None
        response = requests.get(url, stream=True)
        code = response.status_code
        size = response.headers.get('content-length',0)
        if size: print('size:', size)

    with open('{}.{}'.format(pathname, extension), "wb") as handle:
        for data in response.iter_content():
            handle.write(data)

    return handle
