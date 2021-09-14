#install postgresql,pgadmin and add extension :postgis,pgrouting
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QCheckBox, QListView, QMessageBox, QWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtWidgets 
from qgis.core import Qgis

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import QgsVectorLayer,QgsProject, QgsGeometry, QgsFeature, QgsSymbol,QgsLayerTreeLayer, QgsSingleSymbolRenderer, QgsDataSourceUri,QgsCoordinateReferenceSystem

from qgis.PyQt.QtWidgets import QAction
import psycopg2
import sys 
#import traceback
import logging
import math    

import os
import time
from qgis.gui import QgsMapToolIdentifyFeature
import re, os.path

from PyQt5.QtCore import QFileInfo
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .find_path_dialog import FindPathDialog
from .route_find_dialog import routeFindDialog
import os.path

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qgis.PyQt.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QMainWindow, QSizePolicy, QWidget, QVBoxLayout, QAction, QLabel, QLineEdit, QMessageBox, QFileDialog, QFrame, QDockWidget, QProgressBar, QProgressDialog, QToolTip
from PyQt5.QtGui import QKeySequence, QIcon

from PyQt5.QtCore import QSettings, QSize, QPoint, QVariant, QFileInfo, QTimer, pyqtSignal, QObject, QItemSelectionModel, QTranslator, qVersion, QCoreApplication
from datetime import timedelta, datetime
from time import strftime
from time import gmtime
from qgis.utils import iface
from qgis.core import *
from qgis.utils import *

import shutil

