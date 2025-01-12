import numpy as np
from datetime import date, datetime, timedelta
import sys
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time
from PIL import Image, ImageGrab, ImageDraw, ImageFont
from decouple import config
import dropbox

#sys.path.append('../sharedpython/')
#import upload_to_dropbox

monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
monthNamesFull = ['Jan','Feb','March','April','May','June','July','Aug','Sep','Oct','Nov','Dec']
monthLengths = [31,28,31,30,31,30,31,31,30,31,30,31]

putOnDropbox = True

missingdates = []

def padzeros(n):
	"""
	Left pad a number with zeros. 
    """
	return str(n) if n >= 10 else '0'+str(n)

def getRank(row):
	value = row[-1]
	rank = 1
	numberOfYears = len(row) 
	for i in range(numberOfYears-1):
		if row[i] < value:
			rank += 1

	return rank

def getRankString(row):
	rank = getRank(row)
	suffix = 'th'
	if rank == 1:
		suffix = 'st'
	elif rank == 2:
		suffix = 'nd'
	elif rank == 3:
		suffix = 'rd'
	
	return ('  ' if rank < 10 else '') + str(rank) + suffix

def getNextLowest(row, previousMin, previousIndex):
	min = None
	index = None
	numberOfYears = len(row) 
	for i in range(numberOfYears):
		if (min == None or row[i] < min) and (previousMin == None or row[i] > previousMin or (row[i] == previousMin and i > previousIndex)):
			min = row[i]
			index = i
	
	return min,index
	
def generateRankSummary(data, extent):
	
	lastSavedDay = getLatestDay(data)
	print(lastSavedDay)
	lastSavedYear = 2025
	date = getDateFromDayOfYear(lastSavedDay, lastSavedYear)
	
	day = lastSavedDay-1
	matrix = data[1:,1:].astype(float)
	
	filename = 'empty-image-long.png'
	im = Image.open(filename)
	im = im.convert("RGBA")
	width, height = im.size
	printimtext = ImageDraw.Draw(im)
	
	fontsize=16
	largeFontsize=17
	smallFontsize=16
	superscriptFontsize=10
	font = ImageFont.truetype("arial.ttf", fontsize)
	largeFont = ImageFont.truetype("arialbd.ttf", largeFontsize)
	smallFont = ImageFont.truetype("arialbd.ttf", smallFontsize)
	superscriptFont = ImageFont.truetype("arialbd.ttf", superscriptFontsize)	
	color = (0,0,0)
	years = 47
	
	row = matrix[:, day]
	rank = getRank(row)
	value = None
	index = None
	
	hemisphere = 'Arctic' if north else 'Antarctic'	
	printimtext.text((0, 4), 'JAXA ' + hemisphere + ' sea ice extent on ' + str(date.day) + ' ' + monthNamesFull[date.month-1], color, font=largeFont)
	verticalOffset = 34
	printimtext.text((5, verticalOffset), 'rank', color, font=smallFont)
	printimtext.text((50, verticalOffset), 'year', color, font=smallFont)
	printimtext.text((113, verticalOffset), 'extent (M km )', color, font=smallFont)
	printimtext.text((193 + (14 if extent else 0), verticalOffset-4), '2', color, font=superscriptFont)
	
	for i in range(15):
		value,index = getNextLowest(row,value,index)
		currentRank = i+1
		if i == 14 and rank > 15:
			value,index = row[-1],years-1
			currentRank = rank
		verticalOffset = 60 + 21*i
		year = 1979 + index
		if year == 2025:
			color = (255,0,0)
		else:
			color = (0,0,0)
		printimtext.text((10, verticalOffset), str(currentRank), color, font=font)
		printimtext.text((50, verticalOffset), str(year), color, font=font)
		printimtext.text((113, verticalOffset), '{:.3f}'.format(round(value,3)), color, font=font)
	hemisphere = 'arctic' if north else 'antarctic'
	saveFileName = 'jaxa-' + hemisphere + '-extent-daily-ranks-latest.png'
	im.save(saveFileName)
	print('image size', width, height)
	return saveFileName

