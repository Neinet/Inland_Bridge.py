#
#   FILE:    Inland_Bridge.py
#   AUTHOR:  Aineias the Stymphalian
#   PURPOSE: Inland_sea.py with a center bridge and multiplayer-friendly customizations.

'''
INLAND BRIDGE NOTES
This mapscript was written based on Bob Thomas (Sirian)'s Inland_Sea.py.

- AineiasSymph, 2026
'''

from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil
import sys
from CvMapGeneratorUtil import MultilayeredFractal
import math

hinted_world = None
# Cache for starting plots
_START_PLOT_MAP = None

def debugLog(msg):
    "Write message to PythonDbg.log"
    try:
        CyPythonMgr().logMsg(msg)
    except:
        print msg   # fallback

def getDescription():
    desc = "Inland_Sea.py with a center bridge and and multiplayer-friendly customizations."
    desc += "Recommended sizes: Small for 3v3, Standard for 4v4."
    return desc

def isAdvancedMap():
    "This map should show up in simple mode"
    return 1

def getNumCustomMapOptions():
    return 7

def getCustomMapOptionName(argsList):
    [iOption] = argsList
    if iOption == 0:
        return "Map Aspect Ratio"
    elif iOption == 1:
        return "Latitude"
    elif iOption == 2:
        return "Axial Tilt"
    elif iOption == 3:
        return "Team Start"
    elif iOption == 4:
        return "Semi-Strategic Resource Balancing"
    elif iOption == 5:
        return "Islands"
    elif iOption == 6:
        return "Geography"
    return ""

def getNumCustomMapOptionValues(argsList):
    [iOption] = argsList
    if iOption == 0: return 2 # Aspect Ratio
    elif iOption == 1: return 2 # Latitude
    elif iOption == 2: return 3 # Axial Tilt
    elif iOption == 3: return 2 # Team Start (Start Together or Disabled)
    elif iOption == 4: return 2 # Semistrategic resources
    elif iOption == 5: return 2 # 
    elif iOption == 6: return 3 # 
    return 0

def getCustomMapOptionDescAt(argsList):
    [iOption, iSelection] = argsList
    if iOption == 0: 
        if iSelection ==0: return "16:10"
        return "4:3"
    elif iOption == 1:
        if iSelection == 0: return "Both Hemispheres"
        return "Single Hemisphere"
    elif iOption == 2:
        if iSelection == 0: return "Disabled"
        elif iSelection == 1: return "90 Degrees"
        return "45 Degrees"
    elif iOption == 3: # Team Start
        if iSelection == 0: return "Start Together"
        return "Disabled"
    elif iOption == 4: # SemiStrategic
        if iSelection == 0: return "1/2 Ivory, Marble, Stone per Team Member"
        return "Disabled"
    elif iOption == 5: # Islands
        if iSelection == 0: return "Disabled"
        return "Enabled"
    elif iOption == 6: # Geography
        if iSelection == 0: return "Two Seas"
        elif iSelection == 1: return "Infinity"
        return "Hourglass"
    return ""

def getCustomMapOptionDefault(argsList):
    [iOption] = argsList
    if iOption == 0: # 16:10
        return 0
    elif iOption == 1: # Latitude: Both
        return 0
    elif iOption == 2: # Axial Tilt: 
        return 1
    elif iOption == 3: # Team Start: 
        return 0
    elif iOption == 4: # SemiStrategic: 1/2 per player
        return 0
    elif iOption == 5: # Islands: On
        return 1
    elif iOption == 6: # Geography: Two Seas
        return 0
    return 0

########################################
# Starting Plot
########################################

# Global variables for Team Start
bTeamPlacement = False
teamHalfMap = {}
northThreshold = 0   # y >= this is north
southThreshold = 0   # y < this is south
_START_PLOT_MAP = None

