"""
This script automates a number of common steps of terrain analysis in QGIS.

Outputs:
    -Mosaicked and resampled (as necessary) DEM, saved to outputs folder
        and displayed on map
    -Hillshade, saved to outputs folder and displayed on map using 
        cumulative count cut symbology (the grayscale color ramp is stretched 
        between the 2nd and 98th percentiles of the raster's values)
    -DEM converted to vertical units of feet, saved to outputs folder
    -Base and index contours (vector), saved to outputs folder and displayed on map
    -Slope as percent (raster), saved to outputs folder and displayed on map 
        using a classified color scheme
    -Classified slope (raster), saved to outputs folder
    -Vectorized classified slope, saved to outputs folder and displayed on map 
        using the same classified color scheme as the raster slope layer
    -Aspect (raster), saved to outputs folder and displayed on map using a 
        rainbow color gradient
    -Classified aspect (raster), saved to outputs folder
    -Vectorized classified aspect, saved to outputs folder and displayed on map
        using a classified color scheme matching the rainbow color gradient
        of the raster aspect layer
    -Filled DEM (used for drainage analysis), saved to outputs folder
    -Vector channel network (drainage), saved to outputs folder and displayed 
        on map using a classified color scheme based on Strahler order
    
Maja Cannavo, Rhumb Line Maps, July 2020

*********************************************************************************
BEFORE YOU RUN THE SCRIPT:

    1. Create a folder named "Script-Data" in the same directory (folder) 
        as your current QGIS project.
        
    2. Inside the "Script-Data" folder, create a folder named "DTM-RAW" ("DTM" means 
        "digital terrain model"), which must include all the DEMs you want to 
        use but nothing else. These DEMs should have vertical and horizontal
        units of meters. Make sure to copy the folder name exactly!
        
    3. Also inside the "Script-Data" folder, create a folder named "Script-Outputs".
        This folder will be the location for all files created by the script.
        Make sure to copy the folder name exactly!
    
    4. Specify which outputs you'd like the script to produce. For each output
        variable, "1" means "do produce" and "0" means "don't produce."
        (In some cases, if you indicate not to produce an output that is needed
        for further steps in the analysis, that output will still be produced
        and saved to the Script-Outputs folder but not added to the map.) 
        Then, if applicable, modify the following parameters:
    
        5. Specify the grain (in meters; must be a whole number) of your raw DEMs
            (the ones in the "DTM-RAW" folder).
        
        6. Specify the DEM grain (in meters; must be a whole number) that you'd 
            like your project to use. The script will resample your DEMs to this 
            grain before proceeding with further analysis.
        
        7. Specify the contour intervals (in feet) you'd like for your base (more
            detailed) and index (less detailed) contours.
        
        8. Specify the threshold (the minimum Strahler order a cell must have to be
            included in the channel network) you'd like to use for channel computation.
            The lower the number, the more detailed your channel network will be.
*********************************************************************************
"""
from os import listdir
from os.path import isfile, join

# *** STEP 4 ***
# *** specify which outputs you'd like the script to produce ***
# 1 = produce; 0 = do not produce

produce_hillshade = 1
produce_baseContours = 1
produce_indexContours = 1
produce_rasterSlope = 1
produce_vectorSlope = 1
produce_rasterAspect = 1
produce_vectorAspect = 1
produce_channels = 1

# *** STEP 5 ***
# *** specify the grain (in meters; must be a whole number) of your raw DEMs ***
DEM_grain = 1

# *** STEP 6 ***
# **** specify the DEM grain (in meters; whole #) that you'd like your project to use ***
desired_grain = 2

# *** STEP 7 ***
# *** specify your desired contour interval(s) (in feet) ***
baseContourInt = 2
indexContourInt = 10

# *** STEP 8 ***
# *** specify the channel threshold (min. Strahler order) you'd like to use for channel computation***
channel_threshold = 5

