# terrain-analysis

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