def beforeGeneration():
    global bTeamPlacement, teamHalfMap, northThreshold, southThreshold, _START_PLOT_MAP
    gc = CyGlobalContext()
    map = CyMap()
    mapRand = gc.getGame().getMapRand()
    _START_PLOT_MAP = None

    print "=== beforeGeneration START ==="
    activeTeams = []
    for i in range(gc.getMAX_CIV_PLAYERS()):
        pPlayer = gc.getPlayer(i)
        if pPlayer.isEverAlive():
            iTeam = pPlayer.getTeam()
            if iTeam not in activeTeams:
                activeTeams.append(iTeam)
    
    activeTeams.sort() # Sorted list ensures consistent mapping
    numTeams = len(activeTeams)
    teamStartOption = map.getCustomMapOption(3)

    bTeamPlacement = False
    teamHalfMap.clear()

    # We only handle team placement for 2, 3, or 4 teams
    if teamStartOption != 2 and (numTeams >= 2 and numTeams <= 4):
        bTeamPlacement = True
        iH = map.getGridHeight()
        
        # 1. Define region pool based on team count
        if numTeams == 2:
            regions = [0, 1] # 0=North, 1=South
            southThreshold = int(iH * 0.3)
            northThreshold = int(iH * 0.7)
        else:
            regions = [10, 11, 12, 13] # 10=SW, 11=SE, 12=NW, 13=NE

        # 2. Shuffle the regions list using Civ's mapRand
        # This ensures every generation (even on "Regenerate Map") swaps positions
        for i in range(len(regions)):
            j = mapRand.get(len(regions), "Shuffling Regions PYTHON")
            # Swap
            temp = regions[i]
            regions[i] = regions[j]
            regions[j] = temp
        
        # 3. Assign the shuffled regions to the sorted team list
        for i in range(numTeams):
            targetTeam = activeTeams[i]
            assignedRegion = regions[i]
            teamHalfMap[targetTeam] = assignedRegion
            print "Team %d assigned to Region %d" % (targetTeam, assignedRegion)
            
    print "=== beforeGeneration END ==="

def _assign_all_starting_plots():
    gc = CyGlobalContext()
    map = CyMap()
    mapRand = gc.getGame().getMapRand()
    iW = map.getGridWidth()
    iH = map.getGridHeight()
    
    # 1. Group players by Team
    teamPlayersMap = {}
    for i in range(gc.getMAX_CIV_PLAYERS()):
        pPlayer = gc.getPlayer(i)
        if pPlayer.isEverAlive():
            tID = pPlayer.getTeam()
            if not teamPlayersMap.has_key(tID):
                teamPlayersMap[tID] = []
            teamPlayersMap[tID].append(i)

    sortedTeams = teamPlayersMap.keys()
    sortedTeams.sort()

    assignments = {}
    assigned_plots = []
    
    biggestArea = map.findBiggestArea(False)
    biggestAreaID = -1
    if not biggestArea.isNone():
        biggestAreaID = biggestArea.getID()

    for tID in sortedTeams:
        teamPlayers = teamPlayersMap[tID]
        numInTeam = len(teamPlayers)
        region = teamHalfMap.get(tID, -1)
        
        # RANDOMIZE SLICES
        # We create a list of indices and shuffle them to assign horizontal positions
        sliceOrder = []
        for s in range(numInTeam):
            sliceOrder.append(s)
        
        for i in range(numInTeam):
            j = mapRand.get(numInTeam, "Shuffle Slices")
            temp = sliceOrder[i]
            sliceOrder[i] = sliceOrder[j]
            sliceOrder[j] = temp

        # 2. Process each player in the team
        for i in range(numInTeam):
            playerID = teamPlayers[i]
            player = gc.getPlayer(playerID)
            player.AI_updateFoundValues(True)

            # --- SEARCH BOX CALCULATION ---
            xMin, xMax = 2, iW - 2
            yMin, yMax = 2, iH - 2

            # Team Region Logic
            if region == 0: yMin = northThreshold
            elif region == 1: yMax = southThreshold
            elif region == 10 or region == 11: yMax = int(iH * 0.3)
            elif region == 12 or region == 13: yMin = int(iH * 0.7)

            # Horizontal Slice Logic (Even Distribution)
            availXMin, availXMax = 2, iW - 2
            if region == 10 or region == 12: availXMax = int(iW * 0.3)
            elif region == 11 or region == 13: availXMin = int(iW * 0.7)

            sliceIdx = sliceOrder[i]
            sliceWidth = (availXMax - availXMin) / numInTeam
            xMin = availXMin + (sliceIdx * sliceWidth)
            xMax = xMin + sliceWidth
            
            # Add overlap and clamp
            xMin = max(2, xMin - 2)
            xMax = min(iW - 3, xMax + 2)
            yMin = max(2, yMin)
            yMax = min(iH - 3, yMax)

            # 3. Best Plot Search
            currentMinDist = 10
            plotAssigned = False
            while currentMinDist >= 0 and not plotAssigned:
                bestVal, bestPlot = -1, None
                for x in range(xMin, xMax + 1):
                    for y in range(yMin, yMax + 1):
                        pPlot = map.plot(x, y)
                        if pPlot.isWater() or pPlot.isPeak(): continue
                        if biggestAreaID != -1 and pPlot.getArea() != biggestAreaID: continue
                        
                        tooClose = False
                        for (ax, ay) in assigned_plots:
                            if plotDistance(x, y, ax, ay) < currentMinDist:
                                tooClose = True
                                break
                        if tooClose: continue
                        
                        val = pPlot.getFoundValue(playerID)
                        if val > bestVal:
                            bestVal, bestPlot = val, pPlot
                
                if bestPlot is not None:
                    assignments[playerID] = map.plotNum(bestPlot.getX(), bestPlot.getY())
                    assigned_plots.append((bestPlot.getX(), bestPlot.getY()))
                    plotAssigned = True
                else:
                    currentMinDist -= 1
            
            # Emergency Fallback
            if not plotAssigned:
                for x in range(xMin, xMax + 1):
                    for y in range(yMin, yMax + 1):
                        pPlot = map.plot(x, y)
                        if not pPlot.isWater() and not pPlot.isPeak():
                            if (x, y) not in assigned_plots:
                                assignments[playerID] = map.plotNum(x, y)
                                assigned_plots.append((x, y))
                                plotAssigned = True
                                break
                    if plotAssigned: break
                    
    return assignments