# make sure you're in the correct QGIS project, located in the correct project folder
# project_path will look for the filepath of the currently open project
project_path = QgsProject.instance().readPath("./")

# data folder--MUST be in the same directory as your current QGIS project
data_folder = 'Script-Data'

# raw DEM folder (should contain only the raw DEMs)--must end in "/"
DEM_folder = project_path + '/' + data_folder + '/DTM-RAW/'

# folder for outputs--must end in "/"
analysis_folder = project_path + '/' + data_folder + '/Script-Outputs/'

# list the DEM filenames, avoiding any invisible '.DS_Store' files
DEM_fns = [DEM_folder + f for f in listdir(DEM_folder) if \
    (isfile(join(DEM_folder, f)) and ('.DS_Store' not in f))]

# filepath to save mosaicked DEM
mDEM_fn = analysis_folder + 'dtm_Vm_' + str(DEM_grain) + 'm.sdat'

# filepath to save resampled mosaicked DEM
rmDEM_fn = analysis_folder + 'dtm_Vm_' + str(desired_grain) + 'm.sdat'

# filepath to save hillshade
hs_fn = analysis_folder + 'hillshade_' + str(desired_grain) + 'm.tif'

# filepath to save DEM converted to feet
ftDEM_fn = analysis_folder + 'dtm_Vft_' + str(desired_grain) + 'm.tif'

# filepaths to save slope, classified slope, and vectorized classified slope
s_fn = analysis_folder + 'slope.tif'
cs_fn = analysis_folder + 'classedSlope.tif'
vcs_fn = analysis_folder + 'vectorSlope.shp'

# filepaths to save aspect, classified aspect, and vectorized classified aspect
a_fn = analysis_folder + 'aspect.tif'
ca_fn = analysis_folder + 'classedAspect.tif'
vca_fn = analysis_folder + 'vectorAspect.shp'

# filepaths to save contour shapefiles
bc_fn = analysis_folder + str(baseContourInt) + 'ft.shp'
ic_fn = analysis_folder + str(indexContourInt) + 'ft.shp'

# filepath to save filled DEM
fDEM_fn = analysis_folder + 'filledDEM.sdat'

# filepath to save vectorized channels
vc_fn = analysis_folder + 'vectorChannels.shp'


# define function to display a raster on the map

def displayRaster(raster_fn):
    """
    Displays a raster layer on the map, 
    using the raster's filename as the layer name
    
    Args:
        raster filename
    Returns:
        raster layer
    """
    fi = QFileInfo(raster_fn)
    fname = fi.baseName()
    rlayer = iface.addRasterLayer(raster_fn, fname)
    return rlayer


# define function to extract contours

def extractContours(inDEM, contourInt, contourOut):
    """
    Extracts contours from a DEM using the GDAL contour tool
    for a given contour interval
    
    Args:
        inDEM, DEM filename to use for input
        contourInt, interval between contours (DEM units)
        contourOut, filename to use for output
    Returns:
        None
    """
    processing.run("gdal:contour", # GDAL contour tool
        {'INPUT':inDEM, # input layer
        'BAND':1, # use band 1
        'INTERVAL':contourInt, # interval between contours
        'FIELD_NAME':'ELEV', # optional attribute name
        'CREATE_3D':False, # do not produce 3D vector
        'IGNORE_NODATA':False, # do not treat all raster values as valid
        'NODATA':None, # optional input pixel value to treat as "nodata"
        'OFFSET':0, # optional offset from 0 relative to which to interpret intervals
        'EXTRA':'', # optional additional command-line parameters
        'OUTPUT':contourOut}) # where to save output

    
# mosaic DEMs, if necessary

