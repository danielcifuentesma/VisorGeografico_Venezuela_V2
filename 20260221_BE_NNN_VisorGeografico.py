# --*- coding: utf-8 -*-
"""
Created on Fri Feb 20 20:36:31 2026

@author: Daniel
"""

import geopandas as gpd
import streamlit as st
import leafmap.foliumap as leafmap
import requests
import tempfile
import os
import zipfile
import shutil
from datetime import datetime                                                  # Del Modulo Datetime, se importa la Clase Date para poder actualizar el Script con la Fecha actual



'''
Clase AlistamientoDatos



'''

class AlistamientoDatos:
    
    
    def __init__(self, url_drive):
        self.url_drive = url_drive
        self.url_directa = self.convertir_url(self.url_drive)

    def convertir_url(self, url):
        """
        Versión para SharePoint Business.
        Forzamos el parámetro de descarga directa.
        """
        if "sharepoint.com" in url:
            # Limpiamos el link de parámetros previos y forzamos download=1
            base_url = url.split("?")[0]
            return f"{base_url}?download=1"
        return url

    #@st.cache_data
    
        
    def cargar_capa_zip(_self, nombre_capa):
    
        temp_dir = tempfile.mkdtemp()
        try:
            response = requests.get(_self.url_directa, timeout=30)
            
            # --- DIAGNÓSTICO DE INGENIERÍA ---
            print(f"\n--- REVISANDO CAPA: {nombre_capa} ---")
            print(f"Status: {response.status_code}")
            print(f"Tamaño: {len(response.content) / 1024:.2f} KB")
            print(f"Primeros 100 caracteres: {response.text[:100]}") # Ver si es HTML o binario
            
            if response.status_code != 200:
                return None
            # ---------------------------------

            zip_path = os.path.join(temp_dir, "datos.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)

            # Verificamos si es un ZIP válido antes de abrirlo
            if not zipfile.is_zipfile(zip_path):
                print("❌ ERROR: El archivo descargado NO es un ZIP válido. Probablemente es una página de login de Microsoft.")
                return None

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            ruta_gdb = None
            for raiz, carpetas, archivos in os.walk(temp_dir):
                for carpeta in carpetas:
                    if carpeta.endswith(".gdb"):
                        ruta_gdb = os.path.join(raiz, carpeta)
                        break
            
            if not ruta_gdb:
                print("❌ No se encontró carpeta .gdb dentro del ZIP.")
                return None

            gdf = gpd.read_file(ruta_gdb, layer=nombre_capa, engine='pyogrio')
            
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
                
            cols_fecha = gdf.select_dtypes(include=['datetime64', 'datetimetz']).columns
            
            for col in cols_fecha:
                
                gdf[col] = gdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            return gdf

        except Exception as e:
            print(f"❌ ERROR CRÍTICO: {e}")
            return None
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
                   

    
    def fecha_modelo (self):                                                   # Método para calcular la Fecha en la cual se corre el modelo
        
        self.fecha_actual = datetime.now ()                                    # Obtiene la fecha y hora actual como un objeto datetime
        self.fecha_actual_format = self.fecha_actual.strftime('%Y%m%d')
        
        self.fecha_dma_str = self.fecha_actual.strftime('%d/%m/%Y')
        self.fecha_modelo_colum = self.fecha_actual.date ()                    # Este es el tipo de dato preferido para una columna de fecha en Pandas.
        
        
        
 
class VisorGeografico:
    
    
    def __init__ (self):
        
        self.center = [8.893240, -64.264115]                                   # Coordenadas del Tigre (Venezuela)
        self.zoom = 12
    
    
    
    def generacion_mapa (self, capas_dicc):
        
        
        '''
        capas_dicc = {NombreCapa:Gdf}
        
        '''
        
        
        mapa_1 = leafmap.Map (center = self.center,                            # Se crea un Objeto Tipo Mapa     
                              zoom = self.zoom)
    
        
        mapa_1.add_basemap(basemap='HYBRID',                                    # Se adiciona un Base Map
                          show=True,)
 
        
        for nombre, capa in capas_dicc.items():                                        # Adiciona todas las Capas al Objeto Mapa
            
            if capa is not None:
                
                mapa_1.add_gdf (gdf = capa,
                         layer_name = nombre,
                         info_mode = 'on_click',
                         zoom_to_layer = True)
     
        
            
        mapa_1.to_streamlit (width = 800,
                             height = 600)
            


def inicio_modelo_visor_geografico ():
    
    print ('\n MODELO DE CREACIÓN\n VISOR GEOGRÁFICO\n BLOQUES BUDARE-ELOTES Y NIPA-NARDO-NIEBLAS') 
    
    
    '''
    
    URL (Bases de Datos)
    
    '''
    
    url_drive_be = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQB7c0C5326QTYAR63RSjGpmAS1wPW-gOFfpK8BtJKa_DUg?e=QONC1e'
    ur_drive_nnn = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQA6J7fhOvXcS6RSY3LetrRwAd_srk31sqy6uZ6NzlalHlk?e=WeP3Wx'
 
    
    
    
 
 
    '''
    1- Instanciación de Clase
    
    '''
    
    datos_be = AlistamientoDatos (url_drive_be)                           
    datos_nnn = AlistamientoDatos (ur_drive_nnn)
    
    visor_geografico = VisorGeografico ()
    
    '''
    2- Creación de GeodataFrames
    
    '''
    
    
    be_bloque = datos_be.cargar_capa_zip ('BloqueBE_00_CoordenadasTotalesOficiales_PG_20240911_AjusteLEC')
    be_campos = datos_be.cargar_capa_zip ('BloqueBE_00_CoordenadasCamposTotalesOficiales_PG_20240911_AjusteLEC')
    be_pozos =  datos_be.cargar_capa_zip ('Pozos_BE_PT_Estruct')
    
    
    
    
    
    nnn_bloque = datos_nnn.cargar_capa_zip ('Bloque_NipaNardo_V1_20240518_AjusteLEC')
    nnn_campos = datos_nnn.cargar_capa_zip ('Campos_NipaNardo_V1_20240518_AjusteLEC')
    nnn_pozos = datos_nnn.cargar_capa_zip ('Pozos_NNN_PT_Estruct')
    
    
    
    
    print ('BLOQUE BE: ', be_bloque.columns)
    
    print ('BLOQUE NNN: ',nnn_bloque.columns)
    
    print ('Pozos BE:', be_pozos.columns)
    
    
    capas_dicc = {'Bloque Budare-Elotes': be_bloque,                           # Diccionario con el Nombre y Gdf que se adicionarán al Objeto Mapa (LeafMap)
                  'Bloque Nipa-Nardo-Nieblas': nnn_bloque,
                  'Campos (Budare-Elotes):':  be_campos,
                  'Campos (Nipa-Nardo-Nieblas)': nnn_campos,
                  'Pozos (Budare Elotes)': be_pozos,
                  'Pozos (Nipa-Nardo-Nieblas)': nnn_pozos
                  }
    
    #'Pozos (Budare Elotes)': be_pozos,
    #'Pozos (Nipa-Nardo-Nieblas)': nnn_pozos
    
    visor_geografico.generacion_mapa(capas_dicc)                               # Se envían las capas que se incluirán en el Objeto Mapa
    
    
    
    print ('    ✅ Modelo Ejecutado')
    
    
if __name__ == '__main__':              # Modismo de Python que se utiliza para garantizar que la función principal del programa (inicio_modelo_visor_geografico ()) solo se ejecute cuando el script se esté corriendo directamente, y no cuando el script sea importado como un módulo en otro programa. 

    
    inicio_modelo_visor_geografico ()