def findStartingPlot(argsList):
    global bTeamPlacement, _START_PLOT_MAP
    playerID = argsList[0]
    gc = CyGlobalContext()
    player = gc.getPlayer(playerID)
    
    leaderName = "Unknown"
    if player.isEverAlive():
        leaderName = player.getName()
        
    print "findStartingPlot called for %s (player %d), bTeamPlacement=%s" % (leaderName, playerID, bTeamPlacement)

    # Revert to standard logic if Team Placement turned off or invalid team sizes
    if not bTeamPlacement:
        print "Team placement off, returning -1"
        return -1

    if _START_PLOT_MAP is None:
        print "Generating start plot cache"
        _START_PLOT_MAP = _assign_all_starting_plots()

    result = _START_PLOT_MAP.get(playerID, -1)
    print "Returning plot %d for %s" % (result, leaderName)
    return result

def normalizeStartingPlotLocations():
    """
    By default, the C++ DLL will shuffle players among the chosen starting 
    plots to balance yields or group teams according to its own hardcoded logic.
    We must override this function to prevent the DLL from swapping our players 
    after we carefully assigned them to the North/South halves.
    """
    global bTeamPlacement
    
    if bTeamPlacement:
        # Do NOT call CyPythonMgr().allowDefaultImpl()
        # By doing nothing here, we completely disable the C++ shuffling.
        # Players will spawn exactly on the plots assigned in findStartingPlot.
        return None
    else:
        # If team placement is off, let the C++ engine balance starting plots normally
        CyPythonMgr().allowDefaultImpl()
        return None

#
def minStartingDistanceModifier():
    numPlrs = CyGlobalContext().getGame().countCivPlayersEverAlive()
    if numPlrs  <= 18:
        return -95
    else:
        return -50

########################################
# Map Properties
########################################
def getWrapX():
    return False
def getWrapY():
    return False

def getTopLatitude():
    return 60
def getBottomLatitude():
    return -60

def getGridSize(argsList):
    "Because this is such a land-heavy map, override getGridSize() to make the map smaller"
    map = CyMap()
    AspectRatioOption = map.getCustomMapOption(0)
    if AspectRatioOption == 0: # 16:10
        grid_sizes = {
            WorldSizeTypes.WORLDSIZE_DUEL:      (6,4),
            WorldSizeTypes.WORLDSIZE_TINY:      (8,5),
            WorldSizeTypes.WORLDSIZE_SMALL:     (10,6),
            WorldSizeTypes.WORLDSIZE_STANDARD:  (12,7),
            WorldSizeTypes.WORLDSIZE_LARGE:     (13,8),
            WorldSizeTypes.WORLDSIZE_HUGE:      (15,9)
        }
    else: # 4:3
        grid_sizes = {
            WorldSizeTypes.WORLDSIZE_DUEL:      (6,4),
            WorldSizeTypes.WORLDSIZE_TINY:      (8,6),
            WorldSizeTypes.WORLDSIZE_SMALL:     (9,7),
            WorldSizeTypes.WORLDSIZE_STANDARD:  (10,8),
            WorldSizeTypes.WORLDSIZE_LARGE:     (11,9),
            WorldSizeTypes.WORLDSIZE_HUGE:      (13,10)
        }

    if (argsList[0] == -1): # (-1,) is passed to function on loads
        return []
    [eWorldSize] = argsList
    return grid_sizes[eWorldSize]


