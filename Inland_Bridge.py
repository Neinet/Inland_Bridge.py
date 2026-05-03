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
from CvMapGeneratorUtil import HintedWorld

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
    return 5

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
    return ""

def getNumCustomMapOptionValues(argsList):
    [iOption] = argsList
    if iOption == 0: return 2 # Aspect Ratio
    elif iOption == 1: return 2 # Latitude
    elif iOption == 2: return 3 # Axial Tilt
    elif iOption == 3: return 2 # Team Start (Start Together or Disabled)
    elif iOption == 4: return 2 # Ivory
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
class ISFractalWorld(CvMapGeneratorUtil.FractalWorld):
    def generatePlotTypes(self, water_percent=78, shift_plot_types=True, 
                          grain_amount=3):
        # Check for changes to User Input variances.
        self.checkForOverrideDefaultUserInputVariances()
        
        self.hillsFrac.fracInit(self.iNumPlotsX, self.iNumPlotsY, grain_amount, self.mapRand, 0, self.fracXExp, self.fracYExp)
        self.peaksFrac.fracInit(self.iNumPlotsX, self.iNumPlotsY, grain_amount+1, self.mapRand, 0, self.fracXExp, self.fracYExp)

        water_percent += self.seaLevelChange
        water_percent = min(water_percent, self.seaLevelMax)
        water_percent = max(water_percent, self.seaLevelMin)

        iWaterThreshold = self.continentsFrac.getHeightFromPercent(water_percent)
        iHillsBottom1 = self.hillsFrac.getHeightFromPercent(max((self.hillGroupOneBase - self.hillGroupOneRange), 0))
        iHillsTop1 = self.hillsFrac.getHeightFromPercent(min((self.hillGroupOneBase + self.hillGroupOneRange), 100))
        iHillsBottom2 = self.hillsFrac.getHeightFromPercent(max((self.hillGroupTwoBase - self.hillGroupTwoRange), 0))
        iHillsTop2 = self.hillsFrac.getHeightFromPercent(min((self.hillGroupTwoBase + self.hillGroupTwoRange), 100))
        iPeakThreshold = self.peaksFrac.getHeightFromPercent(self.peakPercent)

        for x in range(self.iNumPlotsX):
            for y in range(self.iNumPlotsY):
                i = y*self.iNumPlotsX + x
                val = self.continentsFrac.getHeight(x,y)
                if val <= iWaterThreshold:
                    self.plotTypes[i] = PlotTypes.PLOT_OCEAN
                else:
                    hillVal = self.hillsFrac.getHeight(x,y)
                    if ((hillVal >= iHillsBottom1 and hillVal <= iHillsTop1) or (hillVal >= iHillsBottom2 and hillVal <= iHillsTop2)):
                        peakVal = self.peaksFrac.getHeight(x,y)
                        if (peakVal <= iPeakThreshold):
                            self.plotTypes[i] = PlotTypes.PLOT_PEAK
                        else:
                            self.plotTypes[i] = PlotTypes.PLOT_HILLS
                    else:
                        self.plotTypes[i] = PlotTypes.PLOT_LAND

        if shift_plot_types:
            self.shiftPlotTypes()

        return self.plotTypes

class ISHintedWorld(CvMapGeneratorUtil.HintedWorld, ISFractalWorld):
    def __doInitFractal(self):
        self.shiftHintsToMap()
        
        # don't call base method, this overrides it.
        size = len(self.data)
        minExp = min(self.fracXExp, self.fracYExp)
        iGrain = None
        for i in range(minExp):
            width = (1 << (self.fracXExp - minExp + i))
            height = (1 << (self.fracYExp - minExp + i))
            if not self.iFlags & CyFractal.FracVals.FRAC_WRAP_X:
                width += 1
            if not self.iFlags & CyFractal.FracVals.FRAC_WRAP_Y:
                height += 1
            if size == width*height:
                iGrain = i
        assert(iGrain != None)
        iFlags = self.map.getMapFractalFlags()
        self.continentsFrac.fracInitHints(self.iNumPlotsX, self.iNumPlotsY, iGrain, self.mapRand, iFlags, self.data, self.fracXExp, self.fracYExp)

    def generatePlotTypes(self, water_percent=-1, shift_plot_types=False):
        for i in range(len(self.data)):
            if self.data[i] == None:
                self.data[i] = self.mapRand.get(48, "Generate Plot Types PYTHON")
        
        self.__doInitFractal()
        if (water_percent == -1):
            numPlots = len(self.data)
            numWaterPlots = 0
            for val in self.data:
                if val < 192:
                    numWaterPlots += 1
            water_percent = int(100*numWaterPlots/numPlots)
        
        # Call superclass
        return ISFractalWorld.generatePlotTypes(self, water_percent, shift_plot_types)

