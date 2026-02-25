# --*- coding: utf-8 -*-
"""
Created on Fri Feb 20 20:36:31 2026

@author: Daniel
"""

import geopandas as gpd
import pandas as pd
import streamlit as st
import leafmap.foliumap as leafmap
import leafmap.common as leafmap_tools
import folium
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
            
            
            if hasattr(gdf, 'crs') and gdf.crs is not None:
                
                if gdf.crs != "EPSG:4326":
                   
                    gdf = gdf.to_crs(epsg=4326)
            
            else:
                # Si entra aquí, es una tabla pura (como be_reservas_TB)
                print(f"ℹ️ La capa '{nombre_capa}' se cargó como Tabla (sin geometría).")
            
            # ---------------------------------------------------------

            # Formateo de fechas (esto funciona tanto para GeoDataFrames como DataFrames)
            cols_fecha = gdf.select_dtypes(include=['datetime64', 'datetimetz']).columns
            
            for col in cols_fecha:
                gdf[col] = gdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            return gdf
            
            
        except Exception as e:
            
            print(f"❌ ERROR CRÍTICO en {nombre_capa}: {e}")
            return None
            
        
        finally:
            
            # Limpieza del directorio temporal
            
            if os.path.exists(temp_dir):
                
                shutil.rmtree(temp_dir)   

      
        
                   

'''
class AnalisisGeoespacial ():
    
    Contiene todos los métodos y acciones a implementar sobre las capas de información

'''



class AnalisisGeoespacial ():
    
    
    def filtrado_registros (self, gdf, columna, valor):                        # Realiza una Selección Específica sobre un GeodataFrame
    
    
        if columna in gdf.columns:
            
            gdf_filtrado = gdf[gdf[columna] == valor].copy ()
            
            return  gdf_filtrado
        
        
        else:
            
            print (f'⚠️ La Columna {columna} No Existe')
            
            return gdf
            
            
        
    def join_tables (self, df_left, df_right, df_left_key, df_right_key, how): # Permite realizar Uniones entre DataFrames
    
    
        if df_left is None or df_right is None:
            
            print("⚠️ Uno de los DataFrames es None. No se puede realizar el Join.")
            
            return df_left
        
        
        df_join = df_left.merge (df_right,
                       left_on = df_left_key,
                       right_on = df_right_key,
                       how = how,
                       suffixes= ('', '_tabla') )                              # Evita nombres de columnas duplicados)
        
        print(f"✅ Join exitoso: {len(df_join)} registros resultantes.")
        
        return df_join
    
    
    
    def vincular_tabla_1_a_muchos (self, gdf_padre, df_hijo, gdf_padre_Key, df_hijo_key, columnas_interes, boton_nombre):    # Crea una Columna en el Gdf padre para contener una tabla HTML 
                                                                                                                             # con todos los registros relacionados de la Tabla Hija
                                                                                                                             # gdf_padre = Es el Geodataframe
                                                                                                                             # df_hijo = Es la Tabla a Relacionar. Tiene n registros asociados a 1 gdf_padre
                                                                                                                             # gdf_padre_Key = Es la Llave del gdf_padre
                                                                                                                             # df_hijo_key = Es la llave de df_hijo
                                                                                                                             # columnas_interes = Lista con las columnas de df_hijo, que se desean visualizar en el popUp del Mapa
                                                                                                                             # boton_Nombre = Es el Nombre de la Columna Nueva que aparecerá en el popUp del Mapa
        
        
        def generar_html_resumen (uwi):                                        # Se filtran todos los Registros para el ID Específico   
        
            
            registros = df_hijo[df_hijo [df_hijo_key] == uwi]                  # Realiza una Máscara con los registros de df_hijo_key, cuyo ID conincide con el de gdf_padre
            
            if registros.empty:                                                # Si No existe asociación de registros, se devuelve un texto para evitar errores o vacíos.
                
                return 'Sin Registros asociados'
            
            
            registros_vista = registros [columnas_interes].copy ()             # Crea una Copia de los Registros, únicamente con las Columnas que 
                                                                               # se desean visualizar en el popUp
                                                                               
                                                                               
            '''
                to_html: Este es el elemento clave. Convierte el pedazo de tabla de reservas en código HTML puro
                index =False: Quita la columna de números de la izquierda para que la tabla se vea más limpia
                classes: Inyecta clases de Bootstrap. Como Streamlit usa este framework, la tabla heredará un diseño profesional (filas intercaladas con color y efecto al pasar el mouse).
            '''
            
            
            
            html_tabla = registros_vista.to_html (index = False,
                                                  classes = 'table table-striped table-hover table-sm',
                                                  justify ='center',
                                                  border = 0)

            return f"""
        <div style="max-height: 250px; max-width: 450px; overflow-y: auto; overflow-x: auto; border: 1px solid #ccc; padding: 5px;">            
            <p style="font-weight: bold; margin-bottom: 5px; color: #0078D4;">Resumen de Reservas:</p>
            {html_tabla}
        </div>
        """       # Se envuelve en un div para controlar el scroll si son muchos registros                                                 
      
    
    
        gdf_padre [boton_nombre] = gdf_padre [gdf_padre_Key].apply (generar_html_resumen)         # Se aplica la función para crear la Columna de boton_nombre
                                                                                                  # .apply (): La función recorre cada registro de gdf_padre. Para cada uno, toma el valor de
                                                                                                  # gdf_padre_Key y se lo pasa al parámetro uwi de la función def generar_html_resumen (uwi):.
                                                                                                  # El resultado lo guarda en la nueva columba.
                                                                                                  # Ahora cada registro de gdf_padre, tiene un botón con acceso a los registros asociados con df_hijo
    
        print (f' ✅ Relación 1:Muchos en la columna {boton_nombre}')
        
        return gdf_padre