#shutil.rmtree(path)
class FindPath:
    routecount = 0
    count1 = 0
    pointlistcount = 0
    pointlist = []
    routegeom = []
    sourcelist = []
    destinationlist =[]
    source = 0
    destination = 0
    val1_int = 0
    incroute = 0
    mapTool = None
    iii = 0
    lyr = ""
    edate11 = ""

    plugin_path = os.path.dirname(__file__)
    def __init__(self, iface):
        
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FindPath_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&army_data')

        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        return QCoreApplication.translate('FindPath', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):

        #icon_path = ':/plugins/army_plugin/army2.png'
        icon_path = self.plugin_path+'/'+'army2.png'
        self.add_action(
            icon_path,
            text=self.tr(u'movement capture data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&army_data'),
                action)
            self.iface.removeToolBarIcon(action)
            
    def run(self):
        try:
            connection = psycopg2.connect(user="postgres", password="postgres", host="localhost", database="project")
            cursor = connection.cursor()

            self.source = 0
            self.destination = 0
            self.count1 = 0
            halt_node = []
            halt_time = []
            vehicals = []
            vehicals_speed = []
            routenodes = []
            routeedges = []
            routegeom = []
            start_time = 0
            table_detail_list = []

            self.dlg = FindPathDialog()
            self.dlg.pushButton_addlayer.hide()

            # add logo of gui
            self.dlg.label_logo.setPixmap(QtGui.QPixmap(self.plugin_path+'/'+'bisag_n.png').scaledToWidth(120))
            #calender qdateedit
            self.dlg.dateEdit.setMinimumDate(QtCore.QDate(2021, 7, 1))
            self.dlg.dateEdit.setMaximumDate(QtCore.QDate(2023, 1, 1))
            self.dlg.dateEdit.setCalendarPopup(True)

            def onDateChanged(qDate):
                st_date = "%02d-%02d-%02d"%(qDate.year(), qDate.month(), qDate.day())
            self.dlg.dateEdit.dateChanged.connect(onDateChanged)

            #postgis node 
            pnode = QgsDataSourceUri()
            pnode.setConnection("localhost", "5432", "project", "postgres", "postgres")
            pnode.setDataSource("public", "node", "geom")
            nodelayer = QgsVectorLayer(pnode.uri(), "node", "postgres")

            def loadOpenLayersPluginMap(mapProvider, openLayersMap):

                webMenu = iface.webMenu()
                for webMenuItem in webMenu.actions(): 
                    if 'OpenLayers plugin' in webMenuItem.text():
                        openLayersMenu = webMenuItem 

                        for openLayersMenuItem in openLayersMenu.menu().actions():
                            if mapProvider in openLayersMenuItem.text(): 
                                mapProviderMenu = openLayersMenuItem 

                                for map in mapProviderMenu.menu().actions():
                                    if openLayersMap in map.text(): 
                                        map.trigger() 

                root = QgsProject.instance().layerTreeRoot()
                for child in root.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        childClone = child.clone()
                        root.insertChildNode(0, childClone)
                        root.removeChildNode(child)

            def addLayer():

                #add openstreet map 
                loadOpenLayersPluginMap('OpenStreetMap', 'OpenStreetMap')

                #postgis node 
                QgsProject.instance().addMapLayer(nodelayer)

            self.dlg.pushButton_addlayer.clicked.connect(addLayer)

            mc = self.iface.mapCanvas()
            if self.routecount == 0:
                self.lyr = nodelayer
                #self.lyr = self.iface.activeLayer()
                
            self.mapTool = QgsMapToolIdentifyFeature(mc)
            self.mapTool.setLayer(self.lyr)
            mc.setMapTool(self.mapTool) 
            

            if self.routecount == 0:
                self.dlg1 = routeFindDialog()

                self.dlg1.setWindowTitle('REPORT')
                self.dlg1.tableWidget_detail.setColumnCount(10)

                header = self.dlg1.tableWidget_detail.horizontalHeader()       
                header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
                header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
                header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
                header.setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeToContents)
                header.setSectionResizeMode(9, QtWidgets.QHeaderView.ResizeToContents)

                stylesheet = "QHeaderView::section{color:blue; border-radius:14px;}"
                self.dlg1.tableWidget_detail.setStyleSheet(stylesheet)
                self.dlg1.label_route.setStyleSheet("color: black;font-size: 18pt; ") 
                
                self.dlg1.tableWidget_detail.setHorizontalHeaderLabels(['Route','Source','Destination','Intermediate Nodes','Halt Node', 'Halt Time','Vehicle','Vehicle Speed','Starting Date/Time', 'Ending Date/Time'])
                
                self.dlg.pushButton_addlayer.setStyleSheet("color: black;font-size: 14pt;")
                self.dlg.pushButton_addlayer.setToolTip('click')
                self.dlg.pushButton_addlayer.show()
                #remove all layer
                #QgsProject.instance().removeAllMapLayers()
        
            def addTableRowdeatail(tableWidget_details, row_data):
                
                row = tableWidget_details.rowCount()
                tableWidget_details.setRowCount(row+1)
                col = 0
                
                for item in row_data:
                    cell = QTableWidgetItem(str(item))
                    tableWidget_details.setItem(row, col, cell)
                    col += 1
                    
            self.routecount = self.routecount + 1 
            name = "Route " + str(self.routecount)
            self.dlg.pushButton_addroute.setText(name)
            
            self.dlg.pushButton_addroute.setStyleSheet("color: green;font-size: 14pt; ") 

            self.dlg.pushButton_addroute.setToolTip('click')
            #QToolTip.setFont(QFont('SansSerif', 7))
            table_detail_list.append(self.routecount)

            
            def pointselection():
                my_crs=QgsCoordinateReferenceSystem(4326)
                QgsProject.instance().setCrs(my_crs)
                
                print ("pointselectiont:  ")  
                self.dlg.label_pointselect.setStyleSheet("color: brown; ") 
                self.dlg.label_pointselect.show()
                
                def onFeatureIdentified(feature):
                    aa = "select point: "+ str(feature.attributes())
                    print ("select point: "+ str(feature.attributes())) 
                    
                    nodeid = str(feature.attributes()) 
                    nodeid = nodeid.replace('[', '')
                    nodeid = nodeid.replace(']', '')
                    nodeint = int(nodeid)        
            
                    #global self.count1 
                    self.count1 = self.count1 + 1  
                    #self.doubleroute =  self.val1_int * 2

                    if(self.count1 <= 2):
                        #global source                   
                        self.pointlist.append(nodeint) 

                    if(self.count1 >= 2):
                        #global destination
                        self.source = int(self.pointlist[self.pointlistcount])    
                        self.destination = int(self.pointlist[self.pointlistcount+1])   
                        self.sourcelist.append(self.source)
                        self.destinationlist.append(self.destination)
                        self.pointlistcount = self.pointlistcount + 2
                        self.iface.actionPan().trigger()
                        
                        # print("route " + str(self.routecount))
                        # print("source" + str(self.source))
                        # print("destination" + str(self.destination))

                        self.dlg.label_pointselect.show()
                        self.dlg.label_sourcevalue.show()
                        self.dlg.label_source.show()
                        self.dlg.label_destination.show()
                        self.dlg.label_destvalue.show()
                        
                    

                        self.dlg.label_sourcevalue.setText(str(self.source))
                        self.dlg.label_destvalue.setText(str(self.destination))

                        table_detail_list.append(self.source)
                        table_detail_list.append(self.destination)
                        

                        add()
                    
                self.mapTool.featureIdentified.connect(onFeatureIdentified)    
                        
            def addnewroute():
                self.dlg.close()
                self.run()

            halt_lblAdd = []
            def addhaltlist():
                halt = self.dlg.comboBox_halt.currentText()
                duration = self.dlg.lineEdit_durationval.text()
                ht = duration
                #  hh:mm::ss to hour
                ht_hm = [int(n) for n in ht.split(":")]
                ht_hm1 = ht_hm[0] + ht_hm[1]/60.0

                
                halt_node.append(halt) 
                halt_time.append(ht_hm1) 

                halt_lblAdd.append(duration)
                # halt_time.append(duration) 

                ii = 0
                temp = ""
                for items in halt_node:
                    temp =  temp + "(" + halt_node[ii] + " - " + halt_lblAdd[ii] + ") "
                    ii = ii + 1
                self.dlg.label_haltnodelist.setText(str(temp))

            def deletehaltlist():
                del halt_node[-1]
                del halt_time[-1] 
                del halt_lblAdd[-1]
                ii = 0
                temp = ""
                for items in halt_node:
                    temp =  temp + "(" + halt_node[ii] + " - " + halt_lblAdd[ii] + ") "
                    ii = ii + 1
                self.dlg.label_haltnodelist.setText(str(temp))

            def vehiclelist():
                veh = self.dlg.comboBox_vehical.currentText()
                vehspeed = self.dlg.lineEdit_speed.text()
                vehicals.append(veh) 
                vehicals_speed.append(vehspeed)    
                ii = 0
                temp = ""
                for items in vehicals:
                    temp =  temp + "(" + vehicals[ii] + ":" + vehicals_speed[ii] + ") "
                    ii = ii + 1

                self.dlg.label_vehiclevalue.setText(str(temp))

            def deletevehiclelist():
                del vehicals[-1]
                del vehicals_speed[-1] 
                ii = 0
                temp = ""
                for items in vehicals:
                    temp =  temp + "(" + vehicals[ii] + ":" + vehicals_speed[ii] + ") "
                    ii = ii + 1

                self.dlg.label_vehiclevalue.setText(str(temp))

            self.dlg.label_sourcevalue.setText(str(self.source))
            self.dlg.label_destvalue.setText(str(self.destination))


            def add():
                source = self.source
                destination = self.destination
                
                cursor.execute("SELECT node, edge FROM pgr_dijkstra('SELECT gid AS id, start_id::int4 AS source, end_id::int4 AS target, shape_leng::float8 AS cost FROM network', %s, %s, false);", (source, destination))

                list1 = cursor.fetchall()
                
                if len(list1) ==  0:
                    msgbar = "System can not find any route between this source: " + str(self.source) + " and destination: " + str(self.destination)
                    print("System can not find any route between this source: " + str(self.source) + " and destination: " + str(self.destination))
                    self.iface.messageBar().pushMessage(msgbar, level=Qgis.Info)

                    self.run() 

                for k in list1:
                    t = 2
                    for j in k:
                        if(t == 2):
                            #print(j)
                            
                            routenodes.append(j)                                                
                        else:
                            routeedges.append(j)
                        t = t + 1

                del routeedges[-1]

                s = str(routenodes)
                s = s.replace("[", "")
                s = s.replace("]", "")

                table_detail_list.append(s)

                s = s.replace(",", "")
                intermediatenode = list(s.split(" "))
                vlist = ["car", "truck", "taxi", "bus", "riksha" ,"van","train", "plane"]
                
                self.dlg.comboBox_halt.show()

                self.dlg.pushButton_deletehalt.setStyleSheet("color: green;font-size: 12pt; ") 
                self.dlg.pushButton_deletevehicle.setStyleSheet("color: green;font-size: 12pt; ") 
                self.dlg.pushButton_deletehalt.show()
                self.dlg.pushButton_deletevehicle.show()

                self.dlg.label_nodelist.setStyleSheet("color: brown; ") 
                self.dlg.label_nodelist.show()

                self.dlg.label_nodelistvalue.show()
                self.dlg.comboBox_vehical.show()
                
                self.dlg.label_nodelistvalue.setWordWrap(True)
                
                self.dlg.label_nodelistvalue.setText(str(routenodes))
                self.dlg.comboBox_halt.addItems(intermediatenode)
                self.dlg.comboBox_vehical.addItems(vlist)
                
                
                self.dlg.label_nodelistvalue.show()
                self.dlg.label_haltdur.setStyleSheet("color: brown;")
                self.dlg.label_haltdur.show()
                
                self.dlg.lineEdit_durationval.setPlaceholderText('Halt Time')
                self.dlg.lineEdit_durationval.setFocus()

                self.dlg.lineEdit_durationval.show()
                self.dlg.pushButton_addhaltlist.setStyleSheet("color: green;font-size: 12pt; ") 
                self.dlg.pushButton_otherroute.setStyleSheet("color: green;font-size: 12pt; ") 
                self.dlg.pushButton_calculatetime.setStyleSheet("color: blue;font-size: 12pt; ") 

                self.dlg.pushButton_addvehicle.setStyleSheet("color: green;font-size: 12pt; ") 

                self.dlg.pushButton_addhaltlist.show()
                self.dlg.pushButton_calculatetime.show()
                
                self.dlg.label_haltnodelist.show()

                self.dlg.label_vehicle.setStyleSheet("color: brown;")
                self.dlg.label_vehicle.show()
                self.dlg.lineEdit_speed.setPlaceholderText('Vehical Speed')
                self.dlg.lineEdit_speed.setFocus()
                self.dlg.lineEdit_speed.show()
                self.dlg.pushButton_addvehicle.show()
                self.dlg.label_starttime.setStyleSheet("color: brown;")
                self.dlg.label_starttime.show()
                self.dlg.lineEdit_starttime.show()
                self.dlg.lineEdit_starttime.setPlaceholderText('hh:mm')
                self.dlg.label_date.setStyleSheet("color: brown;")
                self.dlg.label_date.show()
                self.dlg.dateEdit.setStyleSheet("color: green;font-size: 11pt; ")
                self.dlg.dateEdit.show()
                

            def gettime():
                #self.dlg1.tableWidget_time.setRowCount(0)
                halttimetemp = []
                source = self.source
                destination = self.destination
                
                total_time = 0
                
                #start date by calender
                sd = self.dlg.dateEdit.date() 
                caldate = str(sd.toPyDate())

                # for calculating time and length
                
                if self.routecount == 1:
                    #check table is exist or not
                    query = "SELECT EXISTS (SELECT relname FROM pg_class WHERE relname = 'Routedetail');"
                    resp = cursor.execute(query)
                    rows = cursor.fetchone()
                    #print(rows[0]) ##True or False

                    #if exist table then remove else no remove
                    if rows[0] == True:
                        print("remove table")

                        cursor.execute("DROP TABLE Routedetail")
                        #cursor.execute("DROP TABLE timecesium")
                        #cursor.execute("DROP TABLE Mobility")
                        #cursor.execute("DROP TABLE Trajectories")

                        os.remove(self.plugin_path+"/cesium_animation/latLongCesium.json")
                        #os.remove(self.plugin_path+"/Army/trips2.csv")
                        os.remove(self.plugin_path+"/Army/LatLongGeom.csv")
                        os.remove(self.plugin_path+"/cesium_animation/cesiumAnimation.json")

                                                        
                cursor.execute("CREATE TABLE IF NOT EXISTS Mobility(route text, geom text, time text)")
                cursor.execute("CREATE TABLE IF NOT EXISTS Trajectories(id text, trip text)")

                cursor.execute("CREATE TABLE IF NOT EXISTS Routedetail (id serial PRIMARY KEY, Route text,  Source text, Destination text, Edge text, EdgeLength text, vehical text, vehicalSpeed text, StartingTime text, s_date text,  HaltNode text, HaltTime text, MovingTime text, EndingTime text, e_date text, Geom text )")
                cursor.execute("CREATE TABLE IF NOT EXISTS timecesium (id serial PRIMARY KEY, route text, vehical text, vehicalSpeed text,cordinate text ,length text, time text)")
                
                file1 = open(self.plugin_path+"/cesium_animation/cesiumAnimation.json", 'a+')
                file2 = open(self.plugin_path+"/cesium_animation/latLongCesium.json", 'a+')
                file3 = open(self.plugin_path+"/Army/trips2.csv", 'a+')
                file4 = open(self.plugin_path+"/Army/animation.csv", 'a+')
                file5 = open(self.plugin_path+"/Army/LatLongGeom.csv", 'a+')

                self.incroute = self.incroute + 1

                v = 0 
                for vehitem in vehicals:
                    vehical = str(vehicals[v])    
                    speed = str(vehicals_speed[v])

                    #print("********************")
                    #print("vehicle:: " + vehical + "      speed: " + speed)

                    reach_time = self.start_time
                    total_time = 0
                    i = 0  

                    for edge1 in routeedges:    
                        Rsource = str(routenodes[i])
                        Rdestination = str(routenodes[i+1])
                        i = i + 1
                        rt2 = str(reach_time)

                        # print("source:: " + Rsource)
                        # print("destination:: " + Rdestination)
                        
                        e1 = str(edge1)
                        #print("edge:: " + str(edge1) )

                        squery = "select ST_AsText(geom) from network where gid= " + str(edge1)

                        cursor.execute(squery)
                        
                        x1 = str(cursor.fetchall())
                                
                        x1 = x1.replace("('", "")
                        x1 = x1.replace(",)","")
                        x1 = x1.replace("'", "")
                        x1 = x1.replace("[", "")
                        x1 = x1.replace("]", "")
                        
                        lenin = "SELECT ST_Length(ST_Transform(ST_GeomFromEWKT('SRID=4326;" + x1  + "'),3857));"
                        cursor.execute(lenin)
                        len22 = cursor.fetchall()
                        len11 = str(len22)
                        len11 = len11.replace("[(", "")
                        len11 = len11.replace(",)]", "")
                        flt = float(len11)
                        edgelength = flt/1000         
                        edgelength = round(edgelength, 2)
                        el = str(edgelength)
                        #print("edge length (km):  " + el)
                        #print("time at  source node: " + str(reach_time)  )
                        time = 0
                        h = 0
                        hn = ""
                        ht = ""
                    
                        for Rholt in halt_node:        
                            if(Rsource == str(Rholt)):
                                #print("Halt here at node :  " + Rsource + " for " + str(halt_time[h]) + " hours") 
                                time = time + float(halt_time[h])
                                hn = str(Rholt)

                                sec11 = float(halt_time[h])*3600 
                                min, sec11 = divmod(sec11, 60) 
                                hour, min = divmod(min, 60) 
                                w1 = "%02d:%02d:%02d" % (hour, min, sec11)

                                # minutes4 = float(halt_time[h]) * 60
                                # hours4, minutes4 = divmod(minutes4, 60)
                                # w1 = "%02d:%02d"%(hours4,minutes4)
                                ht = str(w1)
                                halttimetemp.append(ht)

                            h = h + 1
                        

                        speedfloat = float(speed)
                        movingtime =  edgelength / speedfloat 
                        movingtime = round(movingtime, 2)
                        mt = str(movingtime)
                        #print("moving time: (hours) " + str(movingtime))

                        #print(".............. " )
                        total_time = float(reach_time) + time + movingtime
                        reach_time = float(reach_time) + time + movingtime

                        total_time = round(total_time, 2)
                        reach_time = round(reach_time, 2)
                        tt = str(total_time)
                        route = str(self.incroute)

                        
                        squery = "select geom from network where fnode_ =" + Rsource 
                        cursor.execute(squery)      
                
                        geom = str(cursor.fetchall())
                        geom = geom.replace("[('", "")
                        geom = geom.replace("',)]", "")

                        #date and time formate

                        now = datetime.now()
                        
                        sec11 = float(mt)*3600 
                        min, sec11 = divmod(sec11, 60) 
                        hour, min = divmod(min, 60) 
                        z = "%02d:%02d:%02d" % (hour, min, sec11)

                        # minutes2 = float(mt)*60
                        # hours2, minutes2 = divmod(minutes2, 60)
                        # z = "%02d:%02d"%(hours2,minutes2)
                        mtn = str(z)

                        ###### date and time increment according hours

                        today = datetime.today().strftime("%Y-%m-%d")
                        date = caldate
                    
                        st = rt2


                        div = float(st)/24
                        day = int(div)
                        date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=day)).strftime('%Y-%m-%d')

                        st1 = float(st)%24 
                        
                        sec11 = float(st1)*3600 
                        min, sec11 = divmod(sec11, 60) 
                        hour, min = divmod(min, 60) 
                        w = "%02d:%02d:%02d" % (hour, min, sec11)

                        # minutes3 = float(st1)*60
                        # hours3, minutes3 = divmod(minutes3, 60)
                        # w = "%02d:%02d"%(hours3,minutes3)
                        st2 = str(w)
                        
                        today1 = datetime.today().strftime("%Y-%m-%d")
                        date1 = caldate
                        et = tt


                        div1 = float(et)/24
                        day1 = int(div1)
                        edate1 = (datetime.strptime(date1, '%Y-%m-%d') + timedelta(days=day1)).strftime('%Y-%m-%d')
                        self.edate11 = edate1
                        et1 = float(et)%24 
                        
                        sec11 = float(et1)*3600 
                        min, sec11 = divmod(sec11, 60) 
                        hour, min = divmod(min, 60) 
                        w1 = "%02d:%02d:%02d" % (hour, min, sec11)

                        # minutes4= float(et1)*60
                        # hours4, minutes4 = divmod(minutes4, 60)
                        # w1 = "%02d:%02d"%(hours4,minutes4)
                        et2 = str(w1)


                        cursor.execute("INSERT INTO Routedetail (Route ,Source, Destination , Edge, EdgeLength , vehical , vehicalSpeed , StartingTime, s_date,  HaltNode, HaltTime, MovingTime, EndingTime, e_date, Geom) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(route, Rsource, Rdestination, e1, el,vehical, speed, st2 ,date, hn, ht, mtn , et2 , edate1 ,geom ))
                        

                    tt = str(total_time)
                    #print("total time: (hour) " + str(total_time))
                    v = v + 1
        
                s = str(halt_node)
                s = s.replace("[", "")
                s = s.replace("]", "")
                s = s.replace("'", "")            
                table_detail_list.append(s)

                #print('halttimetemp')
                #print(halttimetemp)
                s1 = str(halttimetemp)
                s1 = s1.replace("[", "")
                s1 = s1.replace("]", "")
                s1 = s1.replace("'", "")
                s1 = s1.replace("''", "")
                
                
                table_detail_list.append(s1)

                s = str(vehicals)
                s = s.replace("[", "")
                s = s.replace("]", "")
                s = s.replace("'", "")    
                table_detail_list.append(s)

                s = str(vehicals_speed)
                s = s.replace("[", "")
                s = s.replace("]", "")
                s = s.replace("'", "")  
                table_detail_list.append(s)

                sec11 = float(self.start_time)*3600 
                min, sec11 = divmod(sec11, 60) 
                hour, min = divmod(min, 60) 
                x = "%02d:%02d:%02d" % (hour, min, sec11)

                # minutes = float(self.start_time) * 60
                # hours, minutes = divmod(minutes, 60)
                # x = "%02d:%02d"%(hours,minutes)

                #edate11 = 
                st1 = str(x)
                s_date = caldate
                sdt = s_date +" / " + st1
                edt = self.edate11 +" / " + et2

                table_detail_list.append(sdt)
                table_detail_list.append(edt)

                now = datetime.now()
                date_time = now.strftime("%Y-%m-%d")
                routeno1 = str(self.incroute)

            
                addTableRowdeatail(self.dlg1.tableWidget_detail, table_detail_list)

                self.dlg1.show()

                tuple1 = tuple(routeedges)
                str1 = str(tuple1)
                str1 = str1.replace('L', '') 
                str1 = str1.replace(', -1', '')
                
                d = "edges of route= " + str1
                #print(d)                

                try:                      
                    squery = "select count(geom) from network where gid in " + str1 
                    cursor.execute(squery)
                    cursorlength = str(cursor.fetchone())

                    squery = "select ST_AsText(geom) from network where gid in " + str1 
                    cursor.execute(squery)
        
                
                    x1 = str(cursor.fetchall())
                    #print("orignal data is --------------------------")
                
                except Exception as e:
                    print('Error: ' + str(e))
                    
                x1 = x1.replace("',), ('LINESTRING",",")
                x1 = x1.replace("[('LINESTRING", "MULTILINESTRING(")
                x1 = x1.replace("',)]", ")")
                
                #cesium json latlong 3857

                #squeryg = "select geom from network where gid in " + str1 
                try:
                    squeryg = "SELECT ST_AsText(ST_Transform(ST_SetSRID(geom,4326),3857)) As spere_merc FROM public.network where gid in " + str1 
                    cursor.execute(squeryg)
                    geom_cesium = str(cursor.fetchall())
                

                    geom_cesium = geom_cesium.replace("',), ('LINESTRING", ",")
                    geom_cesium = geom_cesium.replace("',)]", ")")
                    geom_cesium = geom_cesium.replace("[('LINESTRING(", "MULTILINESTRING((")

                    ##line merge 3857
                    squerym = "SELECT ST_AsText(ST_LineMerge(ST_GeomFromText('" + geom_cesium + "')))"
                    cursor.execute(squerym)
                    resm = str(cursor.fetchall())

                    resm = resm.replace("[('LINESTRING(", "")
                    resm = resm.replace(")',)]", "")

                    #line merge latlong
                    squery = "SELECT ST_AsText(ST_LineMerge(ST_GeomFromText('" + x1 + "')))"

                    cursor.execute(squery)
                    res = str(cursor.fetchall())
                
                
                    res1 = res

                    res1 = res1.replace("[('", "")
                    res1 = res1.replace("',)]", "")

                    res = res.replace("[('LINESTRING(","")
                    res = res.replace(")',)]","")

                
                    
                    self.routegeom.append(x1)
                    wkt = x1
                    #wkt = res
                    #print("geom of route= ")
                    e = "geom of route= "
                    vehspeed = self.dlg.lineEdit_speed.text()

                    
                    #timecontroller plugin Animation for data

                    split1 = res.split(",")
                    split1 = list(zip(split1, split1[1:] + split1[:1]))
                    pair2 = split1
                    
                    total_time1 = float(self.start_time)
                    tfList = []                
                    sec = total_time1 *3600     
                        
                    # route start time
                    min, sec = divmod(sec, 60) 
                    hour, min = divmod(min, 60) 
                    tf1 = "%02d:%02d:%02d" % (hour, min, sec)

                    tf2 = caldate +" " +tf1
                    tfList.append(tf2)
                    #tfList.append(tf1)

                    sec2 = 0

                    #cesium json file for (latlong (cesiumAnimation))
                    routeno = str(self.incroute)
                    routeno1 = '"' +routeno+'"' +":"

                            
                    file2.write("\n")
                    file2.write("%s" % routeno1)

                    file2.write("{")

                    file2.write("\n")
                    position = '"' + "position" +'"' +":"
                    file2.write("%s" % position)

                    file2.write("[")
                    file2.write("\n")

                    #HALT node of add time Longitude latitude 8 march

                    #find halt_node of latlong

                    if (len(halt_node) and len(halt_time)) > 0:
                        halt = str(halt_node)
                        halt = halt.replace("[","(")
                        halt = halt.replace("]",")")
                        halt = halt.replace('"',"")
                        halt = halt.replace("'","")

                        squery = "select ST_AsText(geom) from node where id in " + halt 
                        cursor.execute(squery)
                        latlong = str(cursor.fetchall())

                        latlong = latlong.replace("[('POINT(", "")
                        latlong = latlong.replace(")',),", ",")
                        latlong = latlong.replace(")',)]", "")
                        latlong = latlong.replace(" ('POINT(", "")
                        latlong = latlong.split(",")
                        print(latlong)

                        # for halt time
                        h_t = [float(f) for f in halt_time]

                    else:
                        pass

                    #perticular latlong from time and date
                    for i in pair2:
                        p = str(i)

                        p = p.replace("('","LINESTRING(")
                        p = p.replace(", ",",")
                        p = p.replace("'","")


                        f1 = p
                        f1 = f1.replace("LINESTRING(","")
                        f1 = f1.replace(")","")
                        f1 = f1[:f1.rfind(',')]
                        f1 = f1.replace(" ",",")


                        l = "SELECT ST_Length(ST_Transform(ST_GeomFromEWKT('SRID=4326;" + p+ "'),26986));"
                        cursor.execute(l)
                        len22 = cursor.fetchall()
                        len22 = str(len22)

                        len22 = len22.replace("[(","")
                        len22 = len22.replace(",)]","")
                        len22 = float(len22)/1000 #len is km
                        len22 = round(len22 ,2)

                        vehspeed = self.dlg.lineEdit_speed.text()

                        s1 = int(vehspeed)
                        t = len22 /s1 #time is hour

                        total_time1 = total_time1 + t

                        h = round(total_time1 ,5)

                        #halt time add
                        if (len(halt_node) and len(halt_time)) > 0:
                            for k in range(len(latlong)):
                                ltg = latlong[k]
                                ltg = ltg.replace(" ",",")
                                if f1 == ltg:
                                    total_time1 = total_time1 + t + float(h_t[k])

                        # sec = h *3600 
                        #time
                        sec11 = float(h) % 24
                        sec11 = sec11*3600
                        min, sec11 = divmod(sec11, 60) 
                        hour, min = divmod(min, 60) 
                        tf = "%02d:%02d:%02d" % (hour, min, sec11)

                        #date
                        d = caldate
                        div = float(h)/24
                        day = int(div)
                        date11 = (datetime.strptime(d, '%Y-%m-%d') + timedelta(days=day)).strftime('%Y-%m-%d')
                        
                        tf3 = date11 + " " + tf
                        tfList.append(tf3)

                        csv3 = tfList[0]+","+ f1+","+tfList[1]
                        tfList.pop(0)                
                        
                        file5.write("%s" % csv3)
                        file5.write("\n") 

                        #for cesium json file (latLongCesium.json):::::
                                        
                        sec1 = t * 3600
                        sec2 = float(sec2) + sec1
                        sec2 = round(sec2,3)
                        sec3 = str(sec2)
                        cjson = sec3 +"," +f1 +","+"0"+","
                        
                        file2.write("%s" % cjson)
                        file2.write("\n")

                except Exception as e:
                    print('Error: ' + str(e))

                file5.write("\n")

                file2.write("]")
                file2.write(",")
                file2.write("\n")

                veh = self.dlg.comboBox_vehical.currentText()
                vehical1 = str(veh)
                vtype = '"' +"vehical" +'"' +":" + "[" +'"'+ vehical1 + '"'+"]"+","
                file2.write("%s" % vtype)
                st11 = '"'+"interval"+'"'+ ":" + "[" +'"'+s_date+'T'+st1+":00" +'Z'+'"' +','+'"'+date1+"T" + et2 +":00" + "Z"+'"'+']'
                file2.write("\n")

                file2.write("%s" % st11)
                file2.write("\n")
                file2.write("},")
                file2.write("\n")
                file2.close()
                
                geom_cesium1 = list(resm.split(","))
                geom_cesium2 = list(zip(geom_cesium1, geom_cesium1[1:] + geom_cesium1[:1]))

                ###PROJECTION  CESIUM TIME ANIMATION
                
                routeno = str(self.incroute)
                routeno1 = '"' +routeno+'"' +":"
        
                file1.write("\n")
                file1.write("%s" % routeno1)

                file1.write("{")

                file1.write("\n")
                position = '"' + "position" +'"' +":"
                file1.write("%s" % position)

                file1.write("[")
                file1.write("\n")
                total_time = 0
                n = []
                # all about cesiumAnimation.json file 
                for i in geom_cesium2:

                    ii = str(i)
                    ii = ii.replace("('LINESTRING", "LINESTRING(")
                    ii = ii.replace("', '", ",")
                    ii = ii.replace("')", ")")
                    ii = ii.replace("('", "LINESTRING(")

                    cursor.execute("SELECT ST_AsEWKT(ST_Transform(ST_GeomFromEWKT('SRID=2249;" + ii  + "'),4326));")

                    p = cursor.fetchone()
                    p = str(p)
                    p = p.replace("('SRID=4326;"," ")
                    p = p.replace("',)"," ")
                    geom1 = p
                    
                    #length find 

                    cursor.execute("SELECT ST_Length(ST_Transform(ST_GeomFromEWKT('SRID=3857;" + ii  + "'),26986));")
                    x = cursor.fetchall()

                    xx = str(x)
                    xx = xx.replace("[(", "")
                    xx = xx.replace(",)]", "")

                    # length km
                    xx = float(xx) * 0.001

                    #time  hour
                    time = float(xx) / float(vehspeed)

                    # second
                    time = time * 3600
                    total_time = total_time + time
                    t_t = float(total_time)

                    f = format(t_t, '.7f')
                    time1 = str(f)
                    
                    ii = ii.replace("LINESTRING(", "")
                    ii = ii.replace(")", "")

                    proj1 = time1 + "," + ii
                    proj1 = proj1.replace(" ", ",")

                    #remove last lat long in 
                    proj1 = proj1[:proj1.rfind(',')]
                    proj1 = proj1[:proj1.rfind(',')]
                    proj1 = proj1 + ','
                    
                    file1.write("%s" % proj1)
                    file1.write("\n")
                    
                    route1 = str(self.incroute)
                    veh = self.dlg.comboBox_vehical.currentText()
                    vehical1 = str(veh)
                    vehspeed = self.dlg.lineEdit_speed.text()
                    speed1 = str(vehspeed)

                    # postgresql extension of mobilitydb  for trips csv file and table(timecesium,Mobility) of data
                    st = self.dlg.lineEdit_starttime.text()
                    stT_hm = [int(n) for n in st.split(":")]
                    stT_hm1 = float(stT_hm[0] + stT_hm[1]/60.0)

                    st22 = float(stT_hm1)
                    st221 = st22*3600
                    mob = float(f) *10000000
                    mob1 = st221 + mob
                    m_time = int(mob1)

                    timeformate = strftime("%H:%M:%S", gmtime(m_time))
                    date_time = now.strftime("%Y-%m-%d ")
                    t = s_date + " " +timeformate+"+00"
                    t1 = s_date + " " +timeformate

                    #trajectory table entry like trips of tutorial github::
                    m = p+ "@" + t
                    m = m.replace("[' ","[")
                    m = m.replace("']","]")
                    n.append(m)

                    #for csv file
                    x = geom1
                    x = x.replace(" LINESTRING("," ")
                    x = x.replace(") ","")
                    x = x.split(",")
                    x.pop(-1)
                    x = str(x)
                    x = x.replace(" ",",")
                    x = x.replace("[',","")
                    x = x.replace("']","")

                    csv = vehical1 + route1 +","+x+"," +t1
                    csv1 = t1+','+x

                    file3.write("\n")

                    file3.write("%s" % csv1)

                    cursor.execute("INSERT INTO Mobility(route, geom, time) VALUES (%s, %s, %s)",(route1, geom1, t))
                    cursor.execute("INSERT INTO timecesium (route ,vehical ,vehicalSpeed, cordinate, length, time ) VALUES (%s, %s, %s, %s, %s, %s)",(route1, vehical1, speed1, ii, xx, time1))


                n = str(n)
                n = n.replace("[' ","[")
                n = n.replace("']","]")
                n = n.replace('"'," ")
                n = n.replace("', '",",")
                n = n.replace("'LINESTRING","LINESTRING")

                cursor.execute("INSERT INTO Trajectories(id, trip) VALUES (%s, %s)",(routeno, n))

                file1.write("]")
                file1.write(",")

                file1.write("\n")
                veh = self.dlg.comboBox_vehical.currentText()
                vehical1 = str(veh)
                vtype = '"' +"vehical" +'"' +":" + "[" +'"'+ vehical1 + '"'+"]"+","
                file1.write("%s" % vtype)
                st11 = '"'+"interval"+'"'+ ":" + "[" +'"'+s_date+'T'+st1+":00" +'Z'+'"' +','+'"'+date1+"T" + et2 +":00" + "Z"+'"'+']'
                file1.write("\n")

                file1.write("%s" % st11)
                file1.write("\n")
                file1.write("},")
                file1.write("\n")
                file1.close()

                #END CESIUM TIME PROJECTION

                #Route wkt line draw
                resultname = "Route " + str(self.incroute)
                colorcodelist = ["#00bfff","#0066ff", "#8000ff", "#00ff00", "#00ff80", "#00ffbf", "#00ffff", "#bfff00", "#00bfff", "#00bfff","#00bfff"]
                colorcode = str(colorcodelist[self.incroute])
                colorcode = colorcode.replace("'", "")            
            
                temp = QgsVectorLayer("MultiLineString?crs=EPSG:4326", resultname, "memory")
                QtGui.QColor(255, 0, 0)
                single_symbol_renderer = temp.renderer()
                symbol = single_symbol_renderer.symbol()
                sym = QtGui.QColor(colorcode)
                symbol.setWidth(1.2)

                #add maptips(mouse hover)
                expression = """[%  @layer_name  %]"""
                temp.setMapTipTemplate(expression)

                QgsProject.instance().addMapLayer(temp)
                temp.startEditing()
                geom = QgsGeometry()
                geom = QgsGeometry.fromWkt(wkt)
                feat = QgsFeature()
                feat.setGeometry(geom)
                temp.dataProvider().addFeatures([feat])
                temp.commitChanges()        

                connection.commit()

                cursor.close()

                connection.close()
            def timecontroller():
                #remove delimeterLyer of layers panel in qgis
                for lyr in QgsProject.instance().mapLayers().values():
                    if lyr.name()[0:14] == "RouteAnimation":
                        QgsProject.instance().removeMapLayers([lyr.id()])

                #remove all csv file in directory
                mypath = self.plugin_path+"/Army/AnimCsv/"
                for root, dirs, files in os.walk(mypath):
                    for file in files:
                        os.remove(os.path.join(root, file))

                #####split csv file route wise 
                file_data = self.plugin_path+'/Army/LatLongGeom.csv'
                with open(file_data,'r') as input_file:
                    data_read = input_file.read()
                    data_split = data_read.split('\n\n')
                    
                    for i, smaller_data in enumerate(data_split):
                        i = i + 1
                        #print(smaller_data)
                        if smaller_data != "":
                            #with open(f'/home/bisag/.var/app/org.qgis.qgis/data/QGIS/QGIS3/profiles/default/python/plugins/army_plugin/Army/AnimCsv/RouteAnimation_{i}.csv','w') as new_data_file:
                            with open(self.plugin_path+f'/Army/AnimCsv/RouteAnimation_{i}.csv','w') as new_data_file:
                                new_data_file.write("field_1,field_2,field_3,field_4")
                                new_data_file.write("\n")
                                new_data_file.write(smaller_data)

                ###  all route of csv file animation in time controller

                # directory = self.plugin_path+"/Army/AnimCsv"
                # def load_and_configure(filename):
                #     path = os.path.join(directory, filename)
                #     uri = 'file:///' + path + "?type=csv&escape=&useHeader=No&detectTypes=yes"
                #     uri = uri + "&crs=EPSG:4326&xField=field_2&yField=field_3"
                #     vlayer = QgsVectorLayer(uri, filename, "delimitedtext")
                    
                #     QtGui.QColor(255, 0, 0)

                #     try:
                #         single_symbol_renderer = vlayer.renderer()
                #         symbol1 = single_symbol_renderer.symbol()
                #         sym = QtGui.QColor('#8000ff')
                #         symbol1.setSize(4)
                #         vlayer.triggerRepaint()
                #         vlayer.startEditing()
                #     except Exception as e4:
                #         print('Error: ' + str(e4))
                    
                #     #mouse hover 
                #     expression = """[%  @layer_name  %]"""
                #     vlayer.setMapTipTemplate(expression)

                #     #title label decorations add
                    

                #     QgsProject.instance().addMapLayer(vlayer)
                #     mode = QgsVectorLayerTemporalProperties.ModeFeatureDateTimeStartAndEndFromFields

                #     tprops = vlayer.temporalProperties()
                    
                #     tprops.setStartField("field_1")
                #     tprops.setEndField("field_4")
                #     tprops.setMode(mode)
                #     tprops.setIsActive(True)

                # for filename in os.listdir(directory):
                #     if filename.endswith(".csv"):
                #         load_and_configure(filename)

                # for i in self.iface.mainWindow().findChildren(QtWidgets.QDockWidget):
                #         if i.objectName() == 'Temporal Controller':
                #             #self.iface.mainWindow().findChild(QDockWidget,'PythonConsole').setVisible(False)
                #             i.setVisible(True)  

            def calculatetime():
                st = self.dlg.lineEdit_starttime.text()
                # convert hh:mm to hour(float)
                stT_hm = [int(n) for n in st.split(":")]

                stT_hm1= float(stT_hm[0] + stT_hm[1]/60.0) #hour

                self.start_time = stT_hm1
                # self.start_time = st

                gettime()
                self.dlg.pushButton_otherroute.show()
                self.dlg.pushButton_deletehalt.show()
                self.dlg.pushButton_deletevehicle.show()
                self.dlg.pushButton_intersection.setStyleSheet("color: green;font-size: 12pt; ") 
                self.dlg.pushButton_animation.setStyleSheet("color: purple;font-size: 12pt; ")

                self.dlg.pushButton_intersection.show()
                self.dlg.pushButton_animation.show()

            def intersection():
                #remove intersection route
                for lyr in QgsProject.instance().mapLayers().values():
                    if lyr.name()[0:9] == "Intersect":
                        QgsProject.instance().removeMapLayers([lyr.id()])

                if self.routecount >= 2:
                    for i in range(self.routecount-1):                              
                        j = i
                        for j in range(j , self.routecount-1):
                            j += 1
                            # print("i=",i," j=" ,j)             
                            getIntersetmultiline(i, j)   
                        i +=  1
                
            def getIntersetmultiline(i, j):
                try:
                    #remove all raw belong to duplicates
                    #self.dlg1.tableWidget_time.setRowCount(0)

                    rrr1 = str(i+1)
                    rrr2 = str(j+1)
                    connection = psycopg2.connect(user="postgres", password="postgres", host="localhost", database="project")
                    cursor = connection.cursor()

                    source11 = self.sourcelist[i]
                    destination11 = self.destinationlist[i]
                    x11 = self.routegeom[i] 
                    

                    source22 = self.sourcelist[j]
                    destination22 = self.destinationlist[j]
                    x22 = self.routegeom[j]

                    #print("..............................")
                    
                    f = "intersection between route- " + str(i+1) + " which source is: " + str(source11)  + " and destination is: " + str(destination11) + " and "
                    print(f)

                    g = "                     route- " + str(j+1) + " which source is: " + str(source22)  + " and destination is: " + str(destination22)
                    print(g)
                    
                    squery1 = "SELECT ST_Intersects('" + x11 + "'::geometry, '" + x22 + "'::geometry)"
                    cursor.execute(squery1)
                    res11 = cursor.fetchall()
                    # print("intersection = ")  
                       
                    res1 = str(res11)
                    
                    res1 = res1.replace("[(", "")
                    res1 = res1.replace(",)]","") 
                    # print(res1)

                    # length of Intersects route
                    length1 = "SELECT ST_Length(ST_Transform(ST_GeomFromEWKT('SRID=4326;" + x11  + "'),3857));"
                    cursor.execute(length1)
                    len2 = cursor.fetchall()
                    len1 = str(len2)
                    len1 = len1.replace("[(", "")
                    len1 = len1.replace(",)]", "")
                    flt = float(len1)
                    fltnew = flt/1000
                    lenrout1 = str(fltnew)

                    length2 = "SELECT ST_Length(ST_Transform(ST_GeomFromEWKT('SRID=4326;" + x22  + "'),3857));"
                    cursor.execute(length2)
                    len4 = cursor.fetchall()
                    len3 = str(len4)
                    len3 = len3.replace("[(", "")
                    len3 = len3.replace(",)]", "")
                    flt1 = float(len3)
                    fltnew1 = flt1/1000
                    lenrout2 = str(fltnew1)

                    k = 'length of route 1 =', lenrout1
                    l = 'length of route 2 = ', lenrout2
                    # print(k)
                    # print(l)

                    ###    if intersection is then 

                    if(res1 == "True"):             
                        squery = "SELECT ST_AsText(ST_Intersection('" + x11 + "'::geometry, '" + x22 + "'::geometry))" 

                        cursor.execute(squery)
                        res = cursor.fetchall()

                        # print('intersection point = ')

                        res2 = str(res)
                        res2 = res2.replace("[('", "")
                        res2 = res2.replace("',)]","")
                        
                        lenin = "SELECT ST_Length(ST_Transform(ST_GeomFromEWKT('SRID=4326;" + res2  + "'),3857));"                
                        cursor.execute(lenin)
                        len22 = cursor.fetchall()

                        len11 = str(len22)
                        len11 = len11.replace("[(", "")
                        len11 = len11.replace(",)]", "")
                        flt = float(len11)
                        fltnew = flt/1000
                        len11 = str(fltnew)

                        n = "intersection point length " ,len11
                        #print(n)
                        
                        rt1 = int(flt)

                        wkt = res2
                        wkt1 = wkt[0:5]#POINT

                        # intersection wkt line of route draw in qgis 
                        
                        resultname1 = "Intersect Route " + str(self.incroute) 
                        colorcodelist1 = ["#ff0000", "#ff4000", "#ff8000", "#ffbf00", "#ffff00", "#ff0040", "#ff0080", "#ff00bf", "#ff00ff", "#bf00ff"]
                        colorcode1 = str(colorcodelist1[self.incroute])
                        colorcode1 = colorcode1.replace("'", "")
                        self.incroute = self.incroute + 1 
                        QtGui.QColor(255, 0, 0)

                        #if intersect point if point layer then
                        if wkt1 == "POINT":
                            temp = QgsVectorLayer("Point?crs=EPSG:4326", resultname1, "memory")
                            single_symbol_renderer = temp.renderer()
                            symbol = single_symbol_renderer.symbol()
                            sym = QtGui.QColor(colorcode1)
                            symbol.setSize(4)
                            temp.triggerRepaint()
                        else:
                            temp = QgsVectorLayer("MultiLinestring?crs=EPSG:4326", resultname1, "memory")
                            single_symbol_renderer = temp.renderer()
                            symbol = single_symbol_renderer.symbol()
                            sym = QtGui.QColor(colorcode1)
                            symbol.setWidth(2)
                            temp.triggerRepaint()

                        #mouse hover 
                        expression = """[%  @layer_name  %]"""
                        temp.setMapTipTemplate(expression)

                        QgsProject.instance().addMapLayer(temp)
                        temp.startEditing()
                        geom = QgsGeometry()
                        geom = QgsGeometry.fromWkt(wkt)
                        feat = QgsFeature()
                        feat.setGeometry(geom)
                        temp.dataProvider().addFeatures([feat])
                        temp.commitChanges()

                    ###    if intersection is then find intersection node with below code

                    if(res1 == "True"):    
                        
                        cursor.execute("SELECT node FROM pgr_dijkstra('SELECT gid AS id, start_id::int4 AS source, end_id::int4 AS target, shape_leng::float8 AS cost FROM network', %s, %s, false);", (source11, destination11))
                        nodelist1 = cursor.fetchall()                 
                        
                        cursor.execute("SELECT node FROM pgr_dijkstra('SELECT gid AS id, start_id::int4 AS source, end_id::int4 AS target, shape_leng::float8 AS cost FROM network', %s, %s, false);", (source22, destination22))
                        nodelist2 = cursor.fetchall()

                        routeedges1 = []
                        routeedges2 = []
                        for item1 in nodelist1:
                            for item2 in nodelist2:
                                if(item1 == item2):
                                    stritem = str(item2)                            
                                    stritem = stritem.replace("(", "")
                                    stritem = stritem.replace(",)", "")
                                    
                                    r11 = "'" + rrr1 + "','" + rrr2 +"'"
                                    query = "select route, source, vehical, haltnode, halttime, startingtime from public.routedetail where source='" + stritem + "'  and route in (" + r11 + ")"                         
                                    cursor.execute(query)
                                    intersectnodes =  cursor.fetchall()  
                        
                                    #print("intersectnodes")
                                    #print(intersectnodes)
                                
                                    raw1 = intersectnodes[0]
                                    raw2 = intersectnodes[1]

                                    reachtime1 = raw1[5]
                                    reachtime2 = raw2[5]
                                    
                                    #get split hour and minit
                                    r1 = reachtime1.split(":")
                                    r1 = (float(r1[0])*60 + float(r1[1]))/60                            

                                    r2 = reachtime2.split(":")
                                    r2 = (float(r2[0])*60 + float(r2[1]))/60
                                    rtlow = r1 - 0.5
                                    rtup = r1 + 0.5
                                    intersectvalue = ""

                                    if(r2 >= rtlow and r2 <= rtup ):
                                        intersectvalue = "yes"
                                    else:
                                        intersectvalue = "no"

                                    #print("Intersect node detail:")
                                    #print(intersectnodes)
                        
                                    self.dlg1.label_intersection.show()

                                    
                                    self.dlg1.tableWidget_time.show()
                            
                                    self.dlg1.label_intersection.setStyleSheet("color: black; font-size: 18pt; ") 
                                    self.dlg1.tableWidget_time.setColumnCount(7)
                                    

                                    self.dlg1.tableWidget_time.setHorizontalHeaderLabels([' Route ', ' Intersection Node ', ' Vehical ', ' Halt Node ', ' Halt Time ', ' Reaching Time ', 'Intersect(within 30 Minutes)'])
                                    stylesheet1 = "QHeaderView::section{color:blue; border-radius:14px;}"
                                    self.dlg1.tableWidget_time.setStyleSheet(stylesheet1)

                            
                                    tableWidget_time = self.dlg1.tableWidget_time

                                    def addTableRow(tableWidget_time, row_data):
                                        
                                        row = tableWidget_time.rowCount()
                                        tableWidget_time.setRowCount(row+1)
                                        col = 0
                                        
                                        for item in row_data:
                                            cell = QTableWidgetItem(str(item))
                                            tableWidget_time.setItem(row, col, cell)
                                            col += 1

                                    for i in intersectnodes:
                                        ii = list(i)
                                        ii.append(intersectvalue)
                                        addTableRow(tableWidget_time, ii)
                                    ii = []
                                    addTableRow(tableWidget_time, ii)

                                    self.dlg1.tableWidget_time.horizontalHeader().setStretchLastSection(True) 
                                    self.dlg1.tableWidget_time.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 
                                    self.dlg1.show()

                    connection.commit()

                    cursor.close()

                    connection.close()

                except Exception as e1:
                    print('Error: ' + str(e1))
    
            self.dlg.pushButton_addhaltlist.clicked.connect(addhaltlist)   
            self.dlg.pushButton_deletehalt.clicked.connect(deletehaltlist)
            self.dlg.pushButton_addvehicle.clicked.connect(vehiclelist)
            self.dlg.pushButton_deletevehicle.clicked.connect(deletevehiclelist)
            self.dlg.pushButton_addroute.clicked.connect(pointselection) 

            self.dlg.pushButton_intersection.clicked.connect(intersection)
            self.dlg.pushButton_animation.clicked.connect(timecontroller)

            self.dlg.pushButton_otherroute.clicked.connect(addnewroute)
            self.dlg.pushButton_calculatetime.clicked.connect(calculatetime)
            
                
            self.dlg1.label_intersection.hide()
            self.dlg1.tableWidget_time.hide()
            self.dlg.label_pointselect.hide()
            self.dlg.label_source.hide()
            self.dlg.label_destination.hide()
            self.dlg.label_nodelist.hide()
            self.dlg.label_haltdur.hide()
            self.dlg.label_sourcevalue.hide()
            self.dlg.label_destvalue.hide()
            self.dlg.label_vehicle.hide()
            self.dlg.comboBox_halt.hide()
            self.dlg.comboBox_vehical.hide()

            
            self.dlg.lineEdit_durationval.hide()

            self.dlg.pushButton_addhaltlist.hide()
            self.dlg.pushButton_calculatetime.hide()
            self.dlg.pushButton_otherroute.hide()
            
            self.dlg.pushButton_deletehalt.hide()
            self.dlg.pushButton_deletevehicle.hide()

            self.dlg.pushButton_intersection.hide()
            self.dlg.pushButton_animation.hide()

            self.dlg.lineEdit_speed.hide()
            self.dlg.pushButton_addvehicle.hide() 

            self.dlg.label_starttime.hide()
            self.dlg.label_date.hide()
            self.dlg.dateEdit.hide()

            self.dlg.lineEdit_starttime.hide()
            
            self.dlg.show()

            result = self.dlg.exec_()
            if result:
                getline()
                self.run()
        except Exception as e:
            print('Error: ' + str(e))
        
        