def generateSummary(data, extent):

	lastSavedDay = getLatestDay(data)
	print(lastSavedDay)
	lastSavedYear = 2025
	lastSavedDate = getDateFromDayOfYear(lastSavedDay, lastSavedYear)
	print(lastSavedDate)

	day = lastSavedDay-1 
	matrix = data[1:,1:].astype(float)
	
	filename = 'empty-image.png'
	im = Image.open(filename)
	im = im.convert("RGBA")
	width, height = im.size
	printimtext = ImageDraw.Draw(im)
	
	fontsize=16
	largeFontsize=20
	smallFontsize=16
	superscriptFontsize=10
	font = ImageFont.truetype("arial.ttf", fontsize)
	largeFont = ImageFont.truetype("arialbd.ttf", largeFontsize)
	smallFont = ImageFont.truetype("arialbd.ttf", smallFontsize)
	superscriptFont = ImageFont.truetype("arialbd.ttf", superscriptFontsize)
	
	days = 7

	counter = 0
	dayList = []
	total = -1
	plotday = lastSavedDate + timedelta(days = 1)
	while counter <= days:
		total += 1
		plotday = plotday - timedelta(days = 1)
		if plotday in missingdates:
			continue
		dayList.append(total)
		counter += 1
	earliestDay = dayList.pop()
	dayList.reverse()
	
	previousValue = matrix[-1 if day-earliestDay >= 0 else -2, day-earliestDay]
	color = (0,0,0)
	hemisphere = 'Arctic' if north else 'Antarctic'	
	printimtext.text((37 + (12 if north else 0) + (0), 4), 'JAXA ' + hemisphere + ' sea ice extent'  + ': last ' + str(days) + ' days', color, font=largeFont)
	verticalOffset = 34
	printimtext.text((26, verticalOffset), 'date', color, font=smallFont)
	printimtext.text((113, verticalOffset), 'extent (M km )', color, font=smallFont)
	printimtext.text((193 + (14 if extent else 0), verticalOffset-4), '2', color, font=superscriptFont)
	printimtext.text((226, verticalOffset), 'daily change (km )', color, font=smallFont)
	printimtext.text((353, verticalOffset-4), '2', color, font=superscriptFont)
	printimtext.text((400, verticalOffset), 'rank', color, font=smallFont)
	

	
	counter = -1
	for offset in dayList:
		date = lastSavedDate - timedelta(days = offset)
		print('summary date: ',counter,offset,date)
		counter += 1 
		value = matrix[-1 if day-offset >= 0 else -2, day-offset]
		rank = getRankString(matrix[:, day-offset] if day-offset >= 0 else matrix[0:-1, day-offset])
		dailyDelta = round(1000*(value-previousValue))
		dailyDeltaStr = ('  ' if abs(dailyDelta) < 100 else '') + ('  ' if abs(dailyDelta) < 10 else '') + ('+' if dailyDelta >= 0 else ' ') + str(dailyDelta) + 'k' # km'
		print('last daily value',value,rank,date)
		verticalOffset = 60 + 21*counter
		if counter == days - 1:
			color = (255,0,0)
		printimtext.text((6, verticalOffset), padzeros(date.day) + ' ' + monthNames[date.month-1] + ' ' + str(date.year), color, font=font)
		printimtext.text((148, verticalOffset), '{:.3f}'.format(round(value,3)), color, font=font) #+ ' M km  '
		printimtext.text((260, verticalOffset), dailyDeltaStr, color, font=font)
		printimtext.text((370, verticalOffset), rank + ' lowest', color, font=font)		
		previousValue = value
		
	hemisphere = 'arctic' if north else 'antarctic'
	saveFileName = 'jaxa-' + hemisphere + '-extent-recent-days.png'
	im.save(saveFileName)
	print('image size', width, height)
	return saveFileName

	
def getDateFromDayOfYear(dayOfYear, year):
	for month in range(12):
		if dayOfYear <= monthLengths[month]:
			return datetime(year, month+1, dayOfYear)
		dayOfYear -= monthLengths[month]

def processAuto():
	hemisphere = "arctic" if north else "antarctic"
	hemisphereCapitalized = "Arctic" if north else "Antarctic"
	filename = 'jaxa-' + hemisphere + '-sea-ice-extent'
	tempfilename = filename + '-temp'
	
	data = loadJaxaExtentFile(filename)
	lastSavedDay = getLatestDay(data)
	print(lastSavedDay)
	downloadJaxaExtentFile(north, tempfilename)
	newValues = loadDownloadedJaxaExtentFile(tempfilename, lastSavedDay if lastSavedDay >= 59 else lastSavedDay-1)
	print(newValues)
	appendToCsvFile(newValues, filename + '.csv')
	time.sleep(3)
	data = loadJaxaExtentFile(filename)
	
	extentGraphFilename =  'jaxa-' + hemisphere + '-extent.png'
	extentAnomalyGraphFilename = 'jaxa-' + hemisphere + '-extent-anomaly.png'
	saveExtentGraph(7 if north else 0, 15 if north else 19, data, "JAXA " + hemisphereCapitalized + " sea ice extent", extentGraphFilename, 4 if north else 1)
	saveExtentGraph(-3 if north else -3, 0.1 if north else 2.5, data, "JAXA " + hemisphereCapitalized + " sea ice extent anomaly vs. 1990-2019", extentAnomalyGraphFilename, 4 if north else 2, True)
	
	extentSummary = generateSummary(data, True)
	extentRankSummary = generateRankSummary(data, True)
	
	if putOnDropbox:
		uploadToDropbox([filename + '.csv', extentGraphFilename, extentAnomalyGraphFilename, extentSummary, extentRankSummary])