if len(DEM_fns) != 1: # mosaic if we have more than 1 DEM

    processing.run("saga:mosaicrasterlayers", # SAGA Mosaic Raster Layers tool
        {'GRIDS':DEM_fns, # input grids
        'NAME':'Mosaic', # Name--not important
        'TYPE':7, # data storage type: 4 byte floating point
        'RESAMPLING':1, # bilinear interpolation
        'OVERLAP':4, # overlapping areas: mean
        'BLEND_DIST':8,# blend distance: 8m
        'MATCH':0, # match: none
        'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX':None, # optional output extent
        'TARGET_USER_SIZE':DEM_grain, # raw DEM grain size
        'TARGET_USER_FITS':1, # fit to cells
        'TARGET_OUT_GRID':mDEM_fn}) # where to save output

else: # if we have only 1 DEM, leave as is and treat as mosaicked DEM

    mDEM_fn = DEM_fns[0]


# resample mosaicked DEM, if necessary, and display on map

if DEM_grain != desired_grain:
    
    processing.run("saga:resampling", # SAGA resampling tool
    {'INPUT':mDEM_fn, # input grid
    'KEEP_TYPE':True, # preserve data type
    'SCALE_UP':3, # B-spline interpolation
    'SCALE_DOWN':3, # B-spline interpolation
    'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX':None, # optional output extent
    'TARGET_USER_SIZE':desired_grain, # new grain size
    'TARGET_USER_FITS':1, # fit to cells
    'TARGET_TEMPLATE':None, # optional target system
    'OUTPUT':rmDEM_fn}) # where to save output

else: 
    # we don't have a resampled DEM, so just use the mosaicked one in place of it
    rmDEM_fn = mDEM_fn

displayRaster(rmDEM_fn)


# compute hillshade using desired-grain DEM and display on map

if produce_hillshade == 1:
    
    processing.run("gdal:hillshade", # GDAL hillshade tool
        {'INPUT':rmDEM_fn, # input DEM
        'BAND':1, # band number
        'Z_FACTOR':1, # Z factor (vertical exaggeration)
        'SCALE':1, # scale (ratio of vertical units to horizontal)
        'AZIMUTH':315, # azimuth of the light
        'ALTITUDE':45, # altitude of the light
        'COMPUTE_EDGES':False, # do not compute edges
        'ZEVENBERGEN':False, # do not use ZevenbergenThorne formula
        'COMBINED':False, # do not use combined shading
        'MULTIDIRECTIONAL':False, # do not use multidirectional shading
        'OPTIONS':'', # optional additional creation options
        'EXTRA':'', # optional additional command-line parameters
        'OUTPUT':hs_fn}) # where to save output

    hs_rlayer = displayRaster(hs_fn)

    # apply cumulative cut count setting (set min to 2% and max to 98%)--
    # the "cumulative count cut" option will not be checked in the layer symbology,
    # but the min and max for visualization will be updated accordingly

    hs_dataType = hs_rlayer.renderer().dataType(1) # data type for band 1 (the only band)

    enhancementAlg = QgsContrastEnhancement.StretchToMinimumMaximum

    enhancement = QgsContrastEnhancement(hs_dataType)
    enhancement.setContrastEnhancementAlgorithm(enhancementAlg,True)

    # set cumulative min and max to 2nd and 98th percentiles of band 1 values
    cumulativeMin,cumulativeMax = hs_rlayer.dataProvider().cumulativeCut(1, 0.02, 0.98)

    enhancement.setMinimumValue(cumulativeMin)
    enhancement.setMaximumValue(cumulativeMax)

    hs_rlayer.renderer().setContrastEnhancement(enhancement)

    hs_rlayer.triggerRepaint() # make sure symbology updates
    iface.layerTreeView().refreshLayerSymbology(hs_rlayer.id()) # update legend


# convert desired-grain DEM to feet

if produce_baseContours == 1 or produce_indexContours == 1:

    # set up raster calculator

    rmDEM = QgsRasterLayer(rmDEM_fn)
    output = ftDEM_fn
    entries = []

    rmDEM1 = QgsRasterCalculatorEntry()
    rmDEM1.ref = 'rmDEM@1'
    rmDEM1.raster = rmDEM
    rmDEM1.bandNumber = 1

    entries.append(rmDEM1)

    ftConversionMethod = 'rmDEM@1 * 3.28084'

    # perform calculation

    calc = QgsRasterCalculator(ftConversionMethod, output, 'GTiff',\
        rmDEM.extent(), rmDEM.width(), rmDEM.height(), entries)
    calc.processCalculation()