########################################
# Plot Generation
########################################
# Subclasses to fix the FRAC_POLAR zero row bugs.
# -----------------------------------------------------------------------------
# GeometricMultiFractal Generator
# -----------------------------------------------------------------------------
class GeometricMultiFractal(CvMapGeneratorUtil.MultilayeredFractal):
    """
    Fractal generator supporting geometric masking and rotation.
    Shapes: RECT, ELLIPSE, ISOTRI.
    """
    def generatePlotsByRegion(self, region_data):
        sea = 0 
        
        # Define Terrain Profiles: (HillDensity%, PeakDensity%_of_Hills)
        terrain_profiles = {
            "flat":         (15, 1),
            "plateau":      (60, 25),
            "highland":     (75, 40),
            "alpine":       (95, 70),
            "default":      (30, 20)
        }
        
        gc = CyGlobalContext()
        m = CyMap()
        iRocky = gc.getInfoTypeForString("CLIMATE_ROCKY")
        if m.getClimate() == iRocky:
            for key in terrain_profiles.keys():
                h_dens, p_dens = terrain_profiles[key]
                new_h = int(h_dens * 1.2)
                new_p = int(p_dens * 1.1)
                if new_h > 100: new_h = 100
                if new_p > 100: new_p = 100
                terrain_profiles[key] = (new_h, new_p)

        for data in region_data:
            name, r_type_raw, cx, cy, d1, d2, d3, terrain, grain, h_grain, water_prc = data
            r_type = r_type_raw.upper()
            
            # 1. Coordinate Math
            center_x = cx * self.iW
            center_y = cy * self.iH
            radius_x = (d1 / 2.0) * self.iW
            radius_y = (d2 / 2.0) * self.iH
            height_tiles = d2 * self.iH
            max_radius_tiles = math.sqrt(radius_x**2 + radius_y**2)
            
            iWest = max(0, int(center_x - max_radius_tiles))
            iEast = min(self.iW - 1, int(center_x + max_radius_tiles))
            iSouth = max(0, int(center_y - max_radius_tiles))
            iNorth = min(self.iH - 1, int(center_y + max_radius_tiles))
            
            reg_w, reg_h = iEast - iWest + 1, iNorth - iSouth + 1
            if reg_w <= 0 or reg_h <= 0: continue

            # 2. Fractal Initialization
            NiTextOut("Generating %s (Geometric Fractal) ..." % name)
            
            # This fractal is now shared by BOTH Land and Water regions
            regionContFrac = CyFractal()
            regionContFrac.fracInit(reg_w, reg_h, grain, self.dice, 0, -1, -1)
            
            # Calculate threshold for the "Active" part of the fractal
            if water_prc <= 0:
                iWaterThreshold = -1
            elif water_prc >= 100:
                iWaterThreshold = 255
            else:
                iWaterThreshold = regionContFrac.getHeightFromPercent(water_prc + sea)

            is_subtractive = (terrain == "water")
            
            # Only Land regions need Hill/Peak fractals
            if not is_subtractive:
                regionHillsFrac = CyFractal()
                regionPeaksFrac = CyFractal()
                regionHillsFrac.fracInit(reg_w, reg_h, h_grain, self.dice, 0, -1, -1)
                regionPeaksFrac.fracInit(reg_w, reg_h, h_grain+1, self.dice, 0, -1, -1)

                h_dens, p_dens = terrain_profiles.get(terrain, terrain_profiles["default"])
                iHillThreshold = regionHillsFrac.getHeightFromPercent(100 - h_dens)
                iPeakThreshold = regionPeaksFrac.getHeightFromPercent(100 - p_dens)

            # Rotation/Geometry Math
            rad = -math.radians(d3)
            cosA, sinA = math.cos(rad), math.sin(rad)
            v_dist, b_dist = (2.0 / 3.0) * height_tiles, (1.0 / 3.0) * height_tiles
            invRxSq, invRySq = 0.0, 0.0
            if radius_x > 0: invRxSq = 1.0 / (radius_x * radius_x)
            if radius_y > 0: invRySq = 1.0 / (radius_y * radius_y)

            # 3. Iterate over the grid
            for x in range(reg_w):
                world_x = x + iWest
                # Add 0.5 to world_x to get the center of the tile
                dx = (float(world_x) + 0.5) - center_x
                for y in range(reg_h):
                    world_y = y + iSouth
                    # Add 0.5 to world_y to get the center of the tile
                    dy = (float(world_y) + 0.5) - center_y

                    # Now, tiles on either side of an even-numbered split will have 
                    # identical distance values (e.g., -0.5 and 0.5).
                    # Geometry Check
                    rx = dx * cosA - dy * sinA
                    ry = dx * sinA + dy * cosA
                    is_inside = False
                    if r_type == "ELLIPSE":
                        if (rx*rx * invRxSq) + (ry*ry * invRySq) <= 1.0: is_inside = True
                    elif r_type == "ISOTRI":
                        if ry >= -b_dist and ry <= v_dist:
                            max_rx = radius_x * (v_dist - ry) / height_tiles
                            if abs(rx) <= max_rx: is_inside = True
                    else: # RECT
                        if abs(rx) <= radius_x and abs(ry) <= radius_y: is_inside = True

                    if not is_inside: continue
                        
                    # Decide plot type
                    world_i = world_y * self.iW + world_x
                    val = regionContFrac.getHeight(x, y)
                    
                    if is_subtractive:
                        # WATER REGION: If fractal roll is within the water percent, punch a hole.
                        # Setting water_prc=100 will now correctly turn every tile to ocean.
                        if val <= iWaterThreshold:
                            self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_OCEAN
                    else:
                        # LAND REGION: Skip tiles within the water percent threshold (remains ocean).
                        if val <= iWaterThreshold: 
                            continue
                        
                        # Process Hills and Peaks for land
                        if regionHillsFrac.getHeight(x, y) >= iHillThreshold:
                            if regionPeaksFrac.getHeight(x, y) >= iPeakThreshold:
                                self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_PEAK
                            else:
                                self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_HILLS
                        else:
                            self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_LAND
                            
        return self.wholeworldPlotTypes