'''
Clase Simbología:
    
    Configura la Simbología de los Gdf que se incluirán en el Mapa.
'''



class Simbologia:
    
    
    
                                                                               #  def estilo_poligono (). Define los Parámetros SGV por defecto para la Simbología de los Polígonos. Se basan en https://leafletjs.com/reference.html#path
    def estilo_poligono (self, fill_color = '#ef91f2',
                          color = '#e813f0',
                          weight = 1.5,
                          opacity = 1.0,
                          fill_opacity = 0.4,
                          campo_dinamico = None,
                          simbologia_colores = None):
        
        '''
            fill_color:  Color de Relleno por Defecto
            color : Color de Borde por Defecto
            weight: Grosor de la Línea
            fillOpacity: Transparencia
            campo_dinamico:  Nombre de la Columna para variar la Simbología (OPCIONAL)
            simbologia_colores: Dicionario {valor: color} asociado al Campo Dinámico
        
        
        '''
        
        
        def estilo_poligono_final (feature):                                   # Aplica la Lógica para asignar la Simbología al GDF
    
            '''
                1. Si el GDF únicamente tiene una Simbología se inicia con los Valores Estáticos definidos en def estilo_poligono ()
            
            '''
                                                                               # estilo = {} con los Parámetros por Defecto.
            estilo = {'fillColor': fill_color,
                      'color': color,
                      'weight': weight,
                      'fill_opacity': fill_opacity,
                      'opacity': opacity}


            '''
                2- Si para el GDF se definió un campo Dinámico sobre el cual, la Simbología varía. Se modifica el parámetro fillColor
            
            '''

            if campo_dinamico and simbologia_colores:                          # Si estos 2 campos tienen valores diferentes de None, se activa el Condicional
                
                
                valor_atributo = feature ['properties'].get (campo_dinamico)
                
                estilo ['fillColor'] = simbologia_colores.get ( valor_atributo, fill_color)             # Si el valor no está en simbologia_colores, usará el fill_color original.


            return estilo
        
        
        return estilo_poligono_final
    
    
    
    
    def estilo_punto_icono (self, feature, campo_dinamico, simbologia_colores_pt,               # Extrae la Configuración del Ícono para un Punto Específico
                            icon = 'info-sign',
                            color = 'gray',
                            prefix = 'glyphicon'):               

        '''
            feature: Registro de la Estructura geoJSON
            campo_dinamico: Nombre de la Columna para variar la Simbología (OPCIONAL)
            simbologia_colores_pt: Dicionario {valor: color} asociado al Campo Dinámico
            
        
        '''
        
            # 1. Se define el Estilo por Defecto:
        
        estilo_icono_pt = {'icon': icon,
                           'color': color,
                           'prefix': prefix}
        
        
            # 2. Se extrae el valor de la columna seleccionada para cambiar la simbología (OPCIONAL)
            
        
        valor_atributo_pt = feature ['properties'].get (campo_dinamico)              # Se extrae el Valor de la Columna
        
        
            # 3. sI
        
        return simbologia_colores_pt.get (valor_atributo_pt, estilo_icono_pt)        # Si encuentra el valor en el diccionario, devuelve su config personalizada
                                                                                     # Si NO lo encuentra, devuelve el 'estilo_defecto' (el gris con info-sign).
    




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
    
    
    
    def _ajuste_estilos_popups (self, mapa):                                   # Ajusta el CSS (Cascading Style Sheets (Hojas de Estilo en Cascada))
                                                                               # Si el HTML es el esqueleto o la estructura de una página web, el CSS es la "capa de pintura", el diseño y la estética.
                                                                               # Código HTML que únicamente se lee en la páguna HTML. No en el entorno Python. Por eso, se encuentra ''' '''
                                                                               # Activa el Scroll para garantizar que el texto no se salga del PopUp
        
        estilo = """
        <style>
            /*1. Ajuste del contenedor que permite el redimensionamiento*/
            
            .leaflet-popup-content {
                
                /*  2. Propiedades Iniciales de Dimensionamiento  */
                
                width: 500px; 
                height: 300px;
                
                /*  3. Funcionalidad Elástica del PopUP  */
                
                /* PROPIEDAD CLAVE: Permite ajustar el tamaño con el mouse */
                
                resize: both !important;
                
                /* IMPORTANTE: Para que 'resize' funcione, overflow no puede ser 'visible' */
                
                overflow: auto !important;
                
                
               /*  4. límites de Seguridad: Se definen límites para que el usuario no rompa la interfaz */
               
                min-width: 250px !important;
                min-height: 150px !important;
                max-width: 900px !important;
                max-height: 700px !important;
                padding-right: 10px;
                
                /*  5- Tipografía y Tamaño (Legibilidad Técnica) */
                
                font-family:'Century Gothic', CenturyGothic, AppleGothic, sans-serif;
                font-size: 11px; /* Se mantiene el tamaño compacto para los datos */
                line-height: 1.4; /* Mejora el espacio entre líneas de la tabla */
                padding-right: 15px;
                margin: 13px 19px !important;
                
            }
            /* 6- Ajuste específico para el Envoltorio las tablas dentro del popup */
            
            .leaflet-popup-content-wrapper {
                width: auto !important;
                height: auto !important;
                display: inline-block !important; /* Permite que la caja crezca con el contenido */
                border-radius: 8px !important;
            }
            
            /* 3. Ajuste del CONTENEDOR MAESTRO (Evita que Leaflet fuerce el ancho) */
            
            .leaflet-popup {
                width: auto !important;
            }
            
            /* Para que el icono de resize se vea mejor */
            
            .leaflet-popup-content::-webkit-resizer {
                background-color: #f1f1f1;
                outline: 1px solid #ccc;
                width: 12px;
                height: 12px;
            }
                
                
        </style>
        """        

        mapa.get_root().header.add_child(leafmap.folium.Element(estilo))       # Se añade el estilo al header del mapa
                                                                               # mapa = Objeto de leafmap.foliumap
                                                                               # .get_root() = librería "invisible" que usa folium y leafmap para gestionar el HTML).
                                                                               # Este método accede al objeto Figure de nivel superior. En desarrollo web, esto es el equivalente a tomar el documento HTML completo antes de que se convierta en página web. Sin este método, solo estarías hablando con el "área del mapa" y no con la "estructura del archivo".
                                                                               # header = Clase: branca.element.Figure.Qué hace: Referencia específicamente a la etiqueta <head> del archivo HTML resultante. Es el lugar sagrado donde se colocan los estilos CSS, los títulos de la pestaña y los enlaces a librerías externas. Al llamar a .header, le dices a Python: "Lo que voy a enviarte no es un dato para el mapa (como un pozo), sino una instrucción de configuración".
                                                                               # .add_child()  = Clase: branca.element.Element. Es el método estándar de Folium/Branca para anidar componentes. Se encarga de colocar físicamente tu código dentro de la sección que elegiste (header). Si el header fuera una carpeta física, .add_child() sería la mano que mete el documento dentro.
                                                                               # leafmap.folium.Element(estilo) Librería/Clase: folium.elements.Element (expuesto a través de leafmap).Convierte tu texto de "Ajuste del contenedor general..." en una instrucción que el navegador sabrá leer como una regla de diseño.
    
    
    
    def _leyenda_dinamica (self, capa_iconos):                                 # Recorre la configuración de los Íconos y Extrae Automáticamente
                                                                               # los pares {etiqueta:Color} para la Leyenda
    
    
        leyenda_auto = {}
        
        
        for nombre_capa, config in capa_iconos.items ():                       # Recorre cada Capa Configurada
        
            mapeo = config.get ('mapeo', {})
            
            
            for valor, estilo in mapeo.items ():                               # Recorre cada Regla de Estilo
            
                texto_leyenda = estilo.get ('label', f'{nombre_capa} - {valor}')        # Busca si Existe un Label definido, Si NO, se usa el valor numérico
                
                color = estilo.get ('color', 'gray')                           # Se extrae el Color. Si no se encuentra definido, se define 'gray'
                
                leyenda_auto [texto_leyenda] = color                           # Se agrega al Diccionario Final
                
        
        
        return leyenda_auto
         
        
            
    
    
    
    
    
    
    def generacion_mapa (self, capas_dicc, columnas_enlaces=None, columnas_labels=None, capa_estilos = None, capa_iconos = None):
        
        
        '''
        capas_dicc = {NombreCapa:Gdf}
        columnas_enlaces = {NombreCapa: CampoURL}
        columnas_labels = {NombreCapa: CampoLabel}
        capa_estilos = {NombreCapa: función de estilo}
        capa_iconos = {NombreCapa: {Campo Dinámico:{Atributo: Opciones Personalización}}}
        
        '''
        
        # 1- Se inicializan los Diccionarios para evitar errores si llegan vacíos
        
        
        columnas_enlaces = columnas_enlaces or {}                              # Se inicializa el Dicionario de Enlaces (Hipervinculos)
        columnas_labels = columnas_labels or {}                                # Se inicializa el Diccionario de Labels
        capa_estilos = capa_estilos or {}                                      # Se inicializa el Diccionario
        capa_iconos = capa_iconos or {}                                        # Se inicializa el Diccionario
        
        
        
        # 2A- CONFIGURACIÓN DEL MAPA
        
        mapa_1 = leafmap.Map (center = self.center,                            # Se crea un Objeto Tipo Mapa     
                              zoom = self.zoom)
         
        mapa_1.add_basemap(basemap='HYBRID',                                   # Se adiciona un Base Map
                          show=True,)
        
        
        # 2B-TÍTULO DEL MAPA
        
        estilo_titulo = {
            'font-family': 'Century Gothic, sans-serif',                       # Propiedades CSS
            'font-weight': 'bold',
            'color': '#333333',              # Texto gris oscuro
            'background-color': 'rgba(255, 255, 255, 0.8)', # Fondo blanco al 80% de opacidad
            'padding': '10px',               # Espacio interno
            'border-radius': '10px',         # Bordes redondeados
            'box-shadow': '0px 0px 5px rgba(0,0,0,0.3)', # Sombra suave
            'z-index': '9999'                # Asegura que quede encima de todo
                          }
        
        
        mapa_1.add_title (title = 'VISOR GIS <br> BLOQUES BUDARE - ELOTES <br> NIPA - NARDO - NIEBLA <br> VERSIÓN DE PRUEBA',
                          align ='center',
                          font_size = '16px',
                          style = estilo_titulo)
        
        
        
        # 2C. MEDICIÓN DE LONGITUDES / ÁREAS
        
        
        control_medicion_1 = folium.plugins.MeasureControl (position = 'topleft',
                                       primary_length_unit = 'meters',
                                       secondary_length_unit = 'kilometers',
                                       primary_area_unit = 'sqmeters',
                                       secondary_area_unit = 'acres')
        
        
        mapa_1.add_child (control_medicion_1)
        
        
        
        # 2.D. PRESENTACIÓN DE COORDENADAS
        
        
        formatter_lat = "function(num) {return 'Latitud: ' + L.Util.formatNum(num, 5);};"                 # Script de Java que evita que aparezcan números con 15 decimales flotantes   
        formatter_lon = "function(num) {return 'Longitud: ' + L.Util.formatNum(num, 5);};"     
        
        coordenadas_wgs84_1 = folium.plugins.MousePosition (position ='bottomright',
                                                            separator =' / ',
                                                            empty_string ='Fuera de Rango',
                                                            lng_first = True,
                                                            num_digits = 5,
                                                            prefix = 'WGS84',
                                                            lat_formatter = formatter_lat,
                                                            lng_formatter = formatter_lon)
        
        
        mapa_1.add_child (coordenadas_wgs84_1)
        
        
        
        
        # 2E- GENERACIÓN MINI MAPA
        
        '''
            
            Si bien, leafmap tiene un método add_minimap (), los parámetros definidos son muy básicos, según lo 
            establecido por folium class folium.plugins.MiniMap ().Por esta razón, utilizamos a Folium para crear
            el Objeto mini_mapa_1.
            
            Para vincular este objeto al Mapa, es necesario utilizar el método .add_child () de Folium.
            Toma este objeto externo (el minimapa configurado a mano) y pégalo dentro de mi lienzo
            
            
        '''
        
         
        mini_mapa_1 = folium.plugins.MiniMap (tile_layer = 'OpenStreetMap',
                            position = 'bottomleft',
                            width = 200,
                            height = 200,
                            zoom_level_offset = -5,                            # La diferencia de zoom entre el mapa principal y el mini mapa.Fórmula: $Zoom_{Mini} = Zoom_{Principal} + Offset$
                            toggle_display = True)                             # Define si se muestra un pequeño botón (flecha) para minimizar/ocultar el mini mapa.
        
        
        mapa_1.add_child (mini_mapa_1)        
        
        
        
        
        
        
        self._ajuste_estilos_popups (mapa_1)                                   # Se llama al método ajuste_estilos_popups para Incluir los Scrol a los PopUps
    
        
    
        simbologia_aux = Simbologia()                                          # Se instancia la Clase Simbología para acceder al Método estilo_punto_icono
    
        
       # Bucle Principal que recorre las Capas de entrada
    
    
        for nombre, capa in capas_dicc.items():                                # Adiciona todas las Capas al Objeto Mapa
            
            if capa is not None:
                
                
                gdf_visualizacion = capa.copy()                                # Se copia el GDF para no alterar los datos originales del análisis
                
                estilo_func = capa_estilos.get (nombre)
                
                
                # 1. FORMATEO DE HIPERVÍNCULOS
                
                if nombre in columnas_enlaces:                                 # Si la capa tiene una columna definida como enlace, se formatea
                    
                    gdf_visualizacion = self._formatear_enlace(gdf = gdf_visualizacion, 
                                                               columnas = columnas_enlaces [nombre])
                
                
                # 2. LABELS CON MÁSCARA CSS   
                    
                
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
                    
                    
                # 3. ICONOS PARA GDF = PUNTOS
                
                
                if nombre in capa_iconos:
                    
                    config_capa = capa_iconos[nombre]
                    
                    grupo_capa = folium.FeatureGroup (name = nombre)           # Crea el Grupo de Capa. Permite Encender/Apagar las Capas en el Layer Control
                    
                    
                    for i, fila in gdf_visualizacion.iterrows():               # Recorre cada Registro Individualmente. i es el índice (ID) y fila contiene los datos (Atributos+Geometría)
                        
                        config_final = simbologia_aux.estilo_punto_icono(      # Permite obtener la Configuración del Ícono
                            feature={'properties': fila},
                            campo_dinamico=config_capa['campo'],
                            simbologia_colores_pt=config_capa['mapeo']
                        )
                        
                        # 1. TRANSPOSICIÓN Y LIMPIEZA DE DATOS (Recuperar Verticalidad)
                        
                        df_fila = gdf_visualizacion.loc[[i]].drop(columns=['geometry'], errors='ignore')   # Se usa .loc[[i]] para evitar el IndexError
                        
                        df_vertical = df_fila.transpose().reset_index()                                    # Transpone los datos: De Horizontal a Vertical (Atributo/Valor)
                        
                        df_vertical.columns = ['Atributo', 'Valor']                                        # Se Renombran las cabeceras
                        
                        # 2. GENERAR TABLA HTML RAW (Sin estilos feos por defecto)
                        
                        tabla_html = df_vertical.to_html(
                            index=False,
                            header=True,
                            border=0,                                          # Se quitqn los bordes dobles antiguos
                            escape=False,                                      # Mantiene los enlaces vivos
                            classes='styled-table'                             # Clase para nuestro CSS personalizado
                        )
                        
                        # 3. INYECTAR ESTILOS CSS (Recuperar estética Century y colores)
                       
                        estilo_css = """
                        <style>
                            .styled-table {
                                font-family: 'Century Gothic', 'Century', sans-serif;
                                border-collapse: collapse;
                                width: 100%;
                                font-size: 12px;
                            }
                            .styled-table td, .styled-table th {
                                border: 1px solid #ddd;
                                padding: 8px;
                            }
                            /* Color de fondo para filas pares (Efecto Zebra) */
                            .styled-table tr:nth-child(even){background-color: #f2f2f2;}
                            
                            /* Efecto Hover al pasar el mouse */
                            .styled-table tr:hover {background-color: #ddd;}
                            
                            /* Estilo del Encabezado (Atributo / Valor) */
                            .styled-table th {
                                padding-top: 10px;
                                padding-bottom: 10px;
                                text-align: left;
                                background-color: #4CAF50; /* O el color corporativo que prefieras */
                                color: white;
                            }
                            /* Negrita para la columna de Atributos (Primera columna) */
                            .styled-table td:first-child {
                                font-weight: bold;
                                color: #333;
                                width: 40%; /* Ancho fijo para la etiqueta */
                            }
                        </style>
                        """
                        
                        # 4. ARMAR EL POPUP FINAL (CSS + Scroll + Tabla)
                        
                        html_completo = f"""
                        {estilo_css}
                        <div style="max-height: 300px; overflow-y: auto;">
                            {tabla_html}
                        </div>
                        """

                        # 5. CREAR MARCADOR Y LO AÑADE AL GRUPO CREADO
                       
                        folium.Marker(
                            location=[fila.geometry.y, fila.geometry.x],
                            icon=folium.Icon(
                                icon=config_final['icon'],
                                color=config_final['color'],
                                prefix=config_final['prefix']
                            ),
                            popup=folium.Popup(html_completo, max_width=450)
                        ).add_to(grupo_capa)                                   # Se añade el folium.map.FeatureGroup
                        
                    
                    grupo_capa.add_to (mapa_1)                                 # Se añade el Grupo completo al Mapa
                                       
                                
                
                else:
                    
                    mapa_1.add_gdf(
                        gdf = gdf_visualizacion,
                        layer_name = nombre,
                        info_mode = 'on_click',
                        zoom_to_layer = False,
                        style_function = estilo_func
                    )
                    
        
        dicc_leyenada_final = self._leyenda_dinamica(capa_iconos)              # Se llama al método _leyenda_dinamica
        
        
        if dicc_leyenada_final:
            
            mapa_1.add_legend (title = 'CONVENCIONES',                         # Se adiciona la Leyenda al Mapa
                               legend_dict =  dicc_leyenada_final)
      
        
            
        mapa_1.to_streamlit (width = 900,
                             height = 700)
            