# extract base contours and display on map
    
if produce_baseContours == 1:

    extractContours(ftDEM_fn, baseContourInt, bc_fn)
    iface.addVectorLayer(bc_fn, '', 'ogr')

# extract index contours and display on map

if produce_indexContours == 1:
        
    extractContours(ftDEM_fn, 10, ic_fn)
    iface.addVectorLayer(ic_fn, '', 'ogr')


# compute slope and display on map

if produce_rasterSlope == 1 or produce_vectorSlope == 1:

    processing.run("gdal:slope",  # GDAL slope tool
        {'INPUT':rmDEM_fn, # input layer
        'BAND':1, # band number
        'SCALE':1, # ratio of vertical units to horizontal
        'AS_PERCENT':True, # express as percent instead of degrees
        'COMPUTE_EDGES':False, # do not compute edges
        'ZEVENBERGEN':False, # do not use ZevenbergenThorne formula
        'OPTIONS':'', # optional additional creation options
        'EXTRA':'', # optional additional command-line parameters
        'OUTPUT':s_fn}) # where to save output

if produce_rasterSlope == 1:
    
    s_rlayer = displayRaster(s_fn)

    # change slope symbology to a classified color scheme

    # set shader

    sShader = QgsColorRampShader()
    sShader.setColorRampType(QgsColorRampShader.Discrete)

    # define symbol categorization

    slopeClassDict = { 5 : ('#000000', '<=5'),
        10 : ('#420a68', '5-10'),
        15 : ('#932567', '10-15'),
        20 : ('#dd5039', '15-20'),
        30 : ('#fcbf0b', '20-30'),
        float('inf') : ('#fcffa4', '>30') }
        
    s_colorRampList = []
        
    for slopeClass, (color, label) in slopeClassDict.items():
        s_colorRampList.append(QgsColorRampShader.ColorRampItem(slopeClass, \
            QColor(color), label))

    sShader.setColorRampItemList(s_colorRampList)
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(sShader)

    # set renderer 

    sRenderer = QgsSingleBandPseudoColorRenderer(s_rlayer.dataProvider(), 1, shader) # 1 is for band 1
    s_rlayer.setRenderer(sRenderer)

    s_rlayer.triggerRepaint() # make sure symbology updates


if produce_vectorSlope == 1:

    # classify slope using raster calculator

    # set up raster calculator

    lyr1 = QgsRasterLayer(s_fn)
    output = cs_fn
    entries = []

    ras = QgsRasterCalculatorEntry()
    ras.ref = 'ras@1'
    ras.raster = lyr1
    ras.bandNumber = 1

    entries.append(ras)

    slopeClassMethod = '(ras@1 >= 0) + (ras@1 > 5) + (ras@1 > 10)\
        + (ras@1 > 15) + (ras@1 > 20) + (ras@1 > 30)'

    # perform calculation

    calc = QgsRasterCalculator(slopeClassMethod, output, 'GTiff', 
        lyr1.extent(), lyr1.width(), lyr1.height(), entries)
    calc.processCalculation()


    # vectorize classed slope and display on map

    processing.run("gdal:polygonize", # GDAL polygonize tool
        {'INPUT':cs_fn, # input layer
        'BAND':1, # band number
        'FIELD':'class', # field to create
        'EIGHT_CONNECTEDNESS':False, # do not use 8-connectedness
        'EXTRA':'', # additional command-line parameters (optional)
        'OUTPUT':vcs_fn}) # where to save output

    # define layer
    vcs_layer = QgsVectorLayer(vcs_fn, 'vectorSlope', 'ogr')

    # define symbol categorization

    categories = []

    vectorSlopeClassDict = { 1 : ('#000000', '<=5'),
        2 : ('#420a68', '5-10'),
        3 : ('#932567', '10-15'),
        4 : ('#dd5039', '15-20'),
        5 : ('#fcbf0b', '20-30'),
        6 : ('#fcffa4', '>30') }

    for slopeClass, (color, label) in vectorSlopeClassDict.items():
        sym = QgsSymbol.defaultSymbol(vcs_layer.geometryType())
        sym.setColor(QColor(color))
        sym.symbolLayer(0).setStrokeColor(QColor('transparent'))
        category = QgsRendererCategory(slopeClass, sym, label)
        categories.append(category)

    # set renderer

    field = 'class'
    vcsRenderer = QgsCategorizedSymbolRenderer(field, categories)
    vcs_layer.setRenderer(vcsRenderer)

    # add to map
    QgsProject.instance().addMapLayer(vcs_layer)