def generatePlotTypes():
    """Specify map regions here."""
    NiTextOut("Setting Plot Types (Python Central Plains) ...")
    
    global _START_PLOT_MAP, _DEBUG_REGIONS
    _START_PLOT_MAP = None

    gc = CyGlobalContext()
    m = CyMap()
    climate = m.getClimate()
    
    peak_opt = m.getCustomMapOption(1)
    geography_opt = m.getCustomMapOption(6)
    island_opt = m.getCustomMapOption(5)
    
    regions = []
    additional_regions = []
    island_regions = []
    
    sizekey = m.getWorldSize()
    sizevalues = {
        WorldSizeTypes.WORLDSIZE_DUEL:      (3,2,1),
        WorldSizeTypes.WORLDSIZE_TINY:      (3,2,1),
        WorldSizeTypes.WORLDSIZE_SMALL:     (4,2,1),
        WorldSizeTypes.WORLDSIZE_STANDARD:  (4,2,1),
        WorldSizeTypes.WORLDSIZE_LARGE:     (5,2,1),
        WorldSizeTypes.WORLDSIZE_HUGE:      (5,2,1)
    }
    (ScatterGrain, BalanceGrain, GatherGrain) = sizevalues[sizekey]

    # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
    regions = [
            ("Rect3", "Rect", 0.500, 0.5, 1.000, 1.000, 0, "default", BalanceGrain, ScatterGrain, 0),
        ]
    if geography_opt == 0: # Two Seas
        # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
        additional_regions = [
            ("Ellipse_Sea_R_BG", "Ellipse", 0.730, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, BalanceGrain, 100),
            ("Ellipse_Sea_R", "Ellipse", 0.730, 0.5, 0.4, 0.5, 0, "water", BalanceGrain, BalanceGrain, 70),
            ("Ellipse_Sea_L_BG", "Ellipse", 0.270, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, BalanceGrain, 100),
            ("Ellipse_Sea_L", "Ellipse", 0.270, 0.5, 0.4, 0.5, 0, "water", BalanceGrain, BalanceGrain, 70),
            ("Bridge", "Ellipse", 0.500, 0.500, 0.170, 0.200, 0, "default", GatherGrain, ScatterGrain, 10),
        ]
        if island_opt == 1: # Enabled
            # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
            island_regions = [
                ("IslandsTL", "Rect", 0.270, 0.650, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 85),
                ("IslandsTR", "Rect", 0.730, 0.650, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 85),
                ("IslandsBL", "Rect", 0.270, 0.350, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 85),
                ("IslandsBR", "Rect", 0.730, 0.350, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 85),
            ]
    elif geography_opt == 1: # Infinite Sea
        # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
        additional_regions = [
            ("Ellipse_Sea_R_BG", "Ellipse", 0.730, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, BalanceGrain, 100),
            ("Ellipse_Sea_L_BG", "Ellipse", 0.270, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, BalanceGrain, 100),
            ("Ellipse_Sea_R", "Ellipse", 0.730, 0.500, 0.375, 0.650, 0, "water", BalanceGrain, BalanceGrain, 70),
            ("Ellipse_Sea_L", "Ellipse", 0.270, 0.500, 0.375, 0.650, 0, "water", BalanceGrain, BalanceGrain, 70),
            ("Bridge", "Ellipse", 0.500, 0.500, 0.170, 0.200, 0, "water", GatherGrain, BalanceGrain, 90),
        ]
        if island_opt == 1: # Enabled
            # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
            island_regions = [
                ("IslandsCL", "Ellipse", 0.280, 0.500, 0.170, 0.200, 0, "default", BalanceGrain, BalanceGrain, 10),
                ("IslandsCR", "Ellipse", 0.720, 0.500, 0.170, 0.200, 0, "default", BalanceGrain, BalanceGrain, 10),
            ]
    else: # Hourglass
        # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
        additional_regions = [
            ("Ellipse_SeaL", "Ellipse", 0.95, 0.500, 0.500, 0.850, 0, "water", BalanceGrain, BalanceGrain, 90),
            ("Ellipse_SeaR", "Ellipse", 0.050, 0.500, 0.500, 0.850, 0, "water", BalanceGrain, BalanceGrain, 90),
            ("Ellipse_small_seaL", "Ellipse", 0.250, 0.500, 0.300, 0.400, 0, "water", BalanceGrain, BalanceGrain, 85),
            ("Ellipse_small_seaR", "Ellipse", 0.750, 0.500, 0.300, 0.400, 0, "water", BalanceGrain, BalanceGrain, 85),
        ]
        if island_opt == 1: # Enabled
            # Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
            island_regions = [
                ("IslandsTL", "Rect", 0.100, 0.650, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 87),
                ("IslandsTR", "Rect", 0.900, 0.650, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 87),
                ("IslandsBL", "Rect", 0.100, 0.350, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 87),
                ("IslandsBR", "Rect", 0.900, 0.350, 0.170, 0.200, 0, "flat", ScatterGrain, BalanceGrain, 87),
            ]

    regions.extend(additional_regions)
    regions.extend(island_regions)

    # Peak Reduction Logic
    processed_regions = []
    for r in regions:
        r_list = list(r)
        terrain = r_list[7]
        if peak_opt == 0: # Flatten Alpine
            if terrain == "alpine": r_list[7] = "highland"
        elif peak_opt == 1: # Flatten Highland
            if terrain == "highland": r_list[7] = "plateau"
            if terrain == "alpine": r_list[7] = "highland"
        processed_regions.append(tuple(r_list))

    # Store the list for the debug sign placer
    _DEBUG_REGIONS = regions

    global plotgen
    plotgen = GeometricMultiFractal()
    plotTypes = plotgen.generatePlotsByRegion(regions)
    
    # ENFORCE LAND EDGES
    # We iterate through the final plot array and force edges to PLOT_LAND
    iW = m.getGridWidth()
    iH = m.getGridHeight()
    for x in range(iW):
        for y in range(iH):
            if x == 0 or x == iW - 1 or y == 0 or y == iH - 1:
                i = y * iW + x
                # If it's water or a peak, force it to be flat or hill
                if plotTypes[i] == PlotTypes.PLOT_OCEAN:
                    plotTypes[i] = PlotTypes.PLOT_LAND
                if plotTypes[i] == PlotTypes.PLOT_PEAK:
                    plotTypes[i] = PlotTypes.PLOT_HILLS

    
    return plotTypes