def downloadJaxaExtentFile(north, localfilename):
	url = 'https://ads.nipr.ac.jp/vishop/data/SeaIceExtentGraph/seasonal_' + ('n' if north else 's') + '.csv'
	file_object = requests.get(url) 
	with open(localfilename + '.csv', 'wb') as local_file:
		local_file.write(file_object.content)	
	
def getImageFilename(date, orbit):
	return './data/' + '/VISHOP_JAXA_ICO_' + str(date.year) + padzeros(date.month) + padzeros(date.day) + '.png';
	
def downloadJaxaImage(date, orbit):
	orbitname = (orbit[0]).capitalize()
	url = 'https://ads.nipr.ac.jp/vishop/data/jaxa/data/' + str(date.year) + padzeros(date.month) + '/AM2SI' + str(date.year) + padzeros(date.month) + padzeros(date.day) + orbitname + '_ICO_NP.png'
	print(url)
	exit()
	file_object = requests.get(url)
	localfilename = getImageFilename(date, orbit)
	with open(localfilename, 'wb') as local_file:
		local_file.write(file_object.content)
		
def loadDownloadedJaxaExtentFile(filename, lastSavedDay):
	data = np.loadtxt(filename + ".csv", delimiter=",", dtype=str)
	print(data.shape)
	currentyear = data[1:,-1]
	print(currentyear.shape)
	lastDay = np.where(currentyear != '-9999')[-1][-1]
	print(lastDay)
	if lastDay > lastSavedDay:
		return (currentyear[lastSavedDay+1:lastDay+1].astype(float)/1000000.0).astype(str)
	else:
		return []

def loadJaxaExtentFile(filename):
	with open(filename + ".csv", 'r') as f:
		lines = f.readlines()
	lastRowLength = len(lines[-1].split(','))
	lines[-1] = lines[-1] + "".join([",nan"] * (366-lastRowLength))
	print('last row length', lastRowLength)
	return np.array([line.split(',') for line in lines])
	#return np.loadtxt(filename + ".csv", delimiter=",", dtype=str)
	
def getLatestDay(data):
	print(data.shape)
	currentyear = data[-1,:]
	print(currentyear.shape)
	lastDay = np.where(currentyear != 'nan')[-1][-1]
	return lastDay
	
def appendToCsvFile(data, filename):
	if len(data) == 0:
		return
	with open(filename, "a") as file:
		file.write( ',' + ','.join(data))

	
def saveExtentGraph(ymin, ymax, data, name, filename, legendpos=1, anomaly=False):
	print('inside saveRegionalPlot', name)
	fig, axs = plt.subplots(figsize=(8, 5))
	plotExtentGraph(data, axs, ymin, ymax, name, legendpos, anomaly)	
	fig.savefig(filename)
	