def inicio_modelo_visor_geografico ():
    
    print ('\n MODELO DE CREACIÓN\n VISOR GEOGRÁFICO\n BLOQUES BUDARE-ELOTES Y NIPA-NARDO-NIEBLAS') 
    
    
    '''
    
    URL (Bases de Datos)
    
    '''
    
    url_drive_be = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQB09BUzYmdwRItVi2O_JKxdAQtgQQqW1TyiXgOG1_H_0SI?e=OYV6rD'
    ur_drive_nnn = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQD8Q0kbD-IOQLFS1TcLE9SIAaKjjfr53MzJUz0yb_Aq8Kk?e=eTMqnq'
 
    
    
    
 
 
    '''
    1- Instanciación de Clase
    
    '''
    
    datos_be = AlistamientoDatos (url_drive_be)                           
    datos_nnn = AlistamientoDatos (ur_drive_nnn)
    analisis_geoespacial = AnalisisGeoespacial ()
    simbologia = Simbologia ()
    visor_geografico = VisorGeografico ()
    
    '''
    2A- Creación de GeodataFrames
    
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
    
    2B- Creación de Dataframes
    '''
    
    be_reservas_TB = datos_be.cargar_capa_zip ('PruebaPiloto_Reservas_TB_20260219')
    
    
    
    
    
    
    
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
    
    
    '''
    
       D-  PRESENTACIÓN DE RESERVAS (JOIN)
    '''
    
    be_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = be_pozos_prueba_piloto,
                                                    df_hijo = be_reservas_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'ID_UWISuperf',
                                                    columnas_interes = ['ID_UWISuperf',
                                                                        'Bloque',
                                                                        'Campo',
                                                                        'FechaPerforacion',
                                                                        'FechaCompletamiento',
                                                                        'FechaIniProduccion',
                                                                        'FechaFinProduccion',
                                                                        'ArenasCompletadas',
                                                                        'CumOil_kBls',
                                                                        'CumGas_MMscf',
                                                                        'CumWater_KBls'],
                                                    boton_nombre = 'Informacion_Reservas')
    
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = nnn_pozos_prueba_piloto,
                                                    df_hijo = be_reservas_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'ID_UWISuperf',
                                                    columnas_interes = ['ID_UWISuperf',
                                                                        'Bloque',
                                                                        'Campo',
                                                                        'FechaPerforacion',
                                                                        'FechaCompletamiento',
                                                                        'FechaIniProduccion',
                                                                        'FechaFinProduccion',
                                                                        'ArenasCompletadas',
                                                                        'CumOil_kBls',
                                                                        'CumGas_MMscf',
                                                                        'CumWater_KBls'],
                                                    boton_nombre = 'Informacion_Reservas')
    

   
    
    
    
    
    
    
    
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
    
        # 1- HIPERVINCULOS DE POZOS.
    
    campos_be = [
        'URL_DiagramaPozo', 
        'URL_FichaCompletacion', 
        'URL_HistoriaPozo', 
        'URL_EvaluacionFormacion', 
        'URL_DiagnosticoAmbiental2024']
    
    
    campos_nnn = [
        'URL_DiagramaPozo', 
        'URL_FichaCompletacion', 
        'URL_HistoriaPozo', 
        'URL_EvaluacionFormacion', 
        'URL_DiagnosticoAmbiental2024']
    
    
        # 2- HIPERVINCULOS DE ESTACIONES.
        
    campos_be_estaciones = ['URL_DiagnosticoAmbiental2024']  
    campos_nnn_estaciones = ['URL_DiagnosticoAmbiental2024'] 
        
        
        
        # ---------------------------------------------------------------------------------
        
    
    columnas_hipervinculo = {'Pozos (Budare Elotes): Prueba Piloto': campos_be,                                        # Diccionario con el Nombre de Gdf y sus campos donde existe una Dirección URL para realizar los hipervinculos 
                             'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': campos_nnn,
                             'Estaciones Activas (Budare-Elotes)': campos_be_estaciones,
                             'Estaciones Activas (Nipa-Nardo-Nieblas)': campos_nnn_estaciones}                                    
    
    
    columnas_labels = {'Pozos (Budare Elotes): Prueba Piloto': 'UWISuperf',
                       'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': 'UWISuperf',
                       'Estaciones Activas (Budare-Elotes)': 'ID',
                       'Estaciones Activas (Nipa-Nardo-Nieblas)': 'ID'}
    
    
    '''
    
    DEFINICIÓN DE ESTILOS
    
    '''
    
           # ESTILOS PARA GEOMETRÍAS TIPO POLÍGONO
    
    
    
    be_bloque_simbologia =  simbologia.estilo_poligono(color = '#370540',
                               fill_opacity = 0.0,
                               weight = 2.0)
    
    nnn_bloque_simbologia =  simbologia.estilo_poligono(color = '#370540',
                               fill_opacity = 0.0,
                               weight = 2.0)
    
    be_campos_simbologia =  simbologia.estilo_poligono(color = '#cc18c0',
                               fill_opacity = 0.0)
    
    nnn_campos_simbologia =  simbologia.estilo_poligono(color = '#cc18c0',
                               fill_opacity = 0.0)
    
    
    
    capas_estilos = {'Bloque Budare-Elotes': be_bloque_simbologia,
                     'Bloque Nipa-Nardo-Nieblas': nnn_bloque_simbologia,
                     'Campos (Budare-Elotes):': be_campos_simbologia,
                     'Campos (Nipa-Nardo-Nieblas)': nnn_campos_simbologia}
    
    
    
                    # ESTILOS PARA GEOMETRÍAS TIPO PUNTO
    
    
    capas_iconos_config = {
        'Pozos (Budare Elotes): Prueba Piloto':{
            'campo': 'CategIni',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                               },
        'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto':{
            'campo': 'CategIni',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                                     },
        'Pozos (Budare Elotes): Priorizados. Versión No. 1 (18/02/2026)':{
            'campo': 'CategIni',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                               },
        'Pozos (Nipa-Nardo-Nieblas): Priorizados. Versión No. 1 (18/02/2026)':{
            'campo': 'CategIni',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                                     }
                           }
    
    
    
    '''
    GENERACIÓN DEL MAPA
    '''
    
    
    
    visor_geografico.generacion_mapa(capas_dicc = capas_dicc,                           # Se envían las capas que se incluirán en el Objeto Mapa
                                     columnas_enlaces = columnas_hipervinculo,
                                     columnas_labels = columnas_labels,
                                     capa_estilos = capas_estilos,
                                     capa_iconos = capas_iconos_config)         
    
    
    
    print ('    ✅ Modelo Ejecutado')
    
    
if __name__ == '__main__':              # Modismo de Python que se utiliza para garantizar que la función principal del programa (inicio_modelo_visor_geografico ()) solo se ejecute cuando el script se esté corriendo directamente, y no cuando el script sea importado como un módulo en otro programa. 

    
    inicio_modelo_visor_geografico ()