########################################
# Terrain & Feature Generation
########################################
def calculateInternalLat(iX, iY):
    """
    Helper to calculate raw latitude (0.0 to 1.0) based on 
    Latitude and Axial Tilt settings.
    """
    map = CyMap()
    iW = map.getGridWidth()
    iH = map.getGridHeight()
    
    # Custom Option 1: Latitude (0=Both, 1=Single)
    # Custom Option 2: Axial Tilt (0=Disabled, 1=90 deg, 2=45 deg)
    iLatOption = map.getCustomMapOption(1)
    iTiltOption = map.getCustomMapOption(2)
    
    # Avoid division by zero
    if iW <= 1: iW = 2
    if iH <= 1: iH = 2
    
    # Normalize coordinates to 0.0 - 1.0 range
    fX = float(iX) / (iW - 1)
    fY = float(iY) / (iH - 1)
    
    resLat = 0.0
    
    # Case 0: Disabled (Standard horizontal bands)
    if iTiltOption == 0:
        if iLatOption == 0: # Both Hemispheres
            resLat = abs(fY - 0.5) * 2.0
        else: # Single Hemisphere
            resLat = fY
            
    # Case 1: 90 Degrees (Vertical bands / Poles on left and right)
    elif iTiltOption == 1:
        if iLatOption == 0: # Both Hemispheres
            resLat = abs(fX - 0.5) * 2.0
        else: # Single Hemisphere
            resLat = fX
            
    # Case 2: 45 Degrees (Diagonal bands)
    elif iTiltOption == 2:
        if iLatOption == 0: # Both Hemispheres
            # Equator runs from top-left to bottom-right
            resLat = abs((fX + fY) - 1.0)
        else: # Single Hemisphere
            # Equator at bottom-left corner, Pole at top-right
            resLat = (fX + fY) / 2.0
            
    # Final clamping to ensure safety
    if resLat > 1.0: resLat = 1.0
    if resLat < 0.0: resLat = 0.0
    
    return resLat