def plotExtentGraph(data, ax, ymin, ymax, name, legendpos=1, anomaly=False):
	print('inside printRegionalData', name, ymin, ymax)
	
	matrix = data[1:,1:].astype(float)
	print(matrix.shape)
	offset = 304

	if anomaly:
		avg = np.mean((matrix[11:41,:]), axis=0)
		avg = np.hstack((avg[offset:],avg[0:offset]))
	else:
		avg = np.zeros(365)

	matrix = np.hstack((matrix[:,offset:], np.vstack((matrix[1:,0:offset],np.full((1,offset), np.nan)))))
	if data[-1,offset+1] == 'nan':
		matrix = matrix[0:-1,:]
	dates = np.arange(0,365)
		
	ax.plot(dates, matrix[-15,:]-avg, label='2010/11', color=(0.65,0.65,0.65));
	ax.plot(dates, matrix[-14,:]-avg, label='2011/12', color=(0.44,0.19,0.63));
	ax.plot(dates, matrix[-13,:]-avg, label='2012/13', color=(0.0,0.13,0.38));
	ax.plot(dates, matrix[-12,:]-avg, label='2013/14', color=(0,0.44,0.75));
	ax.plot(dates, matrix[-11,:]-avg, label='2014/15', color=(0.0,0.69,0.94));
	ax.plot(dates, matrix[-10,:]-avg, label='2015/16', color=(0,0.69,0.31));
	ax.plot(dates, matrix[-9,:]-avg, label='2016/17', color=(0.57,0.82,0.31));
	ax.plot(dates, matrix[-8,:]-avg, label='2017/18', color=(1.0,0.75,0));
	ax.plot(dates, matrix[-7,:]-avg, label='2018/19', color=(0.9,0.4,0.05));
	ax.plot(dates, matrix[-6,:]-avg, label='2019/20', color=(1.0,0.5,0.5));
	ax.plot(dates, matrix[-5,:]-avg, label='2020/21', color=(0.58,0.54,0.33));
	ax.plot(dates, matrix[-4,:]-avg, label='2021/22', color=(0.4,0,0.2));
	ax.plot(dates, matrix[-3,:]-avg, label='2022/23', color=(0.7,0.2,0.3));
	ax.plot(dates, matrix[-2,:]-avg, label='2023/24', color=(0.6,0,0));
	ax.plot(dates, matrix[-1,:]-avg, label='2024/25', color=(1.0,0,0), linewidth=3);
	ax.set_ylabel("Sea ice extent" + (' anomaly' if anomaly else '') + " (million km$^2\!$)")
	ax.set_title(name)
	ax.legend(loc=legendpos, prop={'size': 8})
	ax.axis([0, 120, ymin, ymax])
	ax.grid(True);
	
	months = ['Nov', 'Dec', 'Jan', 'Feb']
	ax.set_xticks([0,30,61,92,120], ['', '', '', '', '']) 
	ax.xaxis.set_minor_locator(ticker.FixedLocator([15,45.5,76.5,106]))
	ax.xaxis.set_minor_formatter(ticker.FixedFormatter(months))
	ax.tick_params(which='minor', length=0)
	
def uploadToDropbox(filenames):
	dropbox_access_token = config('DROPBOX_ACCESS_TOKEN')
	app_key = config('APP_KEY')
	app_secret = config('APP_SECRET')
	oauth2_refresh_token = config('OAUTH2_REFRESH_TOKEN')
	client = dropbox.Dropbox(oauth2_access_token=dropbox_access_token,app_key=app_key,app_secret=app_secret,oauth2_refresh_token=oauth2_refresh_token)
	print("[SUCCESS] dropbox account linked")
	
	for computer_path in filenames:
		print("[UPLOADING] {}".format(computer_path))
		dropbox_path= "/" + computer_path
		client.files_upload(open(computer_path, "rb").read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
		print("[UPLOADED] {}".format(computer_path))
	
atotalarea = []
atotalextent = []

ayear = []
aday = []

auto = True

if auto:
	north = True
	processAuto()
	
	north = False
	processAuto()
	exit()
else:
	north = True
	hemisphere = "arctic" if north else "antarctic"
	hemisphereCapitalized = "Arctic" if north else "Antarctic"
	filename = 'jaxa-' + hemisphere + '-sea-ice-extent'
	tempfilename = filename + '-temp'
	
	data = loadJaxaExtentFile(filename)
	lastSavedDay = getLatestDay(data)
	print(lastSavedDay)
	downloadJaxaExtentFile(north, tempfilename)
	newValues = loadDownloadedJaxaExtentFile(tempfilename, lastSavedDay if lastSavedDay >= 59 else lastSavedDay-1)
	print(newValues)
	appendToCsvFile(newValues, filename + '.csv')
	time.sleep(3)
	data = loadJaxaExtentFile(filename)
	
	extentGraphFilename =  'jaxa-' + hemisphere + '-extent.png'
	extentAnomalyGraphFilename = 'jaxa-' + hemisphere + '-extent-anomaly.png'
	saveExtentGraph(7 if north else 0, 15 if north else 19, data, "JAXA " + hemisphereCapitalized + " sea ice extent", extentGraphFilename, 4 if north else 1)
	saveExtentGraph(-3 if north else -3, 0.1 if north else 2.5, data, "JAXA " + hemisphereCapitalized + " sea ice extent anomaly vs. 1990-2019", extentAnomalyGraphFilename, 4 if north else 2, True)
	
	extentSummary = generateSummary(data, True)
	extentRankSummary = generateRankSummary(data, True)
	
	if putOnDropbox:
		uploadToDropbox([filename + '.csv', extentGraphFilename, extentAnomalyGraphFilename, extentSummary, extentRankSummary])	