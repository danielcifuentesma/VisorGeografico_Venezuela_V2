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




'''
Clase AlistamientoDatos

Accede a los Datos ubicados en el OneDrive

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
        
                   

'''
class AnalisisGeoespacial ():
    
    Contiene todos los métodos y acciones a implementar sobre las capas de información

'''



class AnalisisGeoespacial ():
    
    
    def filtrado_registros (self, gdf, columna, valor):       # Realiza una Selección Específica sobre un GeodataFrame
    
    
        if columna in gdf.columns:
            
            gdf_filtrado = gdf[gdf[columna] == valor].copy ()
            
            return  gdf_filtrado
        
        
        else:
            
            print (f'⚠️ La Columna {columna} No Existe')
            
            return gdf
            
            
        
        
    











'''
Clase VisorGeografico:


Configura el Objeto .Map y los Elementos que Contendrá.
Al final se conecta con  streamlit   


'''
    
        
 
class VisorGeografico:
    
    
    def __init__ (self):
        
        self.center = [8.893240, -64.264115]                                   # Coordenadas del Tigre (Venezuela)
        self.zoom = 12
    
    
    
    
    def _formatear_enlace (self, gdf, columnas):                               # Formatea uno o varios campos para convertirlos en hipervínculos.
                                                                               # Método que convierte la Dirección URL de los Documentos a enlazar, a formato HTML
                                                                               # La Estructura de la dirección URL en formato HTML es url_html = f'<a href="{url_documento}" target="_blank">Abrir Documento</a>'
        
        if isinstance(columnas, str):                                          # Si nos pasan un solo string, lo convertimos a lista para procesarlo igual
            
            columnas = [columnas]
            
        
        
        for col in columnas:
            
            if col in gdf.columns:
                
                gdf[col] = gdf[col].apply(
                    lambda x: f'<a href="{x}" target="_blank" style="color: #0078D4; font-weight: bold;">Ver Documento 🔗</a>' 
                    if str(x).startswith('http') else x)
                
                   
        return gdf
        
    
    
    
    
    def generacion_mapa (self, capas_dicc, columnas_enlaces=None, columnas_labels=None):
        
        
        '''
        capas_dicc = {NombreCapa:Gdf}
        columnas_enlaces = {NombreCapa: CampoURL}
        columnas_labels = {NombreCapa: CampoLabel}
        
        '''
        
        columnas_enlaces = columnas_enlaces or {}                              # Se inicializa el Dicionario de Enlaces (Hipervinculos)
        columnas_labels = columnas_labels or {}                                # Se inicializa el Diccionario de Labels
        
        
        mapa_1 = leafmap.Map (center = self.center,                            # Se crea un Objeto Tipo Mapa     
                              zoom = self.zoom)
    
        
        mapa_1.add_basemap(basemap='HYBRID',                                   # Se adiciona un Base Map
                          show=True,)
 
    
    
    
        
        for nombre, capa in capas_dicc.items():                                # Adiciona todas las Capas al Objeto Mapa
            
            if capa is not None:
                
                
                gdf_visualizacion = capa.copy()                                # Se copia el GDF para no alterar los datos originales del análisis
                
                
                
                if nombre in columnas_enlaces:                                 # Si la capa tiene una columna definida como enlace, se formatea
                    
                    gdf_visualizacion = self._formatear_enlace(gdf = gdf_visualizacion, 
                                                               columnas = columnas_enlaces [nombre])
                
                
                
                if nombre in columnas_labels:                                  # Etiqueta siempre encendida
                    
                    
                    
                   
                    mascara_css = (                                            # Definimos un halo negro para texto blanco
                        "white; "                                              # El text-shadow crea una máscara en las 4 esquinas del texto
                        "text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, "
                        "-1px 1px 0 #000, 1px 1px 0 #000, "
                        "0px 0px 5px #000;")
                    
                    mapa_1.add_labels(
                        data=gdf_visualizacion,
                        column=columnas_labels[nombre],
                        font_size="10pt",
                        font_color= mascara_css,
                        font_family="verdana",
                        font_weight="bold")         
                    
                    
                
                
                
                
                
                
                
                mapa_1.add_gdf (gdf = gdf_visualizacion,
                         layer_name = nombre,
                         info_mode = 'on_click',
                         zoom_to_layer = False)
     
        
            
        mapa_1.to_streamlit (width = 900,
                             height = 700)
            


def inicio_modelo_visor_geografico ():
    
    print ('\n MODELO DE CREACIÓN\n VISOR GEOGRÁFICO\n BLOQUES BUDARE-ELOTES Y NIPA-NARDO-NIEBLAS') 
    
    
    '''
    
    URL (Bases de Datos)
    
    '''
    
    url_drive_be = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQAM5WHa8RvARaTaSBLSaXa7AdZyOdf8IXWJm3L7fjfqOO8?e=j4uUSw'
    ur_drive_nnn = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQBHykmgrq4vT4GOOiGbIhumAYJRm7fNnt7OfkzdeFQX-ro?e=cW0Ufc'
 
    
    
    
 
 
    '''
    1- Instanciación de Clase
    
    '''
    
    datos_be = AlistamientoDatos (url_drive_be)                           
    datos_nnn = AlistamientoDatos (ur_drive_nnn)
    analisis_geoespacial = AnalisisGeoespacial ()
    visor_geografico = VisorGeografico ()
    
    '''
    2- Creación de GeodataFrames
    
    '''
    
    
    be_bloque = datos_be.cargar_capa_zip ('BloqueBE_00_CoordenadasTotalesOficiales_PG_20240911_AjusteLEC')
    be_campos = datos_be.cargar_capa_zip ('BloqueBE_00_CoordenadasCamposTotalesOficiales_PG_20240911_AjusteLEC')
    be_estaciones = datos_be.cargar_capa_zip ('PlantasEstaciones_BudareElotes_V3_20240724_AjusteLECCampo_PT')
    be_pozos =  datos_be.cargar_capa_zip ('Pozos_BE_PT_Estruct')
    
    
    
    nnn_bloque = datos_nnn.cargar_capa_zip ('Bloque_NipaNardo_V1_20240518_AjusteLEC')
    nnn_campos = datos_nnn.cargar_capa_zip ('Campos_NipaNardo_V1_20240518_AjusteLEC')
    nnn_estaciones = datos_nnn.cargar_capa_zip ('PlantasEstaciones_NipaNardo_V3_20240724_AjusteLECCampo_PT')
    nnn_pozos = datos_nnn.cargar_capa_zip ('Pozos_NNN_PT_Estruct')
    
    
    
    
    '''
    3- Análisis Geoespacial
    
    '''
    
    '''
        A. Selección de Estaciones Activas
    
    '''
    
    be_estaciones_activas = analisis_geoespacial.filtrado_registros(gdf = be_estaciones, 
                                            columna = 'Condicion', 
                                            valor = 'Activa')
    
    nnn_estaciones_activas = analisis_geoespacial.filtrado_registros(gdf = nnn_estaciones, 
                                            columna = 'Condicion', 
                                            valor = 'Activa')
    
    
    
    '''
        B. Selección de Pozos que fueron Priorizados Versión No. 1 (18/02/2026)
    '''
    
    
    be_pozos_Priorizados_v1 = analisis_geoespacial.filtrado_registros (gdf = be_pozos,                           # Selección de Pozos BE, que fueron priorizados Versión No. 1 (18/02/2026)
                                             columna = 'PrioridadVersion',
                                             valor = 'Versión No. 1 (18/02/2026)')
    
    
    nnn_pozos_Priorizados_v1 = analisis_geoespacial.filtrado_registros (gdf = nnn_pozos,                         # Selección de Pozos NN, que fueron priorizados Versión No. 1 (18/02/2026)
                                             columna = 'PrioridadVersion',
                                             valor = 'Versión No. 1 (18/02/2026)')
    
    
    
    '''
    
        C. Pozos de la Prueba Piloto
    '''
    
    
    be_pozos_prueba_piloto = analisis_geoespacial.filtrado_registros (gdf = be_pozos,                           # Selección de Pozos BE, que fueron definidos para la Pruba Piloto
                                             columna = 'PruebaPiloto',
                                             valor = 'SI (19/02/2026)')
    
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.filtrado_registros (gdf = nnn_pozos,                           # Selección de Pozos BE, que fueron definidos para la Pruba Piloto
                                             columna = 'PruebaPiloto',
                                             valor = 'SI (19/02/2026)')
    
    
    
    
    
    
    print ('BLOQUE BE: ', be_bloque.columns)
    
    print ('BLOQUE NNN: ',nnn_bloque.columns)
    
    print ('Pozos BE:', be_pozos.columns)
    
    
    print ('Pozos (Budare Elotes): Prueba Piloto:', len (be_pozos_prueba_piloto))
    
    print ('Pozos (Nipa-Nardo-Nieblas): Prueba Piloto:', len (nnn_pozos_prueba_piloto))
    
    
    
    capas_dicc = {'Bloque Budare-Elotes': be_bloque,                           # Diccionario con el Nombre y Gdf que se adicionarán al Objeto Mapa (LeafMap)
                  'Bloque Nipa-Nardo-Nieblas': nnn_bloque,
                  'Campos (Budare-Elotes):':  be_campos,
                  'Campos (Nipa-Nardo-Nieblas)': nnn_campos,
                  'Estaciones (Budare-Elotes)':be_estaciones,
                  'Estaciones (Nipa-Nardo-Nieblas)': nnn_estaciones,
                  'Estaciones Activas (Budare-Elotes)':be_estaciones_activas,
                  'Estaciones Activas (Nipa-Nardo-Nieblas)': nnn_estaciones_activas, 
                  'Pozos (Budare Elotes)': be_pozos,
                  'Pozos (Nipa-Nardo-Nieblas)': nnn_pozos,
                  'Pozos (Budare Elotes): Priorizados. Versión No. 1 (18/02/2026)':  be_pozos_Priorizados_v1,
                  'Pozos (Nipa-Nardo-Nieblas): Priorizados. Versión No. 1 (18/02/2026)': nnn_pozos_Priorizados_v1,
                  'Pozos (Budare Elotes): Prueba Piloto':  be_pozos_prueba_piloto,
                  'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': nnn_pozos_prueba_piloto 
                  }
    
    
    '''
    HIPERVÍNCULOS
    
    '''
    
    campos_be = [
        'URL_DiagramaPozo', 
        'URL_FichaCompletacion', 
        'URL_HistoriaPozo', 
        'URL_EvaluacionFormacion', 
        'URL_DiagnosticoAmbiental2024']
    
    
    campos_nn = [
        'URL_DiagramaPozo', 
        'URL_FichaCompletacion', 
        'URL_HistoriaPozo', 
        'URL_EvaluacionFormacion', 
        'URL_DiagnosticoAmbiental2024']
    
    columnas_hipervinculo = {'Pozos (Budare Elotes): Prueba Piloto': campos_be,                                        # Diccionario con el Nombre de Gdf y sus campos donde existe una Dirección URL para realizar los hipervinculos 
                             'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': campos_nn}                                    
    
    
    columnas_labels = {'Pozos (Budare Elotes): Prueba Piloto': 'UWISuperf',
                       'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': 'UWISuperf',
                       'Estaciones Activas (Budare-Elotes)': 'ID',
                       'Estaciones Activas (Nipa-Nardo-Nieblas)': 'ID'}
    
    
    
    
    '''
    GENERACIÓN DEL MAPA
    '''
    
    
    
    visor_geografico.generacion_mapa(capas_dicc = capas_dicc,                           # Se envían las capas que se incluirán en el Objeto Mapa
                                     columnas_enlaces = columnas_hipervinculo,
                                     columnas_labels = columnas_labels)         
    
    
    
    print ('    ✅ Modelo Ejecutado')
    
    
if __name__ == '__main__':              # Modismo de Python que se utiliza para garantizar que la función principal del programa (inicio_modelo_visor_geografico ()) solo se ejecute cuando el script se esté corriendo directamente, y no cuando el script sea importado como un módulo en otro programa. 

    
    inicio_modelo_visor_geografico ()