# subclass TerrainGenerator to eliminate arctic, equatorial latitudes
class ISTerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):
    def getLatitudeAtPlot(self, iX, iY):
        map = CyMap()
        # Custom Option 1: Latitude (0=Both, 1=Single)
        # Custom Option 2: Axial Tilt (0=Disabled, 1=90 deg, 2=45 deg)
        iLatOption = map.getCustomMapOption(1)
        iTiltOption = map.getCustomMapOption(2)
        lat = calculateInternalLat(iX, iY)
        # Apply the Inland Sea temperate shift
        if iLatOption == 1 and iTiltOption == 1:
            lat = 0.07 + 0.55 * lat
        elif iLatOption == 1 and iTiltOption == 0:
            lat = 0.03 + 0.55 * lat
        else:
            lat = 0.03 + 0.57 * lat
        return lat

def generateTerrainTypes():
    NiTextOut("Generating Terrain (Python Inland Sea) ...")
    terraingen = ISTerrainGenerator()
    terrainTypes = terraingen.generateTerrain()
    return terrainTypes

# subclass FeatureGenerator to eliminate arctic, equatorial latitudes
class ISFeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
    def getLatitudeAtPlot(self, iX, iY):
        lat = calculateInternalLat(iX, iY)
        # Apply the Inland Sea temperate shift (0.07 to 0.63)
        lat = 0.03 + 0.60 * lat
        return lat

def addFeatures():
    NiTextOut("Adding Features (Python Inland Sea) ...")
    featuregen = ISFeatureGenerator()
    featuregen.addFeatures()
    return 0

def getRiverStartCardinalDirection(argsList):
    pPlot = argsList[0]
    map = CyMap()

    iX = pPlot.getX()
    iY = pPlot.getY()
    iW = map.getGridWidth()
    iH = map.getGridHeight()

    # 1. THE LAND BRIDGE OVERRIDE
    # If we are in the central 20% of the map, force rivers sideways into the seas.
    if (iX > (iW * 0.4) and iX < (iW * 0.6)):
        if (iX < (iW / 2)):
            return CardinalDirectionTypes.CARDINALDIRECTION_WEST
        else:
            return CardinalDirectionTypes.CARDINALDIRECTION_EAST

    # 2. Top and Bottom latitudes flow towards the equator
    if (iY > ((iH * 2) / 3)):
        return CardinalDirectionTypes.CARDINALDIRECTION_SOUTH

    if (iY < (iH / 3)):
        return CardinalDirectionTypes.CARDINALDIRECTION_NORTH

    # 3. Middle latitudes flow horizontally into the nearest sea
    if (iX < (iW / 4)):
        return CardinalDirectionTypes.CARDINALDIRECTION_EAST
    if (iX < (iW / 2)):
        return CardinalDirectionTypes.CARDINALDIRECTION_WEST
    if (iX < ((iW * 3) / 4)):
        return CardinalDirectionTypes.CARDINALDIRECTION_EAST

    return CardinalDirectionTypes.CARDINALDIRECTION_WEST

def getRiverAltitude(argsList):
    pPlot = argsList[0]
    map = CyMap()

    CyPythonMgr().allowDefaultImpl()

    iX = pPlot.getX()
    iY = pPlot.getY()
    iW = map.getGridWidth()
    iH = map.getGridHeight()
    
    iCenterY = iH / 2
    
    if iX < (iW / 2):
        iCenterX = iW / 4
    else:
        iCenterX = (iW * 3) / 4
        
    # The X-axis gradient (30) is now much steeper than the Y-axis gradient (10).
    # This forces rivers to "fall" into the sea rather than running parallel to the shore.
    return ((abs(iX - iCenterX) * 15) + (abs(iY - iCenterY) * 10))
    
########################################
# Custom Resource Options
########################################


