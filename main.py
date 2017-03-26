import sip
# Do this before you import PyQt
sip.setapi('QString', 2)
from PyQt4.QtCore import QThread
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import sys # We need sys so that we can pass argv to QApplication
import pafy
	
from pprint import pprint
import user_interface as UI
import settingsUI as settingsUI


class MainApp(QMainWindow, QStandardItemModel, UI.Ui_MainWindow, settingsUI.Ui_Form):

	def __init__(self):

		super(self.__class__, self).__init__()
		self.setupUi(self) 
		#print QStyleFactory.keys() #diff styles
		QApplication.setStyle(QStyleFactory.create("plastique"))
		self.urlArea.returnPressed.connect(self.get_data)
		self.getButton.clicked.connect(self.get_data)
		self.downloadButton.clicked.connect(self.download_data)
		self.downloadButton.setEnabled(False)
		self.actionSettings.triggered.connect(self.show_settings)
		self.progressBar.setRange(0,1)

	def show_settings(self):
		#self.setupSettingsUi(self)
		pass
        
	def get_data(self):
		self.progressBar.setRange(0,0)
		url = self.urlArea.displayText()
		self.getThread = getData_Thread(url)
		self.connect(self.getThread, SIGNAL("finished()"), self.notify_fetched_data)
		self.connect(self.getThread, SIGNAL("started()"), self.updateStatusBar)
		self.connect(self.getThread,SIGNAL("getPafyObject(PyQt_PyObject)"), self.get_PafyObject)
		self.connect(self.getThread,SIGNAL("update_VideoData(PyQt_PyObject)"), self.update_VideoData)
		self.connect(self.getThread,SIGNAL("update_AudioData(PyQt_PyObject)"), self.update_AudioData)
		self.connect(self.getThread,SIGNAL("update_FullData(PyQt_PyObject)"), self.update_FullData)
		self.getThread.start()			

		#self.audioQualityComboBox.addItems(resolutionList)

	def get_PafyObject(self,pfObject):

		#print type(pfObject)
		self.pfObject = pfObject
		#print type(self.pfObject)


	def update_FullData(self, fullData):
		#pass
		self.YouTubeData = fullData


	def download_data(self):
		self.progressBar.setRange(0,100)
		audio_selected_user = str(self.audioQualityComboBox.currentText())
		video_selected_user = str(self.videoQualityComboBox.currentText())
		

		audio_selected_bitrate = audio_selected_user.split(":")[0]
		audio_selected_extension = audio_selected_user.split(":")[1]
		video_selected_resolution = video_selected_user.split(":")[0]
		video_selected_extension = video_selected_user.split(":")[1]

		print audio_selected_bitrate +"    "+video_selected_resolution
		for item in self.pfObject.allstreams:
			if item.mediatype == 'audio':	
				if item.bitrate == audio_selected_bitrate and item.extension == audio_selected_extension :
					print item
					item.download(quiet=True, callback=self.mycb)

			if item.mediatype == 'video':
				if item.resolution == video_selected_resolution and item.extension == video_selected_extension :
					print item
					item.download(quiet=True, callback=self.mycb)

	def mycb(self, total, recvd, ratio, rate, eta):
		percentage = int(ratio*100)
		print "Completed - "+str(percentage)
		self.progressBar.setValue(percentage)
		self.statusbar.showMessage("Total Size: "+str(total/1048576)+"MB ETA: "+str(eta)+" Speed: "+str(rate))

	def updateStatusBar(self):
		self.statusbar.showMessage("Thread Running")

	def notify_fetched_data(self):

		self.downloadButton.setEnabled(True)
		self.progressBar.setRange(0,1)
		self.statusbar.showMessage("Data Fetched")
		status = QMessageBox()
		status.setIcon(QMessageBox.Information)
		status.setWindowTitle("Success")
		status.setText("Done Fetching Data")
		status.exec_()

	def update_VideoData(self, resolutionList):

		self.videoQualityComboBox.addItems(resolutionList)

	def update_AudioData(self, bitrateList):

		self.audioQualityComboBox.addItems(bitrateList)

	def show_error_dialogue(self):
		error = QMessageBox()
		error.setIcon(QMessageBox.Critical)
		error.setWindowTitle("Error!!!")
		error.setDetailedText(str(self.errorMessage))
		error.setInformativeText("You have run into an Error...!!!")
		error.exec_()


class getData_Thread(QThread):

	mysignal = pyqtSignal(list)

	def __init__(self,url):
		 QThread.__init__(self)
		 self.url = url

	def __del__(self):
		pass

	def getYouTubeAudioData(self, pafyObj):

		dataList = []
		
		audioStreams = pafyObj.audiostreams

		for stream in audioStreams:
			streamInfo = {
						"type":"audio",
						"extension":stream.extension,
						"bitrate":stream.bitrate,
						"url":stream.url,
						"size":stream.get_filesize()
						}
			dataList.append(streamInfo)

		return dataList


	def getYouTubeVideoData(self,pafyObj):

		dataList = []
		videoStreams = pafyObj.videostreams

		for stream in videoStreams:
			streamInfo = {
						"type":"video",
						"extension":stream.extension,
						"url":stream.url,
						"size":stream.get_filesize(),
						"resolution":stream.resolution
						}
			dataList.append(streamInfo)

		return dataList



	def run(self):
		fullData = []
		resolutionList = []
		bitrateList = []
		#https://www.youtube.com/watch?v=XGH-LdR_ObY
		try:
			self.pfobj = pafy.new(self.url)
			self.emit(SIGNAL("getPafyObject(PyQt_PyObject)"), self.pfobj)
			#print type(self.pfobj.audiostreams[1])
			video_data_list = self.getYouTubeVideoData(self.pfobj)
			audio_data_list = self.getYouTubeAudioData(self.pfobj)

		except ValueError, self.e:
			self.errorMessage = self.e
			print "Error in the Entered URL: ",self.e
			self.show_error_dialogue()

		except NameError, self.e:
			self.errorMessage = self.e
			print "URL Lib Error: ",self.e
			self.show_error_dialogue()

		else:
			for videostream in video_data_list:
				size = float(videostream['size'])/1048576
				fileSize = str("%.2f"%round(size,2))+'MB'
				resolutionList.append(videostream['resolution']+':'+videostream['extension']+':'+fileSize)
				fullData.append(videostream)

			for audiostream in audio_data_list:
				size = float(audiostream['size'])/1048576
				fileSize = str("%.2f"%round(size,2))+'MB'
				bitrateList.append(audiostream['bitrate']+':'+audiostream['extension']+':'+fileSize)
				fullData.append(audiostream)

			self.emit(SIGNAL("update_VideoData(PyQt_PyObject)"), resolutionList)
			self.emit(SIGNAL("update_AudioData(PyQt_PyObject)"), bitrateList)
			self.emit(SIGNAL("update_FullData(PyQt_PyObject)"), fullData)



def main():

	app = QApplication(sys.argv) # A new instance of QApplication
	

	#adding url to clipboard as i am too lazy to copy and paste the URL again and again
	clipboard = QApplication.clipboard()
	clipboard.setText("https://www.youtube.com/watch?v=XGH-LdR_ObY")
	
	MainWindow = MainApp()                 # We set the form to be our ExampleApp (design)
	MainWindow.show()                         
	app.exec_()         


if __name__ == '__main__':              
	main()                              