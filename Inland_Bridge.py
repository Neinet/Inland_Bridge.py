#
#	FILE:	 Inland_Bridge.py
#	AUTHOR:	 Aineias the Stymphalian
#	PURPOSE: Adapted from Bob Thomas (Sirian)'s Inland_Sea.py. Features several multiplayer-friendly customizations.

from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil
import sys
from CvMapGeneratorUtil import MultilayeredFractal
import math
from CvMapGeneratorUtil import BonusBalancer
balancer = BonusBalancer()

# Cache for starting plots
_START_PLOT_MAP = None

def debugLog(msg):
	"Write message to PythonDbg.log"
	try:
		CyPythonMgr().logMsg(msg)
	except:
		print msg	# fallback

def getDescription():
	desc = "Inland_Sea.py with a center bridge and customizations intended for multiplayer teamer games."
	desc += "Recommended sizes: Tiny for 2v2, Small for 3v3, Standard for 4v4."
	return desc

def isAdvancedMap():
	"This map should show up in simple mode"
	return 1

def getNumCustomMapOptions():
	return 11

def getCustomMapOptionName(argsList):
	[iOption] = argsList
	if iOption == 0:
		return "Climate Details"
	elif iOption == 1:
		return "Hemisphere Option"
	elif iOption == 2:
		return "Axial Tilt"
	elif iOption == 3:
		return "World Wrap"
	elif iOption == 4:
		return "Geography"
	elif iOption == 5:
		return "Islands"
	elif iOption == 6:
		return "Two-tile Coasts"
	elif iOption == 7:
		return "Team Start"
	elif iOption == 8:
		return "Teamer Resource Balancing"
	elif iOption == 9:
		return "Debug Signs"
    elif iOption == 10:
    		return "Land Food Across Map"
    elif iOption == 11:
        	return "Reveal Start Area Radius"
	return ""

def getNumCustomMapOptionValues(argsList):
	[iOption] = argsList
	if iOption == 0: return 2 # Climate Details
	elif iOption == 1: return 2 # Latitude
	elif iOption == 2: return 3 # Axial Tilt
	elif iOption == 3: return 3 # World Wrap
	elif iOption == 4: return 6 # Geography
	elif iOption == 5: return 2 # Islands
	elif iOption == 6: return 2 # Two-tile Coasts
	elif iOption == 7: return 2 # Team Start (Start Together or Disabled)
	elif iOption == 8: return 2 # Semistrategic resources
	elif iOption == 9: return 2 # Debug Signs
	elif iOption == 10: return 4 # Land Food Across Map
	elif iOption == 11: return 4  # Radius
	return 0

def getCustomMapOptionDescAt(argsList):
	[iOption, iSelection] = argsList
	if iOption == 0: 
		if iSelection == 0: return "Default Inland_Sea"
		return "Natural"
	elif iOption == 1:
		if iSelection == 0: return "Both Hemispheres"
		return "Single Hemisphere"
	elif iOption == 2:
		if iSelection == 0: return "Disabled"
		elif iSelection == 1: return "90 Degrees"
		return "45 Degrees"
	elif iOption == 3: # Wrap
		if iSelection == 0: return "Flat"
		elif iSelection == 1: return "Wrap X"
		return "Wrap X & Y"
	elif iOption == 4: # Geography
		if iSelection == 0: return "Two Seas"
		elif iSelection == 1: return "Infinity"
		elif iSelection == 2: return "Hourglass"
		elif iSelection == 3: return "Two Seas (corner seas)"
		elif iSelection == 4: return "Two Shores (E-W)"
		return "Two Shores (N-S)"
	elif iOption == 5: # Islands
		if iSelection == 0: return "Disabled"
		return "Enabled"
	elif iOption == 6: # Two-tile Coasts
		if iSelection == 0: return "Enabled"
		return "Disabled"
	elif iOption == 7: # Team Start
		if iSelection == 0: return "Start Together"
		return "Disabled"
	elif iOption == 8: # TeamerBalancing
		if iSelection == 0: return "Disabled"
		return "Enabled"
	elif iOption == 9: # Debug Signs
		if iSelection == 0: return "Disabled"
		return "Enabled"
	elif iOption == 10: # Land Food Across Map
		if iSelection == 0: return "Disabled"
		elif iSelection == 1: return "1 per 4x4 tiles"
		elif iSelection == 2: return "1 per 5x5 tiles"
		return "1 per 6x6 tiles"
	elif iOption == 11:
	    if iSelection == 0: return "Disabled"
	    elif iSelection == 1: return "Radius 2"
	    elif iSelection == 2: return "Radius 3"
	    return "Radius 4"
	return ""

def getCustomMapOptionDefault(argsList):
	[iOption] = argsList
	if iOption == 0: # Climate Details: Natural
		return 1
	elif iOption == 1: # Latitude: Both
		return 0
	elif iOption == 2: # Axial Tilt: 
		return 1
	elif iOption == 3: # Wrap
		return 0
	elif iOption == 4: # Geography: Two Seas
		return 0
	elif iOption == 5: # Islands: On
		return 1
	elif iOption == 6: # Two-tile Coasts
		return 0
	elif iOption == 7: # Team Start:
		return 0
	elif iOption == 8: # TeamerBalancing
		return 1
	elif iOption == 9: # Debug Signs
		return 0
	elif iOption == 10: # Land Food Across Map
		return 2
	elif iOption == 11: # default = Disabled
		return 0  
	return 0

########################################
# Starting Plot
########################################

# Global variables for Team Start
bTeamPlacement = False
teamHalfMap = {}
northThreshold = 0	 # y >= this is north
southThreshold = 0	 # y < this is south
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
	teamStartOption = map.getCustomMapOption(7)
	geographyOption = map.getCustomMapOption(4)

	bTeamPlacement = False
	teamHalfMap.clear()

	# We only handle team placement for 2, 3, or 4 teams
	if teamStartOption == 0 and (numTeams >= 2 and numTeams <= 4):
		bTeamPlacement = True
		iH = map.getGridHeight()
		
		# 1. Define region pool based on team count
		if numTeams == 2:
			if geographyOption == 4:
				regions = [2, 3] # 2=West, 3=East
			else:
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

def _get_team_region_bounds(region, iW, iH):
	xMin, xMax = 2, iW - 2
	yMin, yMax = 2, iH - 2
	iEdgeBuffer = 3

	if region == 0:
		yMin = northThreshold
		yMax = iH - 1 - iEdgeBuffer
	elif region == 1:
		yMin = iEdgeBuffer
		yMax = southThreshold
	elif region == 2:
		xMax = int(iW * 0.2)
	elif region == 3:
		xMin = int(iW * 0.8)
	elif region == 10 or region == 11:
		yMax = int(iH * 0.3)
	elif region == 12 or region == 13:
		yMin = int(iH * 0.7)

	if region == 10 or region == 12:
		xMax = int(iW * 0.3)
	elif region == 11 or region == 13:
		xMin = int(iW * 0.7)

	if xMin < 4: xMin = 4
	if xMax > iW - 5: xMax = iW - 5
	if region == 0 or region == 1:
		if yMin < 0: yMin = 0
		if yMax > iH - 1: yMax = iH - 1
		if yMin > yMax:
			yMin = yMax
	else:
		if yMin < 2: yMin = 2
		if yMax > iH - 3: yMax = iH - 3

	return (xMin, xMax, yMin, yMax)