# compute aspect and display on map

if produce_rasterAspect == 1 or produce_vectorAspect == 1:

    processing.run("qgis:aspect", # QGIS aspect tool
        {'INPUT': rmDEM_fn, # elevation layer
        'Z_FACTOR':1, # Z factor
        'OUTPUT': a_fn}) # where to save output

if produce_rasterAspect == 1:
    
    a_rlayer = displayRaster(a_fn)

    # set shader

    aShader = QgsColorRampShader()
    aShader.setColorRampType(QgsColorRampShader.Interpolated)

    # define symbol categorization

    aspectClassDict = { 0 : ('#bf1f26', '0° = N'),
        45: ('#c57724', '45° = NE'),
        90 : ('#dee119', '90° = E'),
        135: ('#76c043', '135° = SE'),
        180 : ('#49c8f5', '180° = S'),
        225: ('#015eae', '225° = SW'),
        270 : ('#4d2d8f', '270° = W'),
        315: ('#bf5095', '315° = NW'),
        360 : ('#bf1f26', '360° = N')}
        
    a_colorRampList = []
        
    for aspectClass, (color, label) in aspectClassDict.items():
        a_colorRampList.append(QgsColorRampShader.ColorRampItem(aspectClass, QColor(color), label))

    aShader.setColorRampItemList(a_colorRampList)
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(aShader)

    # set renderer

    aRenderer = QgsSingleBandPseudoColorRenderer(a_rlayer.dataProvider(), 1, shader)
    a_rlayer.setRenderer(aRenderer)

    a_rlayer.triggerRepaint() # make sure symbology updates


