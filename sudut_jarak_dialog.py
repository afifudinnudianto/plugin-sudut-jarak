# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SudutJarakDialog
                                 A QGIS plugin
 Penggambaran sudut dan jarak
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-10-05
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Kelompok9
        email                : afifudinnudianto@mail.ugm.ac.id
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

from qgis.core import QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry, QgsPointXY, Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPoint
from qgis.utils import iface


# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sudut_jarak_dialog_base.ui'))


class SudutJarakDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SudutJarakDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #definisi antar muka
        self.iface = iface

        #mengatur tampilan plugin pertama kali dibuka
        self.input_az.setEnabled(False)
        self.input_jarak.setEnabled(False)
        self.cek_garis.setEnabled(False)

        #objek yang menunjukkan seberapa banyak tombol plot telah ditekan
        self.plot_clicked = 0

        #objek yang menunjukkan seberapa banyak geometri garis yang telah dibuat
        self.plot_garis = 0

        # menghubungkan tombol Plot! dengan suatu method
        self.plot.clicked.connect(self.gambar_plot)
        
    
    def gambar_plot(self):
        """ Lakukan sesuatu ketika tombol ditekan """
        try:
            #memanggil input sistem koordinat
            crs = self.sistem_koordinat.crs()

            #cek sistem koordinat yang dipilih
            self.cek_sistem_koordinat(crs) 

            # memanggil isi dari Line Edit pada kolom X dan Y
            # sekaligus mengkonversinya menjadi angka
            x = float(self.input_x.text())
            y = float(self.input_y.text())

            #cek input x dan y
            self.cek_koordinat(x, y, crs)

        except Exception as e:
            print(e)
        
        else:
            #nilai self.plot_clicked ditambah setiap tombol plot! ditekan
            self.plot_clicked += 1

            #aksi yang dilakukan apabila tombol plot! pertama kali diklik
            if self.plot_clicked == 1 :

                #panggil fungsi buat_titik() dengan parameter x, y, dan crs
                self.buat_titik(x, y, crs)  

                #mengatur tampilan plugin setelah dilakukan plot
                self.input_az.setEnabled(True)
                self.input_jarak.setEnabled(True)
                self.cek_garis.setEnabled(True)
                self.input_x.setEnabled(False)
                self.input_y.setEnabled(False)
                self.sistem_koordinat.setEnabled(False)
                
            else :                
                # memasukkan nilai azimuth ke variabel az dan
                # memasukkan nilai jarak ke variabel d
                az = self.cek_azimuth()
                d = self.cek_jarak()

                # menghitung koordinat baru dengan parameter x, y, az, d, serta crs
                self.hitung_koordinat(x, y, az, d, crs)

                #kosongkan input azimuth dan jarak setelah plot ditekan
                self.input_az.clear()
                self.input_jarak.clear()

    
    def cek_sistem_koordinat(self, crs):
        try:
            #mengecek apakah sudah memilih sistem koordinat proyeksi
            #memberikan peringatan apabila bukan sistem koordinat proyeksi
            if crs.isGeographic() :
                print("Sistem koordinat yang dipilih bukan sistem koordinat proyeksi")
                iface.messageBar().pushMessage(
                    "Peringatan","Sistem koordinat yang dipilih bukan sistem koordinat proyeksi", level=Qgis.Warning)
        
        except Exception as e:
            print(e)
    

    def cek_koordinat(self, x, y, crs):
        try:
            # mendapatkan epsg 
            geog = crs.geographicCrsAuthId()   #geographic crs' epsg
            proj = crs.authid()   #projected crs' epsg

            #mendapatkan batas sistem proyeksi yang digunakan dalam lat long
            #kemudian dibuat menjadi sebuah geometri poligon
            batas = crs.bounds()
            geom_rec = QgsGeometry.fromRect(batas)

            #transformasi menuju lat long
            crsSrc = QgsCoordinateReferenceSystem(proj)   
            crsDest = QgsCoordinateReferenceSystem(geog)  
            transformContext = QgsProject.instance().transformContext()

            xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)
            
            pt = xform.transform(QgsPointXY(x,y))

            # menampilkan hasil cek
            hasil_cek = geom_rec.contains(pt)
            print("Apakah titik berada dalam sistem koordinat proyeksi :", hasil_cek)

            #peringatan karena titik tidak sesuai dengan sistem koordinat yang dipilih
            assert hasil_cek, iface.messageBar().pushMessage(
                    "Peringatan","Koordinat titik yang dimasukkan tidak sesuai dengan sistem koordinat yang dipilih", level=Qgis.Warning)

        except Exception as e:
            print(e)
        
    
    def buat_titik(self, x, y, crs):
        """ buat titik di koordinat masukan """   
        # sistem koordinat yang digunakan
        proj = crs.authid()     

        if self.plot_clicked == 1 :
            # cek masukan
            print(x, y)
            print(crs.description())

            # membuat layer pada memory
            layer_titik = QgsVectorLayer(f"Point?crs="+proj, "Plot Titik", "memory")
            QgsProject.instance().addMapLayer(layer_titik)

        #memberi geometri baru pada layer
        feature_pt = QgsFeature()     
        feature_pt.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))

        # menambahkan fitur pada layer
        layer_titik = QgsProject.instance().mapLayersByName('Plot Titik')[0]
        layer_titik.dataProvider().addFeatures([feature_pt])
        layer_titik.updateExtents()

        # zoom ke layer
        self.iface.actionZoomToLayer().trigger()
    
    
    def cek_azimuth(self):
        try :
            # memanggil isi dari Line Edit pada kolom azimuth
            # sekaligus mengkonversinya menjadi angka
            az = float(self.input_az.text())

            #apabila input lebih dari 360 maka
            if az > 360 :
                az -= 360
            
            #menampilkan azimuth yang diterima
            print("nilai azimuth yang diterima : ", az)
        
        except Exception as e:
            print(e)    

        else:   
            return az


    def cek_jarak(self):
        try:
            # memanggil isi dari Line Edit pada kolom jarak
            # sekaligus mengkonversinya menjadi angka
            jarak = float(self.input_jarak.text())

            #mengecek nilai jarak 
            assert jarak < 30000, iface.messageBar().pushMessage(
                "Peringatan","Jarak yang anda masukkan melebihi batas kelengkungan bumi", level=Qgis.Warning,duration=3)
        
        except Exception as e:
            print(e)
        
        else:
            return jarak
        
    
    def hitung_koordinat(self, x, y, az, d, crs):
        #membuat geometri titik berdasar besar azimuth dan jarak dari titik awal
        titik_awal = QgsPoint(x, y)
        titik_akhir = titik_awal.project(d, az)

        #tambahkan titik akhir ke layer
        self.buat_titik(titik_akhir.x(), titik_akhir.y(), crs)

        #cek apakah QCheckBox dicentang
        if self.cek_garis.isChecked(): 
            #apabila iya, buat layer berupa garis dari titik awal ke titik akhir
            self.buat_garis(titik_awal, titik_akhir, crs)

        #ubah isi input x dan y dengan koordinat baru
        self.input_x.setText(str(titik_akhir.x()))
        self.input_y.setText(str(titik_akhir.y()))

    
    def buat_garis(self, awal, akhir, crs):
        self.plot_garis += 1
        
        # sistem koordinat yang digunakan
        proj = crs.authid()

        if self.plot_garis == 1 :
            # membuat layer pada memory
            layer_garis = QgsVectorLayer(f"LineString?crs="+proj, "Plot Garis", "memory")
            QgsProject.instance().addMapLayer(layer_garis)

        # memberi geometri pada fitur    
        feature_line = QgsFeature()
        feature_line.setGeometry(QgsGeometry.fromPolyline([awal, akhir]))

        # menambahkan fitur pada layer
        layer_garis = QgsProject.instance().mapLayersByName('Plot Garis')[0]
        layer_garis.dataProvider().addFeatures([feature_line])
        layer_garis.updateExtents()

        # zoom ke layer
        self.iface.actionZoomToLayer().trigger()
    
    
            