class ResourceManager:
    def __init__(self, map_obj, gc, dice):
        self.map = map_obj
        self.gc = gc
        self.dice = dice
        self.engine = CyEngine()
        self.iW = map_obj.getGridWidth()
        self.iH = map_obj.getGridHeight()

    def _bonus_id(self, name):
        return self.gc.getInfoTypeForString(name)

    def swap_resources(self, target_name, replace_name):
        """Globally replaces target with replace, or removes if None."""
        iTarget = self._bonus_id(target_name)
        iReplace = -1
        if replace_name is not None:
            iReplace = self._bonus_id(replace_name)

        for i in range(self.map.numPlots()):
            pPlot = self.map.plotByIndex(i)
            if pPlot.getBonusType(-1) == iTarget:
                pPlot.setBonusType(iReplace)
                # Place Debug Sign
                # msg = "Swapped: " + str(target_name)
                # if replace_name: msg += " -> " + str(replace_name)
                # self.engine.addSign(pPlot, -1, msg)

    def place_balanced_team_resource(self, bonus_name):
        """Places resources near a random team member's starting plot."""
        global _START_PLOT_MAP, teamHalfMap
        
        if _START_PLOT_MAP is None:
            return # Safety check

        iBonus = self._bonus_id(bonus_name)
        
        # 1. Group starting plot coordinates by Team
        teamStartPlots = {}
        teamSizes = {}
        for pID, plotIdx in _START_PLOT_MAP.items():
            pPlayer = self.gc.getPlayer(pID)
            if pPlayer.isEverAlive():
                tID = pPlayer.getTeam()
                if not teamStartPlots.has_key(tID):
                    teamStartPlots[tID] = []
                    teamSizes[tID] = 0
                
                pStartPlot = self.map.plotByIndex(plotIdx)
                teamStartPlots[tID].append((pStartPlot.getX(), pStartPlot.getY()))
                teamSizes[tID] += 1

        # 2. Iterate through teams assigned in beforeGeneration
        sortedTeams = teamHalfMap.keys()
        sortedTeams.sort()

        for tID in sortedTeams:
            if not teamStartPlots.has_key(tID): continue
            
            # Determine how many to place (1 per 2 players, min 1)
            count = teamSizes[tID] / 2
            if count < 1: count = 1
            
            placed = 0
            # Get the list of start plots for this team
            memberPlots = teamStartPlots[tID]
            
            # We shuffle the list of member plots so that if we need to place 
            # multiple bonuses, they are distributed among different members.
            shuffledPlots = []
            for p in memberPlots: shuffledPlots.append(p)
            
            # Simple shuffle for Python 2.4
            for i in range(len(shuffledPlots)):
                j = self.dice.get(len(shuffledPlots), "Member Shuffle")
                temp = shuffledPlots[i]
                shuffledPlots[i] = shuffledPlots[j]
                shuffledPlots[j] = temp

            # 3. Placement Loop
            for i in range(count):
                # Pick a member's plot (loop back if more resources than members)
                originCoords = shuffledPlots[i % len(shuffledPlots)]
                originX, originY = originCoords
                
                bestPlot = None
                bestValue = -1
                
                # Search in a box around the starting plot
                # Distance 5 means looking 5 tiles out in all directions
                for dx in range(-6, 7):
                    for dy in range(-6, 7):
                        dist = plotDistance(originX, originY, originX + dx, originY + dy)
                        
                        # We want it roughly 5 tiles away (allow 4 to 6 for flexibility)
                        if dist >= 4 and dist <= 6:
                            pPlot = self.map.plot(originX + dx, originY + dy)
                            
                            if pPlot.isNone(): continue
                            if pPlot.isWater() or pPlot.isPeak(): continue
                            if pPlot.getBonusType(-1) != -1: continue
                            if pPlot.isStartingPlot(): continue
                                
                            # CRITICAL: Check if the tile already has a resource
                            if pPlot.getBonusType(-1) != -1:
                                continue
                            
                            # Check if it's a "natural" spot for this resource
                            # This checks terrain/feature requirements
                            val = 0
                            if pPlot.canHaveBonus(iBonus, True):
                                val = 100 + self.dice.get(100, "Resource Randomizer")
                            else:
                                # Forced placement candidate
                                val = 10 + self.dice.get(50, "Resource Randomizer")
                                
                            if val > bestValue:
                                bestValue = val
                                bestPlot = pPlot
                
                # 4. Finalize Placement
                if bestPlot is not None:
                    bestPlot.setBonusType(iBonus)
                    
                    # If we forced it onto a bad tile (e.g. Ivory on Marsh), 
                    # clear the feature so the resource is visible/usable
                    if not bestPlot.canHaveBonus(iBonus, False):
                        bestPlot.setFeatureType(FeatureTypes.NO_FEATURE, -1)
                    
                    # Add Debug Sign
                    self.engine.addSign(bestPlot, -1, "Balanced " + bonus_name)
                    placed += 1

def normalizeAddExtras():
    gc = CyGlobalContext()
    map = CyMap()
    dice = gc.getGame().getMapRand()
    # Recalculate to ensure accurate terrain/water detection
    map.recalculateAreas()
    
    # Instantiate the Generalized Manager
    rm = ResourceManager(map, gc, dice)
    
    # Handle Ivory Option (Option 4)
    iSemiStrategicOption = map.getCustomMapOption(4)
    
    # bTeamPlacement is our global variable from the start plot logic
    if bTeamPlacement and iSemiStrategicOption == 0:
        print "PY: Balancing semi-strategic resources for Teams..."
        # 1. Global Swap
        rm.swap_resources("BONUS_IVORY", None)
        rm.swap_resources("BONUS_STONE", None)
        rm.swap_resources("BONUS_MARBLE", None)
        # 2. Place Balanced: Bonus per team region
        rm.place_balanced_team_resource("BONUS_IVORY")
        rm.place_balanced_team_resource("BONUS_STONE")
        rm.place_balanced_team_resource("BONUS_MARBLE")

    # Finalize by calling the engine's default extras (like Goody Huts)
    CyPythonMgr().allowDefaultImpl()