if produce_vectorAspect == 1:
    
    # classify aspect using raster calculator

    # set up raster calculator

    lyr1 = QgsRasterLayer(a_fn)
    output = ca_fn
    entries = []

    ras = QgsRasterCalculatorEntry()
    ras.ref = 'ras@1'
    ras.raster = lyr1
    ras.bandNumber = 1

    entries.append(ras)

    aspectClassMethod = '((ras@1 >=0) + \
        ((ras@1 >= 22.5) AND (ras@1 < 337.5)) + \
        ((ras@1 >= 67.5) AND (ras@1 < 337.5)) + \
        ((ras@1 >= 112.5) AND (ras@1 < 337.5)) + \
        ((ras@1 >= 157.5) AND (ras@1 < 337.5)) + \
        ((ras@1 >= 202.5) AND (ras@1 < 337.5)) + \
        ((ras@1 >= 247.5) AND (ras@1 < 337.5)) + \
        ((ras@1 >= 292.5) AND (ras@1 < 337.5)))'

    # perform calculation

    calc = QgsRasterCalculator(aspectClassMethod, output, 'GTiff', \
        lyr1.extent(), lyr1.width(), lyr1.height(), entries)
    calc.processCalculation()


    # vectorize classed aspect and display on map

    processing.run("gdal:polygonize", # GDAL polygonize tool
        {'INPUT':ca_fn, # input layer
        'BAND':1, # band number
        'FIELD':'class', # field to create
        'EIGHT_CONNECTEDNESS':False, # do not use 8-connectedness
        'EXTRA':'', # additional command-line parameters (optional)
        'OUTPUT':vca_fn}) # where to save output

    # define layer
    vca_layer = QgsVectorLayer(vca_fn, 'vectorAspect', 'ogr')

    # define symbol categorization

    categories = []

    vectorAspectClassDict = { 1 : ('#bf1f26', 'N'),
        2: ('#c57724', 'NE'),
        3 : ('#dee119', 'E'),
        4: ('#76c043', 'SE'),
        5 : ('#49c8f5', 'S'),
        6: ('#015eae', 'SW'),
        7 : ('#4d2d8f', 'W'),
        8: ('#bf5095', 'NW')}

    for aspectClass, (color, label) in vectorAspectClassDict.items():
        sym = QgsSymbol.defaultSymbol(vca_layer.geometryType())
        sym.setColor(QColor(color))
        sym.symbolLayer(0).setStrokeColor(QColor('transparent'))
        category = QgsRendererCategory(aspectClass, sym, label)
        categories.append(category)

    # set renderer

    field = 'class'
    renderer = QgsCategorizedSymbolRenderer(field, categories)
    vca_layer.setRenderer(renderer)

    # add to map
    QgsProject.instance().addMapLayer(vca_layer)


if produce_channels == 1:

    # fill sinks in DEM

    processing.run("saga:fillsinksxxlwangliu", # SAGA Fill Sinks (wang & liu) XXL tool
        {'ELEV':rmDEM_fn, # input DEM
        'MINSLOPE':0.01, # minimum slope (degrees)
        'FILLED':fDEM_fn}) # where to save output


    # compute channel network (vector) and display on map

    processing.run("saga:channelnetworkanddrainagebasins",
        {'DEM':fDEM_fn, # input DEM
        'THRESHOLD':channel_threshold, # threshold
        'DIRECTION':'TEMPORARY_OUTPUT', # flow direction, which we don't need
        'CONNECTION':'TEMPORARY_OUTPUT', # flow connectivity, which we don't need
        'ORDER':'TEMPORARY_OUTPUT', # Strahler order, which we don't need
        'BASIN':'TEMPORARY_OUTPUT', # drainage basins (raster), which we don't need
        'SEGMENTS':vc_fn, # where to save vector channels (the output we want)
        'BASINS':'TEMPORARY_OUTPUT', # drainage basins (vector), which we don't need
        'NODES':'TEMPORARY_OUTPUT'}) # junctions, which we don't need

    # define layer

    vc_layer = QgsVectorLayer(vc_fn, 'vectorChannels', 'ogr')

    # define field name ('ORDER'--the renumbered Strahler order) to use for symbology
    # and obtain max Strahler order value

    order_fieldName='ORDER'
    order_fieldIndex = vc_layer.fields().indexFromName(order_fieldName)
    max_order = vc_layer.maximumValue(order_fieldIndex)

    # obtain Viridis color ramp (built-in)

    vcStyle = QgsStyle().defaultStyle()
    defaultRamps = vcStyle.colorRampNames()
    viridisRamp = vcStyle.colorRamp(defaultRamps[-5]) # this is the index of the Viridis color ramp in Q

    # define symbol graduation

    categories = []

    for channel_order in range(1, max_order+1):
        sym = QgsSymbol.defaultSymbol(vc_layer.geometryType())
        label = str(channel_order)
        category = QgsRendererRange(channel_order, channel_order, sym, label)
        categories.append(category)

    # set renderer

    vcRenderer = QgsGraduatedSymbolRenderer('ORDER', categories) 
    vc_layer.setRenderer(vcRenderer)
    vcRenderer.updateColorRamp(viridisRamp)

    # add to map
    QgsProject.instance().addMapLayer(vc_layer) 