def generatePlotTypes():
    global hinted_world
    gc = CyGlobalContext()
    map = CyMap()
    mapRand = gc.getGame().getMapRand()
    
    NiTextOut("Setting Plot Types (Inland Bridge) ...")
    
    hinted_world = ISHintedWorld(8, 4)
    
    for x in range(hinted_world.w): 
        for y in range(hinted_world.h): 
            # Solid Land Borders
            if (x == 0 or x == 8 or y == 0 or y == 4):
                val = 240 + mapRand.get(10, "Plot Types - Borders")
                hinted_world.setValue(x, y, val)
            # Bridge
            elif (x == 4):
                val = 230 + mapRand.get(20, "Plot Types - Bridge")
                hinted_world.setValue(x, y, val)
            # Corners
            elif (x == 1 or x == 7 ):
                val = 180 + mapRand.get(55, "Plot Types - Corners")
                hinted_world.setValue(x, y, val)
            # Seas
            else:
                val = 50 + mapRand.get(25, "Plot Types - Seas")
                hinted_world.setValue(x, y, val)

    hinted_world.buildAllContinents()
    plotTypes = hinted_world.generatePlotTypes(water_percent=28)
    
    # ENFORCE LAND EDGES
    # We iterate through the final plot array and force edges to PLOT_LAND
    iW = map.getGridWidth()
    iH = map.getGridHeight()
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
            lat = 0.08 + 0.48 * lat
        elif iLatOption == 1 and iTiltOption == 0:
            lat = 0.03 + 0.54 * lat
        else:
            lat = 0.03 + 0.56 * lat
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
        lat = 0.03 + 0.56 * lat
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
                msg = "Swapped: " + str(target_name)
                if replace_name: msg += " -> " + str(replace_name)
                self.engine.addSign(pPlot, -1, msg)

    def place_balanced_team_resource(self, bonus_name):
        """Calculates team requirements and places them with signs."""
        global bTeamPlacement, teamHalfMap, northThreshold, southThreshold
        
        iBonus = self._bonus_id(bonus_name)
        
        # Group players to calculate N
        teamSizes = {}
        for i in range(self.gc.getMAX_CIV_PLAYERS()):
            pPlayer = self.gc.getPlayer(i)
            if pPlayer.isEverAlive():
                tID = pPlayer.getTeam()
                if not teamSizes.has_key(tID): teamSizes[tID] = 0
                teamSizes[tID] += 1

        sortedTeams = teamHalfMap.keys()
        sortedTeams.sort()

        for tID in sortedTeams:
            region = teamHalfMap[tID]
            # Formula: 1-3=1, 4-5=2, 6=3...
            count = teamSizes[tID] / 2
            if count < 1: count = 1
            
            # Region Bounds
            xMin, xMax = 0, self.iW - 1
            yMin, yMax = 0, self.iH - 1
            if region == 0:   yMin = northThreshold
            elif region == 1: yMax = southThreshold - 1
            elif region == 10: xMax = int(self.iW * 0.3); yMax = int(self.iH * 0.3)
            elif region == 11: xMin = int(self.iW * 0.7); yMax = int(self.iH * 0.3)
            elif region == 12: xMax = int(self.iW * 0.3); yMin = int(self.iH * 0.7)
            elif region == 13: xMin = int(self.iW * 0.7); yMin = int(self.iH * 0.7)

            # Collect Candidates
            natural, forced = [], []
            for x in range(xMin, xMax + 1):
                for y in range(yMin, yMax + 1):
                    pPlot = self.map.plot(x, y)
                    if pPlot.isWater() or pPlot.isPeak() or pPlot.isStartingPlot(): continue
                    if pPlot.getBonusType(-1) != -1: continue
                    
                    if pPlot.canHaveBonus(iBonus, True):
                        natural.append(pPlot)
                    else:
                        forced.append(pPlot)

            # Shuffle candidates
            for lst in [natural, forced]:
                for i in range(len(lst) - 1, 0, -1):
                    j = self.dice.get(i + 1, "Resource Shuffle")
                    lst[i], lst[j] = lst[j], lst[i]
            
            # Placement
            placed = 0
            # Try natural first, then forced
            total_candidates = natural + forced
            for pPlot in total_candidates:
                if placed < count:
                    pPlot.setBonusType(iBonus)
                    # If this was a forced plot (not natural), clear feature
                    if not pPlot.canHaveBonus(iBonus, False):
                        pPlot.setFeatureType(FeatureTypes.NO_FEATURE, -1)
                    
                    # Place Debug Sign
                    self.engine.addSign(pPlot, -1, "Balanced " + str(bonus_name))
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
        rm.swap_resources("BONUS_IVORY", "BONUS_FUR")
        rm.swap_resources("BONUS_STONE", "BONUS_COPPER")
        rm.swap_resources("BONUS_MARBLE", "BONUS_SILVER")
        # 2. Place Balanced: Bonus per team region
        rm.place_balanced_team_resource("BONUS_IVORY")
        rm.place_balanced_team_resource("BONUS_STONE")
        rm.place_balanced_team_resource("BONUS_MARBLE")

    # Finalize by calling the engine's default extras (like Goody Huts)
    CyPythonMgr().allowDefaultImpl()