def _get_largest_land_area_in_bounds(map, xMin, xMax, yMin, yMax):
	areaCounts = {}
	bestAreaID = -1
	bestCount = 0

	for x in range(xMin, xMax + 1):
		for y in range(yMin, yMax + 1):
			pPlot = map.plot(x, y)
			if pPlot.isWater() or pPlot.isPeak(): continue
			iArea = pPlot.getArea()
			if not areaCounts.has_key(iArea):
				areaCounts[iArea] = 0
			areaCounts[iArea] += 1
			if areaCounts[iArea] > bestCount:
				bestCount = areaCounts[iArea]
				bestAreaID = iArea

	return bestAreaID

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

	for tID in sortedTeams:
		teamPlayers = teamPlayersMap[tID]
		numInTeam = len(teamPlayers)
		region = teamHalfMap.get(tID, -1)
		(teamXMin, teamXMax, teamYMin, teamYMax) = _get_team_region_bounds(region, iW, iH)
		teamAreaID = _get_largest_land_area_in_bounds(map, teamXMin, teamXMax, teamYMin, teamYMax)

		if region == 0 or region == 1:
			availXMin = teamXMin
			availXMax = teamXMax
			availYMin = teamYMin
			availYMax = teamYMax
		else:
			availXMin = teamXMin + 3
			availXMax = teamXMax - 3
			availYMin = teamYMin + 3
			availYMax = teamYMax - 3
		if availXMin > availXMax:
			availXMin = teamXMin
			availXMax = teamXMax
		if availYMin > availYMax:
			availYMin = teamYMin
			availYMax = teamYMax
		if availXMin < 0: availXMin = 0
		if availXMax > iW - 1: availXMax = iW - 1
		if availYMin < 0: availYMin = 0
		if availYMax > iH - 1: availYMax = iH - 1
		
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
			xMin, xMax = availXMin, availXMax
			yMin, yMax = availYMin, availYMax

			sliceIdx = sliceOrder[i]
			fullXMin, fullXMax = xMin, xMax
			fullYMin, fullYMax = yMin, yMax
			if region == 2 or region == 3:
				sliceHeight = (availYMax - availYMin) / numInTeam
				fullYMin = availYMin + (sliceIdx * sliceHeight)
				fullYMax = fullYMin + sliceHeight
				fullXMin = availXMin
				fullXMax = availXMax
				xMin = fullXMin
				xMax = fullXMax
				yMin = fullYMin
				yMax = fullYMax
				if sliceHeight > 8:
					iSliceMargin = 4
					yMin = fullYMin + iSliceMargin
					yMax = fullYMax - iSliceMargin
			else:
				sliceWidth = (availXMax - availXMin) / numInTeam
				fullXMin = availXMin + (sliceIdx * sliceWidth)
				fullXMax = fullXMin + sliceWidth
				if fullXMin == teamXMin:
					fullXMin += 3
				if fullXMax == teamXMax:
					fullXMax -= 3
				fullYMin = availYMin
				fullYMax = availYMax
				xMin = fullXMin
				xMax = fullXMax
				yMin = fullYMin
				yMax = fullYMax
				if sliceWidth > 8:
					iSliceMargin = 4
					xMin = fullXMin + iSliceMargin
					xMax = fullXMax - iSliceMargin

			# Clamp without adding overlap between teammate slices.
			if xMin < 0: xMin = 0
			if xMax > iW - 1: xMax = iW - 1
			if yMin < 0: yMin = 0
			if yMax > iH - 1: yMax = iH - 1
			if fullXMin < 0: fullXMin = 0
			if fullXMax > iW - 1: fullXMax = iW - 1
			if fullYMin < 0: fullYMin = 0
			if fullYMax > iH - 1: fullYMax = iH - 1

			searchBoxes = [(xMin, xMax, yMin, yMax)]
			if region == 2 or region == 3:
				if fullXMin != xMin or fullXMax != xMax or fullYMin != yMin or fullYMax != yMax:
					searchBoxes.append((fullXMin, fullXMax, fullYMin, fullYMax))

			# 3. Best Plot Search
			plotAssigned = False
			for (searchXMin, searchXMax, searchYMin, searchYMax) in searchBoxes:
				currentMinDist = 10
				while currentMinDist >= 5 and not plotAssigned:
					bestVal, bestPlot = -1, None
					for x in range(searchXMin, searchXMax + 1):
						for y in range(searchYMin, searchYMax + 1):
							pPlot = map.plot(x, y)
							if pPlot.isWater() or pPlot.isPeak(): continue
							if teamAreaID != -1 and pPlot.getArea() != teamAreaID: continue
							
							tooClose = False
							for (ax, ay) in assigned_plots:
								if plotDistance(x, y, ax, ay) < currentMinDist:
									tooClose = True
									break
							if tooClose: continue
							
							val = pPlot.getFoundValue(playerID)
							if region == 2 or region == 3:
								iEdgeDist = min(y - fullYMin, fullYMax - y)
								if iEdgeDist < 0: iEdgeDist = 0
								val -= (10 - min(10, iEdgeDist)) * 8
							elif region == 0 or region == 1:
								iEdgeDist = min(x - fullXMin, fullXMax - x)
								if iEdgeDist < 0: iEdgeDist = 0
								val -= (10 - min(10, iEdgeDist)) * 8
							if val > bestVal:
								bestVal, bestPlot = val, pPlot
					
					if bestPlot is not None:
						assignments[playerID] = map.plotNum(bestPlot.getX(), bestPlot.getY())
						assigned_plots.append((bestPlot.getX(), bestPlot.getY()))
						plotAssigned = True
					else:
						currentMinDist -= 1
				if plotAssigned: break
			
			# Emergency Fallback
			if not plotAssigned:
				for x in range(fullXMin, fullXMax + 1):
					for y in range(fullYMin, fullYMax + 1):
						pPlot = map.plot(x, y)
						if not pPlot.isWater() and not pPlot.isPeak():
							if teamAreaID != -1 and pPlot.getArea() != teamAreaID: continue
							tooClose = False
							for (ax, ay) in assigned_plots:
								if plotDistance(x, y, ax, ay) < 5:
									tooClose = True
									break
							if tooClose: continue
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
	if numPlrs	<= 18:
		return -95
	else:
		return -50

########################################
# Map Properties
########################################
def getWrapX():
	map = CyMap()
	return (map.getCustomMapOption(3) == 1 or map.getCustomMapOption(3) == 2)

def getWrapY():
	map = CyMap()
	return (map.getCustomMapOption(3) == 2)
	

def getTopLatitude():
	return 60
def getBottomLatitude():
	return -60

def getGridSize(argsList):
	"Because this is such a land-heavy map, override getGridSize() to make the map smaller"
	grid_sizes = {
		WorldSizeTypes.WORLDSIZE_DUEL:		(6,4),
		WorldSizeTypes.WORLDSIZE_TINY:		(8,5),
		WorldSizeTypes.WORLDSIZE_SMALL:		(10,6),
		WorldSizeTypes.WORLDSIZE_STANDARD:	(12,7),
		WorldSizeTypes.WORLDSIZE_LARGE:		(13,8),
		WorldSizeTypes.WORLDSIZE_HUGE:		(14,9),
	}

	if (argsList[0] == -1): # (-1,) is passed to function on loads
		return []
	[eWorldSize] = argsList
	return grid_sizes[eWorldSize]



########################################
# Plot Generation
########################################
class GeometricMultiFractal(CvMapGeneratorUtil.MultilayeredFractal):
	"""
	Fractal generator supporting geometric masking and rotation.
	Shapes: RECT, ELLIPSE, ISOTRI.
	"""
	def generatePlotsByRegion(self, region_data):
		sea = 0 
		
		# Define Terrain Profiles: (HillDensity%, PeakDensity%_of_Hills)
		terrain_profiles = {
			"flat":			(15, 1),
			"plateau":		(60, 25),
			"highland":		(75, 40),
			"alpine":		(95, 70),
			"default":		(30, 20)
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

def countTwoShoresLand(plotTypes, iW, iH, geography_opt):
	counts = {}
	counts["side_a"] = 0
	counts["side_b"] = 0

	for x in range(iW):
		for y in range(iH):
			i = y * iW + x
			if plotTypes[i] == PlotTypes.PLOT_OCEAN:
				continue
			if geography_opt == 4: # Two Shores (E-W)
				if x < (iW / 2):
					counts["side_a"] += 1
				else:
					counts["side_b"] += 1
			else: # Two Shores (N-S)
				if y < (iH / 2):
					counts["side_a"] += 1
				else:
					counts["side_b"] += 1

	return counts

def getTwoShoresLandBalanceScore(counts):
	iTotal = counts["side_a"] + counts["side_b"]
	if iTotal == 0:
		return 0

	iScoreA = abs(((counts["side_a"] * 2 * 10000) / iTotal) - 10000)
	iScoreB = abs(((counts["side_b"] * 2 * 10000) / iTotal) - 10000)
	if iScoreA > iScoreB:
		return iScoreA
	return iScoreB

def isTwoShoresLandBalanceAcceptable(counts):
	iTotal = counts["side_a"] + counts["side_b"]
	if iTotal == 0:
		return True

	# +/- 3%, matching Teamer_Hemispheres.py.
	if counts["side_a"] * 2 * 100 < iTotal * 97:
		return False
	if counts["side_a"] * 2 * 100 > iTotal * 103:
		return False
	if counts["side_b"] * 2 * 100 < iTotal * 97:
		return False
	if counts["side_b"] * 2 * 100 > iTotal * 103:
		return False
	return True

def printTwoShoresLandBalance(iAttempt, counts, bAccepted, geography_opt):
	sStatus = "rejected"
	sLabelA = "west"
	sLabelB = "east"
	if bAccepted:
		sStatus = "accepted"
	if geography_opt == 5:
		sLabelA = "south"
		sLabelB = "north"

	print "IB two shores land balance attempt %d %s" % (iAttempt, sStatus)
	print "  %s land: %d" % (sLabelA, counts["side_a"])
	print "  %s land: %d" % (sLabelB, counts["side_b"])

def generatePlotTypes():
	"""Specify map regions here."""
	NiTextOut("Setting Plot Types (Python Central Plains) ...")
	
	global _START_PLOT_MAP, _DEBUG_REGIONS
	_START_PLOT_MAP = None

	gc = CyGlobalContext()
	m = CyMap()
	climate = m.getClimate()
	
	peak_opt = m.getCustomMapOption(1)
	geography_opt = m.getCustomMapOption(4)
	island_opt = m.getCustomMapOption(5)
	iRawSeaLevelChange = gc.getSeaLevelInfo(m.getSeaLevel()).getSeaLevelChange()
	fSeaSizeChange = 0.0
	iWaterPercentChange = 0
	if iRawSeaLevelChange > 0:
		fSeaSizeChange = 0.06
		iWaterPercentChange = -10
	elif iRawSeaLevelChange < 0:
		fSeaSizeChange = -0.08
	
	regions = []
	base_regions = []
	additional_regions = []
	island_regions = []
	
	sizekey = m.getWorldSize()
	sizevalues = {
		WorldSizeTypes.WORLDSIZE_DUEL:		(3,2,1),
		WorldSizeTypes.WORLDSIZE_TINY:		(3,2,1),
		WorldSizeTypes.WORLDSIZE_SMALL:		(4,2,1),
		WorldSizeTypes.WORLDSIZE_STANDARD:	(4,2,1),
		WorldSizeTypes.WORLDSIZE_LARGE:		(5,2,1),
		WorldSizeTypes.WORLDSIZE_HUGE:		(5,2,1)
	}
	(ScatterGrain, BalanceGrain, GatherGrain) = sizevalues[sizekey]
	ZeroGrain = 0

	# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
	regions = [
			("Rect3", "Rect", 0.500, 0.5, 1.000, 1.000, 0, "default", BalanceGrain, ScatterGrain+1, 0),
		]
	if geography_opt == 0 or geography_opt == 3: # Two Seas / (Corner seas)
		bEnforceLandEdge = 1
		# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
		base_regions = [
			("Ellipse_Sea_R_BG", "Ellipse", 0.730, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, ScatterGrain, 100),
			("Ellipse_Sea_R", "Ellipse", 0.730, 0.5, 0.4 + fSeaSizeChange, 0.5 + fSeaSizeChange, 0, "water", BalanceGrain, ScatterGrain, 70),
			("Ellipse_Sea_L_BG", "Ellipse", 0.270, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, ScatterGrain, 100),
			("Ellipse_Sea_L", "Ellipse", 0.270, 0.5, 0.4 + fSeaSizeChange, 0.5 + fSeaSizeChange, 0, "water", BalanceGrain, ScatterGrain, 70),
			("Bridge", "Ellipse", 0.500, 0.500, 0.170, 0.200, 0, "default", GatherGrain, ScatterGrain, 10),
		]
		if island_opt == 1: # Enabled
			# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
			island_regions = [
				("IslandsTL", "Rect", 0.270, 0.60, 0.170, 0.170, 0, "flat", ScatterGrain, ScatterGrain, 80),
				("IslandsTR", "Rect", 0.730, 0.60, 0.170, 0.170, 0, "flat", ScatterGrain, ScatterGrain, 80),
				("IslandsBL", "Rect", 0.270, 0.40, 0.170, 0.170, 0, "flat", ScatterGrain, ScatterGrain, 80),
				("IslandsBR", "Rect", 0.730, 0.40, 0.170, 0.170, 0, "flat", ScatterGrain, ScatterGrain, 80),
			]
		if geography_opt == 3:
			additional_regions = [
				("Water_NE", "Ellipse", 1.000, 1.000, 0.200, 0.200, 0, "water", BalanceGrain, ScatterGrain, 95),
				("Water_NW", "Ellipse", 0.000, 1.000, 0.200, 0.200, 0, "water", BalanceGrain, ScatterGrain, 95),
				("Water_SE", "Ellipse", 1.000, 0.000, 0.200, 0.200, 0, "water", BalanceGrain, ScatterGrain, 95),
				("Water_SE", "Ellipse", 0.000, 0.000, 0.200, 0.200, 0, "water", BalanceGrain, ScatterGrain, 95),
			]
	elif geography_opt == 1: # Infinite Sea
		bEnforceLandEdge = 1
		# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
		base_regions = [
			("Ellipse_Sea_R_BG", "Ellipse", 0.730, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, ScatterGrain, 100),
			("Ellipse_Sea_L_BG", "Ellipse", 0.270, 0.500, 0.3, 0.4, 0, "water", BalanceGrain, ScatterGrain, 100),
			("Ellipse_Sea_R", "Ellipse", 0.730, 0.500, 0.375 + fSeaSizeChange, 0.650 + fSeaSizeChange, 0, "water", BalanceGrain, ScatterGrain, 70),
			("Ellipse_Sea_L", "Ellipse", 0.270, 0.500, 0.375 + fSeaSizeChange, 0.650 + fSeaSizeChange, 0, "water", BalanceGrain, ScatterGrain, 70),
			("Bridge", "Ellipse", 0.500, 0.500, 0.170, 0.200, 0, "water", GatherGrain, ScatterGrain, 90),
		]
		if island_opt == 1: # Enabled
			# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
			island_regions = [
				("IslandsCL", "Ellipse", 0.280, 0.500, 0.170, 0.200, 0, "default", BalanceGrain, ScatterGrain, 10 + iWaterPercentChange),
				("IslandsCR", "Ellipse", 0.720, 0.500, 0.170, 0.200, 0, "default", BalanceGrain, ScatterGrain, 10 + iWaterPercentChange),
			]
	elif geography_opt == 2: # Infinite Sea# Hourglass
		bEnforceLandEdge = 0
		# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
		base_regions = [
			("Ellipse_Sea_L", "Ellipse", 0.95, 0.500, 0.500 + fSeaSizeChange*1.5, 0.850 + fSeaSizeChange*2.5, 0, "water", BalanceGrain, ScatterGrain, 90),
			("Ellipse_Sea_R", "Ellipse", 0.050, 0.500, 0.500 + fSeaSizeChange*1.5, 0.850 + fSeaSizeChange*2.5, 0, "water", BalanceGrain, ScatterGrain, 90),
			("Ellipse_small_seaL", "Ellipse", 0.250, 0.500, 0.300 + fSeaSizeChange*0.5, 0.400 + fSeaSizeChange*0.5, 0, "water", BalanceGrain, ScatterGrain, 85),
			("Ellipse_small_seaR", "Ellipse", 0.750, 0.500, 0.300 + fSeaSizeChange*0.5, 0.400 + fSeaSizeChange*0.5, 0, "water", BalanceGrain, ScatterGrain, 85),
		]
		if island_opt == 1: # Enabled
			# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%
			island_regions = [
				("IslandsTL", "Rect", 0.100, 0.650, 0.170, 0.200, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
				("IslandsTR", "Rect", 0.900, 0.650, 0.170, 0.200, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
				("IslandsBL", "Rect", 0.100, 0.350, 0.170, 0.200, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
				("IslandsBR", "Rect", 0.900, 0.350, 0.170, 0.200, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
			]
	elif geography_opt == 4: # Two Shores (EW)
		bEnforceLandEdge = 0
		base_regions =[
			("Rect_Sea_Base", "Rect", 0.500, 0.500, 0.200 + fSeaSizeChange, 1.000, 0, "water", BalanceGrain, ScatterGrain, 100),
			("Rect_Sea_Grain", "Ellipse", 0.500, 0.200, 0.400 + fSeaSizeChange, 0.800, 0, "water", BalanceGrain, ScatterGrain, 70),
			("Rect_Sea_Grain 2", "Ellipse", 0.500, 0.800, 0.400 + fSeaSizeChange, 0.800, 180, "water", BalanceGrain, ScatterGrain, 70),
		]
		if island_opt == 1: # Enabled
			island_regions = [
					("IslandsBL", "Rect", 0.4, 0.27, 0.2, 0.2, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
					("IslandsTL", "Rect", 0.4, 0.73, 0.2, 0.2, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
					("IslandsBR", "Rect", 0.6, 0.27, 0.2, 0.2, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
					("IslandsTR", "Rect", 0.6, 0.73, 0.2, 0.2, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
				]
	else: # Two Shores (NS)
		bEnforceLandEdge = 0
		base_regions = [
			("Rect_Sea_Base", "Rect", 0.500, 0.500, 1, 0.2 + fSeaSizeChange, 0, "water", BalanceGrain, ScatterGrain, 100),
			("Rect_Sea_Grain", "Ellipse", 0.2, 0.5, 0.8, 0.4 + fSeaSizeChange, 0, "water", ScatterGrain, ScatterGrain, 70),
			("Rect_Sea_Grain 2", "Ellipse", 0.8, 0.5, 0.8, 0.4 + fSeaSizeChange, 180, "water", ScatterGrain, ScatterGrain, 70),
		]
		if island_opt == 1: # Enabled
			island_regions = [
					("IslandsL", "Rect", 0.270, 0.5, 0.250, 0.250, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
					("IslandsR", "Rect", 0.730, 0.5, 0.250, 0.250, 0, "flat", ScatterGrain, ScatterGrain, 80 + iWaterPercentChange),
				]

	regions.extend(base_regions)
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
	bBalanceTwoShores = False
	if (geography_opt == 4 or geography_opt == 5) and m.getCustomMapOption(8) == 1:
		bBalanceTwoShores = True

	if bBalanceTwoShores:
		iW = m.getGridWidth()
		iH = m.getGridHeight()
		iMaxAttempts = 20
		bestPlotTypes = None
		iBestScore = -1

		for iAttempt in range(1, iMaxAttempts + 1):
			plotgen = GeometricMultiFractal()
			attemptPlotTypes = plotgen.generatePlotsByRegion(regions)
			counts = countTwoShoresLand(attemptPlotTypes, iW, iH, geography_opt)
			bAccepted = isTwoShoresLandBalanceAcceptable(counts)
			printTwoShoresLandBalance(iAttempt, counts, bAccepted, geography_opt)
			if bAccepted:
				plotTypes = attemptPlotTypes
				break

			iScore = getTwoShoresLandBalanceScore(counts)
			if iBestScore == -1 or iScore < iBestScore:
				iBestScore = iScore
				bestPlotTypes = attemptPlotTypes

		if bestPlotTypes != None and not bAccepted:
			print "IB two shores land balance fallback after %d attempts" % iMaxAttempts
			plotTypes = bestPlotTypes
	else:
		plotgen = GeometricMultiFractal()
		plotTypes = plotgen.generatePlotsByRegion(regions)
	
	# ENFORCE LAND EDGES
	if bEnforceLandEdge == 1: # Not Hourglass, Two Shores
		# We iterate through the final plot array and force edges to PLOT_LAND
		iW = m.getGridWidth()
		iH = m.getGridHeight()
		iCornerW = iW / 4
		iCornerH = iH / 4
		for x in range(iW):
			for y in range(iH):
				if x == 0 or x == iW - 1 or y == 0 or y == iH - 1:
					bSkipCorner = False
					if y == 0 or y == iH - 1:
						if x < iCornerW or x >= iW - iCornerW:
							bSkipCorner = True
					if x == 0 or x == iW - 1:
						if y < iCornerH or y >= iH - iCornerH:
							bSkipCorner = True
					if bSkipCorner:
						continue

					i = y * iW + x
					# If it's water or a peak, force it to be flat or hill
					if plotTypes[i] == PlotTypes.PLOT_OCEAN:
						plotTypes[i] = PlotTypes.PLOT_LAND
					if plotTypes[i] == PlotTypes.PLOT_PEAK:
						plotTypes[i] = PlotTypes.PLOT_HILLS

	
	return plotTypes

# -----------------------------------------------------------------------------
# Coast distance
# -----------------------------------------------------------------------------
def expandCoastToTwoTiles():
	"""Convert all water tiles within a BFC (Big Fat Cross) radius of land to coast."""
	map = CyMap()
	gc = CyGlobalContext()
	iW = map.getGridWidth()
	iH = map.getGridHeight()
	coast_id = gc.getInfoTypeForString("TERRAIN_COAST")

	# Collect all land plots
	land_plots = []
	for x in range(iW):
		for y in range(iH):
			if not map.plot(x, y).isWater():
				land_plots.append((x, y))

	# Mark water plots within BFC range
	coast_plots = set()
	for lx, ly in land_plots:
		for dx in range(-2, 3):
			for dy in range(-2, 3):
				# BFC Logic: Skip the four corner tiles of the 5x5 area
				# (where both dx and dy are 2 or -2)
				if abs(dx) == 2 and abs(dy) == 2:
					continue
				
				nx = lx + dx
				ny = ly + dy
				
				# Check bounds
				if 0 <= nx < iW and 0 <= ny < iH:
					pPlot = map.plot(nx, ny)
					if pPlot.isWater():
						coast_plots.add((nx, ny))

	# Apply coast terrain
	for x, y in coast_plots:
		map.plot(x, y).setTerrainType(coast_id, True, True)
		
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

def getClimateNoise(iX, iY):
	"Return deterministic coherent plot noise from about -1.0 to 1.0."
	map = CyMap()
	iW = map.getGridWidth()
	iH = map.getGridHeight()
	if iW <= 1: iW = 2
	if iH <= 1: iH = 2

	fX = float(iX) / (iW - 1)
	fY = float(iY) / (iH - 1)
	fTurn = 6.283185307

	fValue = math.sin((fX * 4.0 + fY * 1.5) * fTurn)
	fValue += math.sin((fX * 9.0 - fY * 5.0 + 0.37) * fTurn) * 0.50
	fValue += math.cos((fX * 15.0 + fY * 11.0 + 0.19) * fTurn) * 0.25

	return fValue / 1.75

def applyNaturalClimateDetails(iX, iY, lat, rawLat):
	"Break up tropical and polar bands while keeping mid latitudes calmer."
	map = CyMap()
	if map.getCustomMapOption(0) != 1:
		return lat

	edgeWeight = abs(rawLat - 0.5) * 2.0
	edgeWeight = edgeWeight * edgeWeight
	detail = 0.006 + (0.075 * edgeWeight)

	lat = lat + (getClimateNoise(iX, iY) * detail)

	if lat > 1.0: lat = 1.0
	if lat < 0.0: lat = 0.0
	return lat

# subclass TerrainGenerator to eliminate arctic, equatorial latitudes
class ISTerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):
	def getLatitudeAtPlot(self, iX, iY):
		map = CyMap()
		# Custom Option 1: Latitude (0=Both, 1=Single)
		# Custom Option 2: Axial Tilt (0=Disabled, 1=90 deg, 2=45 deg)
		iLatOption = map.getCustomMapOption(1)
		iTiltOption = map.getCustomMapOption(2)
		rawLat = calculateInternalLat(iX, iY)
		lat = rawLat
		# Apply the Inland Sea temperate shift
		if iLatOption == 1 and iTiltOption == 1:
			lat = 0.07 + 0.55 * lat
		elif iLatOption == 1 and iTiltOption == 0:
			lat = 0.03 + 0.55 * lat
		else:
			lat = 0.04 + 0.57 * lat
		lat = applyNaturalClimateDetails(iX, iY, lat, rawLat)
		return lat

def generateTerrainTypes():
	NiTextOut("Generating Terrain (Python Inland Sea) ...")
	terraingen = ISTerrainGenerator()
	terrainTypes = terraingen.generateTerrain()
	return terrainTypes

# subclass FeatureGenerator to eliminate arctic, equatorial latitudes
class ISFeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
	def getLatitudeAtPlot(self, iX, iY):
		rawLat = calculateInternalLat(iX, iY)
		lat = rawLat
		# Apply the Inland Sea temperate shift (0.07 to 0.63)
		lat = 0.03 + 0.60 * lat
		lat = applyNaturalClimateDetails(iX, iY, lat, rawLat)
		return lat

	def getForestVarietyAtPlot(self, iX, iY):
		lat = self.getLatitudeAtPlot(iX, iY)
		if lat < 0.40:
			return 0
		if lat >= 0.55:
			return 2
		return 1

	def addForestsAtPlot(self, pPlot, iX, iY, lat):
		if pPlot.canHaveFeature(self.featureForest):
			if self.forests.getHeight(iX, iY) >= self.iForestLevel:
				pPlot.setFeatureType(self.featureForest, self.getForestVarietyAtPlot(iX, iY))

def addFeatures():
	NiTextOut("Adding Features (Python Inland Sea) ...")
	featuregen = ISFeatureGenerator()
	featuregen.addFeatures()
	map = CyMap()
	if map.getCustomMapOption(6) == 0:
		expandCoastToTwoTiles()
	return 0

def getRiverStartCardinalDirection(argsList):
	pPlot = argsList[0]
	map = CyMap()
	geography_opt = map.getCustomMapOption(4)
	
	iX = pPlot.getX()
	iY = pPlot.getY()
	iW = map.getGridWidth()
	iH = map.getGridHeight()
	
	if geography_opt == 4: # Two Shores (EW)
		if iX < (iW * 0.5):
			return CardinalDirectionTypes.CARDINALDIRECTION_EAST
		else:
			return CardinalDirectionTypes.CARDINALDIRECTION_WEST
	elif geography_opt == 5: # Two Shores (NS)
		if iY < (iH * 0.5):
			return CardinalDirectionTypes.CARDINALDIRECTION_NORTH
		else:
			return CardinalDirectionTypes.CARDINALDIRECTION_SOUTH
	else:
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
	geography_opt = map.getCustomMapOption(4)

	CyPythonMgr().allowDefaultImpl()

	iX = pPlot.getX()
	iY = pPlot.getY()
	iW = map.getGridWidth()
	iH = map.getGridHeight()
	
	if geography_opt == 4: # Two Shores (EW)
		iCenterX = iW / 2
		if iY < (iH / 2):
			iCenterY = iH / 4
		else:
			iCenterY = (iH * 3) / 4
		return ((abs(iX - iCenterX) * 10) + (abs(iY - iCenterY) * 15))
	else:
		iCenterY = iH / 2
		if iX < (iW / 2):
			iCenterX = iW / 4
		else:
			iCenterX = (iW * 3) / 4
			
		# The X-axis gradient (30) is now much steeper than the Y-axis gradient (10).
		# This forces rivers to "fall" into the sea rather than running parallel to the shore.
		return ((abs(iX - iCenterX) * 15) + (abs(iY - iCenterY) * 10))

# -----------------------------------------------------------------------------
# Normalization overrides
# -----------------------------------------------------------------------------

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
		self.bDebugSignsEnabled = (map_obj.getCustomMapOption(9) == 1)

	def _bonus_id(self, name):
		return self.gc.getInfoTypeForString(name)

	def _bonus_name_from_id(self, iBonus):
		return self.gc.getBonusInfo(iBonus).getType()

	def _debug_sign(self, pPlot, msg):
		if not self.bDebugSignsEnabled: return
		if pPlot is None: return
		if pPlot.isNone(): return
		self.engine.addSign(pPlot, -1, msg)

	def _shuffle_list(self, source_list, log_label):
		shuffled = []
		for item in source_list:
			shuffled.append(item)

		for i in range(len(shuffled)):
			j = self.dice.get(len(shuffled), log_label)
			temp = shuffled[i]
			shuffled[i] = shuffled[j]
			shuffled[j] = temp

		return shuffled

	def _bonus_ids_from_names(self, bonusNames):
		bonusIDs = []
		for bonusName in bonusNames:
			bonusIDs.append(self._bonus_id(bonusName))
		return bonusIDs

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

	def _get_player_count_for_team(self, iTeam):
		iCount = 0
		for iPlayer in range(self.gc.getMAX_CIV_PLAYERS()):
			pPlayer = self.gc.getPlayer(iPlayer)
			if pPlayer.isEverAlive() and pPlayer.getTeam() == iTeam:
				iCount += 1
		return iCount

	def _get_team_region_plots(self, iTeam):
		global teamHalfMap, northThreshold, southThreshold

		plots = []
		if not teamHalfMap.has_key(iTeam):
			return plots

		region = teamHalfMap[iTeam]
		iWest = 0
		iEast = self.iW
		iSouth = 0
		iNorth = self.iH

		if region == 0:
			iSouth = northThreshold
		elif region == 1:
			iNorth = southThreshold
		elif region == 2:
			iEast = int(self.iW * 0.3)
		elif region == 3:
			iWest = int(self.iW * 0.7)
		elif region == 10:
			iEast = int(self.iW * 0.3)
			iNorth = int(self.iH * 0.3)
		elif region == 11:
			iWest = int(self.iW * 0.7)
			iNorth = int(self.iH * 0.3)
		elif region == 12:
			iEast = int(self.iW * 0.3)
			iSouth = int(self.iH * 0.7)
		elif region == 13:
			iWest = int(self.iW * 0.7)
			iSouth = int(self.iH * 0.7)

		for x in range(iWest, iEast):
			for y in range(iSouth, iNorth):
				pPlot = self.map.plot(x, y)
				if pPlot.isNone(): continue
				plots.append(pPlot)

		return plots

	def _get_team_start_radius_plots(self, iTeam, radius):
		plots = []
		used = {}

		if radius < 0:
			radius = 0

		for iPlayer in range(self.gc.getMAX_CIV_PLAYERS()):
			pPlayer = self.gc.getPlayer(iPlayer)
			if pPlayer.isEverAlive() and pPlayer.getTeam() == iTeam:
				pStart = pPlayer.getStartingPlot()
				if pStart and not pStart.isNone():
					sx = pStart.getX()
					sy = pStart.getY()
					for dx in range(-radius, radius + 1):
						for dy in range(-radius, radius + 1):
							nx = sx + dx
							ny = sy + dy
							if nx >= 0 and nx < self.iW and ny >= 0 and ny < self.iH:
								if plotDistance(sx, sy, nx, ny) <= radius:
									key = ny * self.iW + nx
									if not used.has_key(key):
										pPlot = self.map.plot(nx, ny)
										if not pPlot.isNone():
											used[key] = 1
											plots.append(pPlot)

		return plots

	def _present_bonus_types(self, region_plots, bonusIDs):
		wanted = {}
		for iBonus in bonusIDs:
			wanted[iBonus] = 1

		present = {}
		for pPlot in region_plots:
			iBonus = pPlot.getBonusType(-1)
			if wanted.has_key(iBonus):
				present[iBonus] = 1

		return present.keys()

	def _start_plot_lookup(self):
		startLookup = {}
		for i in range(self.gc.getMAX_CIV_PLAYERS()):
			player = self.gc.getPlayer(i)
			if player.isEverAlive():
				pStart = player.getStartingPlot()
				if pStart and not pStart.isNone():
					startLookup[(pStart.getX(), pStart.getY())] = 1
		return startLookup

	def _is_player_start_plot(self, pPlot, startLookup):
		if pPlot.isStartingPlot():
			return True
		return startLookup.has_key((pPlot.getX(), pPlot.getY()))

	def _valid_bonus_plots(self, region_plots, iBonus):
		validPlots = []
		startLookup = self._start_plot_lookup()
		for pPlot in region_plots:
			if pPlot.getBonusType(-1) != -1: continue
			if self._is_player_start_plot(pPlot, startLookup): continue
			if not pPlot.canHaveBonus(iBonus, True): continue
			validPlots.append(pPlot)
		return validPlots

	def _bonus_is_water(self, iBonus):
		bonusInfo = self.gc.getBonusInfo(iBonus)
		iCoast = self.gc.getInfoTypeForString("TERRAIN_COAST")
		iOcean = self.gc.getInfoTypeForString("TERRAIN_OCEAN")

		if iCoast != -1:
			if bonusInfo.isTerrain(iCoast):
				return True
		if iOcean != -1:
			if bonusInfo.isTerrain(iOcean):
				return True
		return False

	def _bonus_matches_plot_type(self, pPlot, iBonus):
		bonusInfo = self.gc.getBonusInfo(iBonus)

		if self._bonus_is_water(iBonus):
			return pPlot.isWater()

		if pPlot.isWater() or pPlot.isPeak():
			return False

		if pPlot.isHills():
			return bonusInfo.isHills()

		return bonusInfo.isFlatlands()

	def _is_bonus_appropriate_for_plot(self, bonus_id, pPlot):
		"""
		Checks if the bonus is physically compatible with the plot's terrain,
		topography, and feature, ignoring proximity and latitude.
		"""
		info = self.gc.getBonusInfo(bonus_id)

		if pPlot.isHills():
			if not info.isHills(): return False
		else:
			if not info.isFlatlands(): return False

		if not info.isTerrain(pPlot.getTerrainType()):
			return False

		iFeature = pPlot.getFeatureType()
		if iFeature != -1:
			if not info.isFeature(iFeature):
				return False

		return True

	def place_bonus_in_radius(self, bonus_list, iTargetCount=1, iCopies=1, radius=5):
		"""
		Ensure target bonus types from bonus_list exist near each player start.
		Uses plotDistance so diagonal radius checks match Civ's plot radius.
		"""
		if iTargetCount < 1: iTargetCount = 1
		if iCopies < 1: iCopies = 1

		ids = []
		for b in bonus_list:
			ids.append(self._bonus_id(b))

		players = []
		startLookup = self._start_plot_lookup()
		for i in range(self.gc.getMAX_CIV_PLAYERS()):
			player = self.gc.getPlayer(i)
			if player.isEverAlive():
				pStart = player.getStartingPlot()
				if pStart and not pStart.isNone():
					players.append((player.getID(), pStart.getX(), pStart.getY(), pStart.getArea()))

		for (pid, sx, sy, iStartArea) in players:
			present = {}

			for dx in range(-radius, radius + 1):
				for dy in range(-radius, radius + 1):
					nx, ny = sx + dx, sy + dy
					if 0 <= nx < self.iW and 0 <= ny < self.iH:
						if plotDistance(sx, sy, nx, ny) <= radius:
							pPlot = self.map.plot(nx, ny)
							if pPlot.getArea() != iStartArea: continue
							iBonus = pPlot.getBonusType(TeamTypes.NO_TEAM)
							if iBonus in ids:
								present[iBonus] = 1

			iPresent = len(present.keys())
			if iPresent >= iTargetCount:
				print "IB radius bonus skipped player %d. Found %d existing bonus types" % (pid, iPresent)
				continue

			missing_ids = []
			for iBonus in ids:
				if not present.has_key(iBonus):
					missing_ids.append(iBonus)

			missing_ids = self._shuffle_list(missing_ids, "IB Radius Bonus Type")
			iNeededTypes = iTargetCount - iPresent
			if iNeededTypes > len(missing_ids): iNeededTypes = len(missing_ids)

			for iType in range(iNeededTypes):
				chosen_id = missing_ids[iType]
				placed = 0

				for iCopy in range(iCopies):
					tier1_plots = []
					for dx in range(-radius, radius + 1):
						for dy in range(-radius, radius + 1):
							nx, ny = sx + dx, sy + dy
							if 0 <= nx < self.iW and 0 <= ny < self.iH:
								if plotDistance(sx, sy, nx, ny) <= radius:
									pPlot = self.map.plot(nx, ny)
									if pPlot.getArea() != iStartArea: continue
									if self._is_player_start_plot(pPlot, startLookup) or pPlot.getBonusType(-1) != -1: continue
									if pPlot.isWater() or pPlot.isPeak(): continue

									if self._is_bonus_appropriate_for_plot(chosen_id, pPlot):
										tier1_plots.append(pPlot)

					target_plot = None
					if len(tier1_plots) > 0:
						target_plot = tier1_plots[self.dice.get(len(tier1_plots), "IB Radius T1")]
					else:
						emergency_plots = []
						for dx in range(-radius, radius + 1):
							for dy in range(-radius, radius + 1):
								nx, ny = sx + dx, sy + dy
								if 0 <= nx < self.iW and 0 <= ny < self.iH:
									if plotDistance(sx, sy, nx, ny) <= radius:
										pPlot = self.map.plot(nx, ny)
										if pPlot.getArea() != iStartArea: continue
										if not pPlot.isWater() and not pPlot.isPeak() and not self._is_player_start_plot(pPlot, startLookup):
											if pPlot.getBonusType(-1) == -1:
												emergency_plots.append(pPlot)

						if len(emergency_plots) > 0:
							target_plot = emergency_plots[self.dice.get(len(emergency_plots), "IB Radius Emergency")]

					if target_plot:
						target_plot.setBonusType(chosen_id)
						bonus_name = self.gc.getBonusInfo(chosen_id).getType()
						self._debug_sign(target_plot, "IB radius " + bonus_name + " P" + str(pid))
						print "IB radius placed %s for player %d at (%d, %d)" % (bonus_name, pid, target_plot.getX(), target_plot.getY())
						placed += 1

				if placed < iCopies:
					print "IB radius placed only %d of %d copies for player %d" % (placed, iCopies, pid)

	def ensure_bonus_per_grid(self, bonusNames, iGridSize):
		if iGridSize <= 0:
			return

		bonusIDs = self._bonus_ids_from_names(bonusNames)
		bonusLookup = {}
		for iBonus in bonusIDs:
			bonusLookup[iBonus] = 1

		startLookup = self._start_plot_lookup()
		iBlocksChecked = 0
		iBlocksSatisfied = 0
		iPlaced = 0
		iBlocked = 0

		for xMin in range(0, self.iW, iGridSize):
			for yMin in range(0, self.iH, iGridSize):
				iBlocksChecked += 1
				xMax = xMin + iGridSize
				yMax = yMin + iGridSize
				if xMax > self.iW: xMax = self.iW
				if yMax > self.iH: yMax = self.iH

				iExisting = 0
				plots = []
				for x in range(xMin, xMax):
					for y in range(yMin, yMax):
						pPlot = self.map.plot(x, y)
						if bonusLookup.has_key(pPlot.getBonusType(-1)):
							iExisting += 1
						plots.append(pPlot)

				if iExisting > 0:
					iBlocksSatisfied += 1
					continue

				plots = self._shuffle_list(plots, "IB Map Food Plot Shuffle")
				shuffledBonusIDs = self._shuffle_list(bonusIDs, "IB Map Food Bonus Shuffle")
				bPlaced = False
				for pPlot in plots:
					if pPlot.getBonusType(-1) != -1: continue
					if pPlot.isWater() or pPlot.isPeak(): continue
					if self._is_player_start_plot(pPlot, startLookup): continue
					for iBonus in shuffledBonusIDs:
						if pPlot.canHaveBonus(iBonus, True):
							pPlot.setBonusType(iBonus)
							self._debug_sign(pPlot, "IB map food " + self._bonus_name_from_id(iBonus))
							iPlaced += 1
							bPlaced = True
							break
					if bPlaced:
						break

				if not bPlaced:
					iBlocked += 1

		print "IB map food scan: checked %d blocks, satisfied %d, placed %d, blocked %d" % (iBlocksChecked, iBlocksSatisfied, iPlaced, iBlocked)

	def _fallback_bonus_plots(self, region_plots, iBonus, bMatchPlotType):
		bWaterBonus = self._bonus_is_water(iBonus)
		fallbackPlots = []
		startLookup = self._start_plot_lookup()
		for pPlot in region_plots:
			if pPlot.getBonusType(-1) != -1: continue
			if self._is_player_start_plot(pPlot, startLookup): continue
			if bMatchPlotType:
				if not self._bonus_matches_plot_type(pPlot, iBonus): continue
			else:
				if bWaterBonus:
					if not pPlot.isWater(): continue
				else:
					if pPlot.isWater() or pPlot.isPeak(): continue
			fallbackPlots.append(pPlot)
		return fallbackPlots

	def _place_bonus_copies(self, region_plots, iBonus, iCopies, regionName, bonusName, iPlayerCount):
		if iCopies < 1: iCopies = 1

		validPlots = self._valid_bonus_plots(region_plots, iBonus)
		validPlots = self._shuffle_list(validPlots, "IB Region Bonus Placement")

		placed = 0
		for pPlot in validPlots:
			if placed >= iCopies: break
			pPlot.setBonusType(iBonus)
			self._debug_sign(pPlot, "IB added " + bonusName + " in " + regionName + " P" + str(iPlayerCount))
			placed += 1

		if placed < iCopies:
			print "IB using relaxed placement for %s in %s, valid plots exhausted" % (bonusName, regionName)
			relaxedPlots = self._fallback_bonus_plots(region_plots, iBonus, True)
			relaxedPlots = self._shuffle_list(relaxedPlots, "IB Relaxed Region Bonus Placement")
			for pPlot in relaxedPlots:
				if placed >= iCopies: break
				pPlot.setBonusType(iBonus)
				self._debug_sign(pPlot, "IB relaxed " + bonusName + " in " + regionName + " P" + str(iPlayerCount))
				placed += 1

		if placed < iCopies:
			print "IB using last-ditch placement for %s in %s, relaxed plots exhausted" % (bonusName, regionName)
			fallbackPlots = self._fallback_bonus_plots(region_plots, iBonus, False)
			fallbackPlots = self._shuffle_list(fallbackPlots, "IB Last Ditch Region Bonus Placement")
			for pPlot in fallbackPlots:
				if placed >= iCopies: break
				pPlot.setBonusType(iBonus)
				self._debug_sign(pPlot, "IB fallback " + bonusName + " in " + regionName + " P" + str(iPlayerCount))
				placed += 1

		return placed

	def _wipe_bonus_types_in_plots(self, region_plots, bonusIDs, regionName):
		removeLookup = {}
		for iBonus in bonusIDs:
			removeLookup[iBonus] = 1

		iRemoved = 0
		for pPlot in region_plots:
			iBonus = pPlot.getBonusType(-1)
			if removeLookup.has_key(iBonus):
				self._debug_sign(pPlot, "IB removed " + self._bonus_name_from_id(iBonus) + " in " + regionName)
				pPlot.setBonusType(-1)
				iRemoved += 1

		if iRemoved > 0:
			print "IB wiped %d listed bonuses in %s" % (iRemoved, regionName)
		return iRemoved

	def place_balanced_team_resource(self, iTeam, bonusNames, iTargetCount, iCopies, bPlaceNear=False, radius=5):
		# Replaces the listed bonus group inside one team's half-map, then
		# places a random subset back into that team region.  This keeps each
		# team supplied from the same resource group without requiring the same
		# exact bonus types on every side.
		#
		# iTeam: team id from teamHalfMap.
		# bonusNames: list of XML bonus type names eligible for this group.
		# iTargetCount: number of different bonus types to attempt for the team.
		# iCopies: number of copies to place for each selected bonus type.
		# bPlaceNear/radius: if set, place inside player start radii instead of
		# the full team half-map after wiping the full region.
		bonusIDs = self._bonus_ids_from_names(bonusNames)
		regionName = "team " + str(iTeam)
		wipeRegionName = regionName

		# Always wipe the full team region so the original map generator cannot
		# leave an uneven advantage from this bonus group behind.
		wipe_plots = self._get_team_region_plots(iTeam)
		self._wipe_bonus_types_in_plots(wipe_plots, bonusIDs, wipeRegionName)

		if bPlaceNear:
			# Semi-strategic balancing uses the tighter start radius so every
			# player on the team has practical access instead of only a remote
			# resource somewhere in the team's half-map.
			region_plots = self._get_team_start_radius_plots(iTeam, radius)
			regionName = regionName + " near starts"
		else:
			region_plots = wipe_plots
		iPlayerCount = self._get_player_count_for_team(iTeam)

		if len(region_plots) == 0:
			print "IB balance found no plots for %s" % regionName
			return 0

		bonusIDs = self._shuffle_list(bonusIDs, "IB Region Bonus Types")
		iNeeded = iTargetCount
		if iNeeded > len(bonusIDs): iNeeded = len(bonusIDs)

		# Choose up to iTargetCount different resource types from the group, then
		# place iCopies of each through the normal/relaxed/fallback placement path.
		iAttempted = 0
		for i in range(iNeeded):
			iBonus = bonusIDs[i]
			self._place_bonus_copies(region_plots, iBonus, iCopies, regionName, self._bonus_name_from_id(iBonus), iPlayerCount)
			iAttempted += 1

		# Return the number of bonus types attempted, not the number of copies
		# successfully placed.
		return iAttempted
def revealStartingArea(iRadius=3):
	gc = CyGlobalContext()
	map = CyMap()
	
	for iPlayer in range(gc.getMAX_CIV_PLAYERS()):
		pPlayer = gc.getPlayer(iPlayer)

		if not pPlayer.isEverAlive():
			continue

		pStart = pPlayer.getStartingPlot()
		if pStart is None or pStart.isNone():
			continue

		iTeam = pPlayer.getTeam()
		sx = pStart.getX()
		sy = pStart.getY()

		for dx in range(-iRadius, iRadius + 1):
			for dy in range(-iRadius, iRadius + 1):
				nx = sx + dx
				ny = sy + dy

				if nx < 0 or nx >= map.getGridWidth():
					continue
				if ny < 0 or ny >= map.getGridHeight():
					continue

				if plotDistance(sx, sy, nx, ny) <= iRadius:
					map.plot(nx, ny).setRevealed(iTeam, True, False, -1)


def normalizeAddExtras():
	gc = CyGlobalContext()
	map = CyMap()
	dice = gc.getGame().getMapRand()
	# Recalculate to ensure accurate terrain/water detection
	map.recalculateAreas()
	# Instantiate the Generalized Manager
	rm = ResourceManager(map, gc, dice)
	iRevealOption = map.getCustomMapOption(11)
	iRevealRadius = 0

	if iRevealOption == 1:
		iRevealRadius = 2
	elif iRevealOption == 2:
		iRevealRadius = 3
	elif iRevealOption == 3:
		iRevealRadius = 4
	bTeamerBalancingOption = map.getCustomMapOption(8)
	iMapFoodOption = map.getCustomMapOption(10)
	LandFoodBonus = ["BONUS_WHEAT", "BONUS_RICE", "BONUS_CORN", "BONUS_COW", "BONUS_SHEEP", "BONUS_PIG", "BONUS_DEER", "BONUS_BANANA"]
	
	# bTeamPlacement is our global variable from the start plot logic
	if bTeamPlacement and bTeamerBalancingOption == 1:
		print "PY: Teamer balancing regional resource groups..."
		
		Strategics = ["BONUS_IRON", "BONUS_COPPER", "BONUS_HORSE"]
		SemiStrategics = ["BONUS_IVORY", "BONUS_STONE", "BONUS_MARBLE"]
		PreciousMetals = ["BONUS_GOLD", "BONUS_SILVER", "BONUS_GEMS"]
		EarlyHappiness = ["BONUS_FUR", "BONUS_WINE"]
		CalendarBonus = ["BONUS_SPICES", "BONUS_SUGAR", "BONUS_BANANA", "BONUS_DYE", "BONUS_INCENSE", "BONUS_SILK"]
		WaterBonus = ["BONUS_CRAB", "BONUS_WHALE"]

		# 1. Global Swap
		rm.swap_resources("BONUS_IVORY", None)
		
		# BonusList, # Types, Count, Radius
		rm.place_bonus_in_radius(Strategics, 3, 1, radius=4)

		# 2. Place Balanced: Bonus list per team region
		sortedTeams = teamHalfMap.keys()
		sortedTeams.sort()
		for iTeam in sortedTeams:
			iPlayerCount = rm._get_player_count_for_team(iTeam)
			iRoundedDown = int(0.5*iPlayerCount)
			iRoundedUp = int(0.5*iPlayerCount + 1)
			if iRoundedDown < 1: iRoundedDown = 1
			# iTeam, BonusList, # Types, Count
			rm.place_balanced_team_resource(iTeam, CalendarBonus, 4, iRoundedDown)
			rm.place_balanced_team_resource(iTeam, PreciousMetals, 3, iRoundedUp)
			rm.place_balanced_team_resource(iTeam, EarlyHappiness, 2, iRoundedUp)
			# rm.place_balanced_team_resource(iTeam, WaterBonus, 2, iRoundedDown)
			rm.place_balanced_team_resource(iTeam, SemiStrategics, 3, iRoundedDown, bPlaceNear=True, radius=4)

	else:
		# Let the DLL handle normal extras when custom team balancing is off.
		CyPythonMgr().allowDefaultImpl()

	if iMapFoodOption != 0:
		print "PY: Inland Bridge ensuring mapwide land food bonuses..."
		rm.ensure_bonus_per_grid(LandFoodBonus, iMapFoodOption + 3)
	if iRevealRadius > 0:
		revealStartingArea(iRevealRadius)
