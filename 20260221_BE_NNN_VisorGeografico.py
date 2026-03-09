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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
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

    #@st.cache_visi
    
        
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
            <p style="font-weight: bold; margin-bottom: 5px; color: #0078D4;">Datos de Produccion:</p>
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




    def estructurar_columnas (self, gdf_df, dicc_columnas):
        
        
        """
        
        Objetivo: Filtrar, Renombrar y Ordenar las columnas de un GeodataFrame o un Dataframe.
        
        Parámetros: 
            
            gdf_df: Geodataframe / Dataframe a modificar
            dicc_columnas: Diccionario ['Nombre_Original': 'Nombre_Ajustado y Orden']
        
                
        """
        
        
        
        if gdf_df is None or dicc_columnas is None:                            # Si no Hay datos para Procesar, se devuelve las Capas originales
            
            return gdf_df
        
        
        
         # 1. VALIDACIÓN: Verifica que las columnas del Diccionario, realmente existan.
        
        
        columnas_existentes = {nombre_original: nombre_ajustado for nombre_original, nombre_ajustado in dicc_columnas.items ()
                                
                               if nombre_original in gdf_df.columns}
        
        
        columnas_faltantes = set (dicc_columnas.keys ()) - set (columnas_existentes.keys ())                # set convierte a conjuntos matemáticos, de tal forma que se pueda aplicar la teoría de conjuntos
        
        if columnas_faltantes:
            
            print (f'⚠️ Advertencia: Las siguientes columnas no existen en la capa y se omitirán: {columnas_faltantes}')
        
        
                 
        """
        COMPRESIÓN DE DICCIONARIOS para validar que los Nombres originales del Diccionario, realmente estén en las columnas del Gdf / Df.
        
         {nombre_original: nombre_ajustado}  Devuelve el Diccionario
         
         for nombre_original,nombre_ajustado in dicc_columnas.items (): La Lista nombre_original,nombre_ajustado recorre la Lista creada a partir del Diccionario entregado, según 
          dicc_columnas.items () [El método .items (), devuelve una lista con la clave: Valor]
          
         if nombre_original in gdf_df.columns: Validador. Si el Nombre Original existe en el nombre de las columnas del gdf/df,
         se incopora en el Diccionario Final
                                
        
        """
        
        
        # 2. VALIDACIÓN COMPONENTE GEOESPACIAL: Asegura que en el caso de Geodataframe, la columna Geometría No se pierda
        
        
        es_geoespacial = isinstance(gdf_df, gpd.GeoDataFrame)                  # Valida si la capa de entrada es una Instancia de la Clase Geodataframe de Geopandas
        
        
        if es_geoespacial:                                                     # Si es un GDF, el Nombre de la Columna Geometría se almacena en col_geometria
            
            col_geometria = gdf_df.geometry.name 
            
        else:                                                                  # Si es un DataFrame, No tiene Geometría. Por lo tanto la columna col_geometria = None
            
            col_geometria = None
            
            
        
        # 3. FILTRADO: Únicamente se dejan las columnas solicitadas
        
        
        cols_a_mantener = list(columnas_existentes.keys())                     # Del Diccionario, se dejan los Nombres de Columnas Iniciales que se van a Mantener, según el orden Solicitado.
                                                                               # Se convierte en Lista porque Geopandas/Pandas requieren una Lista para poder filtrar las Columnas y en caso tal,
                                                                               # adicionar la columna Geometría
            
        
        
        # 4. ADICIÓN COLUMNA GEOMETRÍA
        
        
        if es_geoespacial and col_geometria not in cols_a_mantener:             # Valida si la Capa es un GDF y a su vez, no está en la Lista cols_a_mantener, se adiciona la Geometría.
            
            cols_a_mantener.append(col_geometria)
            
        
        
        # 5. CREACIÓN DE LA CAPA: Únicamente tendrá las columnas definidas
        
        
        df_estructurado = gdf_df [cols_a_mantener].copy ()                     # Sobre la Capa original con la lista de columnas definidas [cols_a_mantener], se realiza una copia
                                                                               # y se almacena en df_estructurado
        
        
        
        
        # 6. RENOMBRE DE COLUMNAS
        
        
        df_estructurado = df_estructurado.rename (columns = columnas_existentes)   # Las columnas se renombran con base en el Diccionario {columnas_existentes}
        
        
        
        
        # 7. ORDENAMIENTO: El Nuevo orden se define por los Valores del Diccionario
        
        
        orden_final = list (columnas_existentes.values ())
        
        
        if es_geoespacial and col_geometria not in orden_final:
            
            orden_final.append (col_geometria)
            
            
        df_estructurado = df_estructurado [orden_final]
        
        
        return df_estructurado



    def ajustar_decimales (self, gdf_df, decimales = 2, columnas_especificas = None):
        
        
        """
        
            Objetivo: Ajusta la cantidad de decimales de las columnas numéricas (float) 
                  para mejorar la visualización en los popups y tablas.
                  
            Parámetros: 
                    
                    gdf_df: GeoDataFrame o DataFrame a modificar
                    decimales: Cantidad de decimales a conservar (Por defecto 2).
                    columnas_especificas: (Opcional) Lista de nombres de columnas a redondear.
                                  Si es None, se aplica a todas las columnas tipo float.
        
        """


        if gdf_df is None:
            
            return gdf_df
        
        
        # 1. COPIA DE LA CAPA: Para mantener la integridad de los Datos
        
        df_modificado = gdf_df.copy ()
        
        
        
        # 2. SELECCIÓN DE COLUMNAS: 
            
            
        if columnas_especificas:        # Solo se Redondean las columnas, según columnas_especificas
        
            cols_redondear = [col for col in columnas_especificas if col in df_modificado.columns]         # Compresión de Lista
            
        
        else:
            
            cols_redondear = df_modificado.select_dtypes (include = ['float64', 'float32']).columns.tolist ()      # Búsqueda automática: Encuentra todas las columnas que sean tipo Float (Decimales)
            
            
            
        # 3. APLICACIÓN DEL REDONDEO FÍSICO
        
        
        if cols_redondear:
            
            
            df_modificado [cols_redondear] = df_modificado [cols_redondear].round (decimales)
        
        
        
        return df_modificado
            
            


    def vincular_grafico_plotly_1_a_muchos (self, gdf_1, df_muchos, gdf_1_key, 
                                            df_muchos_key, col_x, col_agrupacion, 
                                            config_trazas, eje_x_es_fecha=True, 
                                            titulo_base = 'Producción Histórica del Pozo', nombre_col_html = 'Grafico_Interactivo',
                                            titulo_eje_x = None,
                                            titulo_eje_y_izquierda = 'Tasa de Petróleo (Bls) / Tasa de Agua (Bls)',
                                            titulo_eje_y_derecha = 'Tasa de Gas (Mscf)'):
        
        
        '''
            Objetivo: Generar Gráficos Interactivos con Plotly (Incluye Múltiples Ejes, Selectores Temporales y Botones de Agrupación)
            Los codigica en un Botón HTML dentro del GeodataFrame.
            
            Parámetros:
                    gdf_1: GeodataFrame que contiene los Elementos Geoespaciales
                    df_muchos: Tabla con la Información a graficar
                    gdf_1_key: Llave Primaria de gdf_1
                    df_muchos_key: Llave de df_muchos y Foránea coincidente con gdf_1_key
                    col_x: Columna con Datos Eje X (En algunos casos, la Fecha)
                    col_agrupacion: Es la columna que tiene las Categorías para activar el Menú Desplegable (Ej. Producción Histórica: Arenas Completadas)
                    config_trazas : {} Diccionario que define las Variables a Graficar y los parámetros Personalizados.
                    Ej: {'Crudo_Bbls': {'nombre': 'Crudo',
                                        'color': 'green',
                                        'eje_secundario': False}, ...}
                    eje_x_es_fecha: Define si el Eje X son Fechas o NO.
                    titulo_base: Es el título a incluir en el Gráfico. Por defecto se deja 'Análisis de Pozo'
                    nombre_col_html: Nombre del Boton que se adicionará al Geodataframe. Por defecto se dejó 'Grafico_Interactivo'
                    titulo_eje_x: Título del Eje X

        '''


    # 0. VALIDACIÓN DE LOS DATOS DE ENTRADA:



        if gdf_1 is None or df_muchos is None:                      # Valida el gdf/df de entrada. Si alguno está vacío, devuelve la misma capa
            
            return gdf_1
        
        
        df_modificado = gdf_1.copy ()
        botones_html = []
        
        
    # 1A. LIMPIEZA DE DATOS (EJE X):
        
        
        if eje_x_es_fecha:                                          # Si la Variable X es tipo Fecha, se asegura que el campo Fecha realmente se comporte como date. 
                                                                    # errors='coerce', transforma una posible celda de Fecha inválida.
                                                                    # (Ej: ‘Pendiente’, ‘N/A’, ‘’) en un Valor Nulo de Tiempo (Nat: Not a Time), permitiendo que el Bucle siga adelante)
            
            df_muchos [col_x] = pd.to_datetime(df_muchos[col_x],
                                               errors='coerce')
            
        
        else:                                                       # Si la Variable X no es tipo Fecha (Ej: Profundidad, Distancia, etc), se asegura que todos los Datos sean Numéricos.
                                                                    # Esto limpia los datos y convierte textos/vacios en valores Nan
            
            df_muchos [col_x] = pd.to_numeric(df_muchos[col_x],
                                               errors='coerce')
        


    # 1B. LIMPIEZA DE DATOS (EJE Y):
        
        
        for col_variable in config_trazas.keys ():                                  # Se extraen las columnas definidas en config_trazas y se obliga su conversión a números. Los textos/vacíos se vuelven NaN
            
            if col_variable in df_muchos.columns:
                
                df_muchos [col_variable] = pd.to_numeric(df_muchos [col_variable],
                                                         errors='coerce')


    # 1C. DEFINICIÓN DEL TÍTULO DEL EJE X: 
        
        if titulo_eje_x:
            
            texto_eje_x = titulo_eje_x
            
        else:
            
            if eje_x_es_fecha:
                
                texto_eje_x = 'Fecha'
            
            else:
                
                texto_eje_x = str (col_x)
        



        for index, row in df_modificado.iterrows():                                       # Recorre por cada índice y filas de df_modificado

            id_valor = row [gdf_1_key]                                                    # Iguala id_valor con el valor de gdf_1_key (UWI)

            df_filtrado = df_muchos [df_muchos [df_muchos_key] == id_valor].copy ()       # Selecciona los registros de la Tabla TB (Ej: Histórico de Producción) igualando df_muchos_key con id_valor


            if df_filtrado.empty:
                
                botones_html.append ('<p style="color:gray;">Sin datos históricos cargados en el Visor GIS</p>')   # Si la tabla_TB No tiene coincidencias, reporta texto ‘Sin datos históricos cargados en el Visor GIS’

                continue


            df_filtrado = df_filtrado.sort_values (by = col_x)                 # Organiza los datos en orden ascendente, según la columna col_x



            # 2. CONSTRUCCIÓN DE LA FIGURA (DOBLE EJE Y)
            
            fig = make_subplots (specs = [[{"secondary_y": True}]])            # Crea el Objeto fig (Lienzo de la Gráfica). [[{"secondary_y": True}]], 
                                                                               # garantiza que más adelante, cada trace (curva) se pueda asociar a un Eje Y específico


                # 2.A. Determinar los grupos de col_agrupacion (Ej: Arenas). Si no hay, se crea un Grupo Único
                
            
            if col_agrupacion:
                
                grupos = df_filtrado [col_agrupacion].unique ().tolist ()      # Se filtra la columna Específica (Ej: Todas las Arenas del Pozo)
                                                                               # unique() elimina los duplicados. Indica cuále son las categorías de col_agrupacion
                                                                               # .tolist() lo convierte en una lista nativa de Python (ej: ['Arena T', 'Arena R2']

                
            
            else:                                   
                
                grupos = ['General']                                           # Si col_agrupacion es None (Es decir, No se quiere dropdowns)
                                                                               # Se crea una Lista teórica con un solo elemento para que el código no falle



            numero_trazas_por_grupo = len (config_trazas)                      # Depende del Diccionario que se pase. En el contexto de la Producción (Oil/Gas/Water) son 3
            
            total_trazas = len (grupos) * numero_trazas_por_grupo              # (len (grupos) = Cantidad de Arenas) * (numero_trazas_por_grupo) = Total de Curvas que tendrá la Gráfica



            # 3. ADICIÓN DINÁMICA DE TRAZAS (fig.add_trace)


            for i, grupo in enumerate (grupos):                                # Recorre grupos. Enumerate() devuelve índice y grupo (Valor de grupos)


                if col_agrupacion:
                    
                    df_grupo = df_filtrado[df_filtrado [col_agrupacion] == grupo]         # Si existe una categoría de Agrupación, crea grupos de datos

                else:
                    
                    df_grupo = df_filtrado                                     # Si No existe col_agrupación, simplemente todos los valores de df_filtrado



                if i == 0:                                                     # Por default, solo el primer grupo (primera arena) será visible al abrir la gráfica
                                                                               # El parámetro de visibilidad de go.Scatter (), se asocia a la variable es_visible
                    es_visible = True
                    
                else:
                    
                    es_visible = False



                for col_variable, config in config_trazas.items ():            # Desempaqueta el dicc {config_trazas}. col_variable = ‘Key’; config = {}
                    
                    
                    fig.add_trace (go.Scatter (
                                                x = df_grupo [col_x],                           # Tabla limipiada filtrada por categoría. Muestra los valores de col_x (Ej: Fechas)
                                                y = df_grupo [col_variable],                    # Tabla limipiada filtrada por categoría. Realiza una Máscara, según col_variable que es traída, del diccionario config_trazas
                                                name = f"{config['nombre']} ({grupo})",         # El nombre es dinámico
                                                mode = 'lines+markers',                         # Dibuja una línea continua (lines) y pone un punto visible (markers) en cada valor de col_x (Fecha)
                                                line = {
                                                        'color': config['color'],
                                                        'width': 2
                                                        },
                                                marker = {'size': 4},
                                                visible = es_visible                            # Toma el valor de la variable definida previamente
                                                ),
                                    secondary_y = config['eje_secundario']                      # secondary_y=False: Eje Y izquierdo. secondary_y=True: Eje Y Derecho. 
                                    )



            # 4. CONSTRUCCIÓN DEL DROPDOWN (updatemenus)


            botones_dropdown = []
            
            
            if col_agrupacion and len (grupos) > 1:                            # La creación de   botones_dropdown, solo tiene sentido si fue definida 
                                                                               # la variable col_agrupacion y su longitud es mayor a 1 
                
                for i, grupo in enumerate (grupos):                            # Crea un Botón por cada Iteración: Inicia el recorrido por cada categoría (c/u de las Areas) de Grupos. 
                                                                               # i = índica; grupo = categoría de la Arena.
                    
            
                # 4.A. MATRIZ DE BOOLEANOS. Enciende solo las trazas que perteneces a este grupo
                
                    '''
                        inicio = i * numero_trazas_por_grupo
                        fin = inicio + numero_trazas_por_grupo
                        
                            En la Vuelta 0 (Arena T): * 
                                inicio = 0 * 3 = 0
                                fin = 0 + 3 = 3
                                Rango a encender: Posiciones 0, 1 y 2.
                            
                            En la Vuelta 1 (Arena R2):
                                inicio = 1 * 3 = 3
                                fin = 3 + 3 = 6
                                Rango a encender: Posiciones 3, 4 y 5.
                                
                        for j in range(inicio, fin):
                          visibilidad[j] = True
                          
                          Resultado para Arena T: [True, True, True, False, False, False]
•                         Resultado para Arena R2: [False, False, False, True, True, True]


                    '''
                
                
                    visibilidad = [False] * total_trazas
                    
                    inicio = i * numero_trazas_por_grupo
                    
                    fin = inicio + numero_trazas_por_grupo
                    
                    
                    for j in range (inicio, fin):
                        
                        visibilidad [j] = True
                    
            
                
                # 4.B. CREACIÓN DEL DICCIONARIO PARÁMETRO 'buttons', según lo requerido posteriormente para fig.update_layout()
            
            
                    botones_dropdown.append (
                                                 {
                                                   'label': str (grupo),
                                                   'method': 'update',
                                                   'args': [
                                                             # 1er Diccionario: Actualiza las curvas (Trace)
                                                             {'visible': visibilidad}, 
                                                             
                                                             # 2do Diccionario: Actualiza los textos (Layout) conservando el formato
                                                             {'title.text': f'<b>{titulo_base} {id_valor}</b><br><span style="font-size:20px;">Arena: {grupo}</span></b>'}
                                                            ]
                                                 }
                                            )
            


                # 4.C. CREACIÓN DEL DICCIONARIO PARÁMETRO 'updatemenus', según lo requerido posteriormente para fig.update_layout() 


            if botones_dropdown:
                
                
                menu_desplegable = [
                                    {
                                      'active': 0,
                                      'buttons': botones_dropdown,
                                      'type': 'dropdown',
                                      'x': 0.05,
                                      'y': 1.15
                                    }
                                   ]

            else:
                
                menu_desplegable = []




            # 5. ACTUALIZACIÓN DEL LAYOUT (Títulos, Leyendas, Ejes)



            titulo_inicial = f'<b>{titulo_base} {id_valor}</b><br><span style="font-size:20px;">Arena: {grupos[0]}</span></b>'        # grupos[0] inicia con el texto de la primera categoría (Arena). Se actualiza en botones_dropdown.append()


            fig.update_layout( title = {
                                        'text': titulo_inicial,
                                        'font': {
                                                 'family': 'Century Gothic',
                                                 'size': 20,
                                                 'color': '#050200'
                                                 },
                                        'x': 0.5,                              # Centrado horizontalmente
                                        'y': 0.98,                             # Ubicado al 98% de la altura del lienzo (casi al tope)
                                        'xanchor': 'center',                   # El punto de anclaje de la X es el centro del texto
                                        'yanchor': 'top',                      # El punto de anclaje de la Y es la parte superior del texto
                                        'pad': {'t': 10}                       # Un pequeño 'colchón' de 10 píxeles hacia arriba
                                        },
                                 xaxis_title = texto_eje_x,
                                 updatemenus = menu_desplegable,
                                 hovermode ='x unified',
                                 legend = {
                                          'orientation': 'h',
                                          'yanchor': 'bottom',
                                          'y': 1.02,
                                          'xanchor': 'right',
                                          'x': 1,
                                          'font': {'family': 'Century Gothic',
                                                   'size': 12,
                                                   'color': 'black'
                                                   },
                                          'bgcolor': 'White',
                                          'bordercolor': 'Gray',
                                          'borderwidth': 1
                                          },
                                 margin = {
                                           't': 120,
                                           'b': 100,
                                           'l': 80,
                                           'r': 80,
                                           'pad': 10
                                           },
                                 plot_bgcolor = 'white'
                                )



                # 5.A. PERSONALIZACIÓN DE LOS EJES Y (IZQUIERDA Y DERECHA)

                        # Personalización del Eje 'Y' Petróleo / Agua

            fig.update_yaxes(title_text = titulo_eje_y_izquierda,
                             secondary_y = False,
                             showgrid = True,
                             gridcolor = 'lightgray',
                             type = 'log')


                        # Personalización del Eje 'Y' Gas

            fig.update_yaxes(title_text =  titulo_eje_y_derecha,
                             secondary_y = True,
                             showgrid = False,
                             type = 'log')




            # 6. ACTUALIZACIÓN EJE X (Selectores y Slider)
            
            
            if eje_x_es_fecha:                                                 # Si son fechas, le ponemos todo: Slider + Botones de meses/años
            
                fig.update_xaxes(rangeslider = {
                                                 'visible': True,
                                                 'thickness' : 0.08,
                                                 'bgcolor':"#F0F2F5"
                                                },
                                 rangeselector = {
                                                   'buttons' : [
                                                                    {
                                                                      'count': 6,                     # Número de pasos necesarios para actualizar el rango
                                                                      'label': 'últimos 6 meses',     # Etiqueta que aparecerá en el Botón
                                                                      'step': 'month',                # Unidad de Medida que el valor de 'count' usará para configurar su rango
                                                                      'stepmode': 'backward'          # Indica que debe contar 1 mes hacia atrás desde la fecha más reciente en tus datos. 🔙}])}
                                                                    },
                                                                    {
                                                                      'count': 1,                     # Número de pasos necesarios para actualizar el rango
                                                                      'label': 'último Año',          # Etiqueta que aparecerá en el Botón
                                                                      'step': 'year',                 # Unidad de Medida que el valor de 'count' usará para configurar su rango
                                                                      'stepmode': 'backward'          # Indica que debe contar 1 mes hacia atrás desde la fecha más reciente en tus datos. 🔙}])}
                                                                    },
                                                                    {
                                                                      'label': 'Todo',               # Etiqueta que aparecerá en el Botón
                                                                      'step': 'all',                 # Unidad de Medida que el valor de 'count' usará para configurar su rango
                                                                    }
                                                                ]
                                                                    
                                                  }
                                 )
            
            else:                                                              # Si son números (Ej: Profundidad), solo ponemos el Slider para hacer zoom
            
                fig.update_xaxes(rangeslider = {
                                                 'visible': True,
                                                 'thickness' : 0.08,
                                                 'bgcolor':"#F0F2F5"
                                                }
                                 )
            
            
            
            
                           

            # 7. EXPORTAR A HTML
            
            '''
                  full_html=True. crea un archivo web completo e independiente. Incluye las etiquetas <html>, <head> y <body>. 
                  Esto garantiza que, si alguien abre ese código por separado en un navegador, la gráfica se verá perfecta y 
                  ocupará toda la pantalla.   
                  
                  include_plotlyjs='cdn'. Al usar 'cdn', el HTML solo lleva una línea de texto que 
                  le dice al navegador: "Descarga las herramientas de dibujo desde los servidores rápidos de Plotly/Google". 
                  Esto hace que el tamaño de tu cadena de texto pase de megabytes a solo unos cuantos kilobyte
            
            '''
            
            
            html_grafica = fig.to_html(full_html = True,
                                       include_plotlyjs ='cdn')
            
            
            
            '''
                   html_base64: Convierte el código HTML (que tiene caracteres especiales como <, >, /, ") 
                                en una cadena de texto plana que solo usa letras y números. •  
                                
                                html_grafica.encode('utf-8'): Convierte el texto HTML en "bytes" (el lenguaje de la máquina) 
                                usando el estándar internacional de caracteres.
•                              
                               base64.b64encode(...): Es el proceso de cifrado. Transforma esos bytes en una cadena Base64.
•  .                           
                               decode('utf-8'): Convierte el resultado final de nuevo a un "string" de Python para que lo podamos manipular.

            
            '''
            
            
            html_base64 = base64.b64encode(html_grafica.encode('utf-8')).decode('utf-8')






            # 8. CONSTRUCCIÓN DEL BOTÓN ASOCIADO A LA GRÁFICA
            
            
            '''
            
                href="data:text/html;base64,{html_base64}": El prefijo data:text/html;base64 le dice al navegador:
                "Lo que sigue no es una ruta de archivo, es el código de una página web entera empaquetado en base64".
                
                 Al usar la API Blob (fetch) de JavaScript evitamos el bloqueo de seguridad 
                 de los navegadores modernos que impide abrir URLs 'data:text/html' 
                 directamente en nuevas pestañas.

    
            '''
            
            btn = f"""
            <a href="#" onclick="var w = window.open('about:blank', '_blank'); w.document.write('<body style=&quot;margin:0;&quot;><iframe src=&quot;data:text/html;base64,{html_base64}&quot; style=&quot;border:none;width:100vw;height:100vh;&quot;></iframe></body>'); w.document.close(); return false;" 
               style="display:inline-block; padding:8px 15px; background-color:#de610d; 
                      color:white; text-decoration:none; border-radius:5px; 
                      font-family:Arial; font-weight:bold; text-align:center;">
               📈 Abrir Gráfica Interactiva
            </a>
            """


            botones_html.append (btn)                                          # Incluye el Botón 'btn' a la Lista botones_html



        df_modificado  [nombre_col_html] =  botones_html                   # Crea una Columna con el nombre 'nombre_col_html' y le incopora el Botón html ' botones_html'
            
            
        return df_modificado







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
    
    url_drive_be = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQCv1n_6fBkkQ4sggi1bxqtJAUdO-7OmzNI3K2pYXN-SDJI?e=J8OvAH'
    ur_drive_nnn = 'https://grouplngenergy-my.sharepoint.com/:u:/g/personal/dcifuentes_lngenergygroup_com/IQBflwXC98C3QrTHHq25EUdaAS0TWT5xpNZAbbx909HCvGc?e=FFyQvr'
 
    
    
    
 
 
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
    be_nnn_lineasflujo_ini = datos_be.cargar_capa_zip ('LineasProceso_V0')
    
    
    
    nnn_bloque = datos_nnn.cargar_capa_zip ('Bloque_NipaNardo_V1_20240518_AjusteLEC')
    nnn_campos = datos_nnn.cargar_capa_zip ('Campos_NipaNardo_V1_20240518_AjusteLEC')
    nnn_estaciones = datos_nnn.cargar_capa_zip ('PlantasEstaciones_NipaNardo_V3_20240724_AjusteLECCampo_PT')
    nnn_pozos = datos_nnn.cargar_capa_zip ('Pozos_NNN_PT_Estruct')
    
    
    
    '''
    
    2B- Creación de Dataframes
    '''
    
    be_reservas_TB = datos_be.cargar_capa_zip ('PruebaPiloto_Reservas_TB_20260219')
    
    
    #   1. DATAFRAMES DE PRODUCCIÓN
    
    Produccion_Gral_Historica_TB = datos_be.cargar_capa_zip ('Produccion_Gral_Historica')
    Produccion_Gral_Proyectada_VolTecnicos_TB = datos_be.cargar_capa_zip ('Produccion_Gral_Proyectada_VolTecnicos')
    
    Produccion_Detallada_Historica_TB = datos_be.cargar_capa_zip ('Produccion_Detallada_Historica')
    Produccion_Detallada_Proyectada_VolTecnicos_TB = datos_be.cargar_capa_zip ('Produccion_Detallada_Proyectada_VolTecnicos')
    
    
    
    
    
    
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
        D. REDONDEO DE DATOS FLOAT
    
    '''
    
    be_pozos_prueba_piloto = analisis_geoespacial.ajustar_decimales(gdf_df = be_pozos_prueba_piloto)      
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.ajustar_decimales(gdf_df = nnn_pozos_prueba_piloto) 
    
    Produccion_Gral_Historica_TB = analisis_geoespacial.ajustar_decimales(gdf_df = Produccion_Gral_Historica_TB) 
    
    Produccion_Gral_Proyectada_VolTecnicos_TB = analisis_geoespacial.ajustar_decimales(gdf_df = Produccion_Gral_Proyectada_VolTecnicos_TB) 
    
    Produccion_Detallada_Historica_TB = analisis_geoespacial.ajustar_decimales(gdf_df = Produccion_Detallada_Historica_TB)
    
    Produccion_Detallada_Proyectada_VolTecnicos_TB = analisis_geoespacial.ajustar_decimales(gdf_df = Produccion_Detallada_Proyectada_VolTecnicos_TB)
    
    
    
    
    '''
    
       E-  PRESENTACIÓN DE RESERVAS (JOIN)
    '''
    
   
    be_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = be_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Gral_Historica_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Initial_Production_Date',
                                                                        'Final_Production_Date',
                                                                        'Cum_Oil_kBls',
                                                                        'Cum_Gas_MMscf',
                                                                        'Cum_Water_KBls',
                                                                        'Cum_Oil_kBls_Before1994',
                                                                        'Cum_Gas_MMscf_Before1994',
                                                                        'Cum_Water_KBls_Before1994',
                                                                        'Source_Volumes_Before1994'],
                                                    boton_nombre = 'Historia_Produccion_Total')
    
    
    be_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = be_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Gral_Proyectada_VolTecnicos_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Area_acres_Teorico',
                                                                        'Espesor_Total_Teorico',
                                                                        'Espesor_Neto_ft_Teorico',
                                                                        'POR_frac_Teorico',
                                                                        'SW_frac_Teorico',
                                                                        'Presion_Inicial',
                                                                        'Presion_Actual',
                                                                        'Boi',
                                                                        'OOIP_KBls',
                                                                        'EUR_Actual_Kbls',
                                                                        'EUR_Oil_Rem_KBls',
                                                                        'RF_Porc',
                                                                        'Volumen_Reservas_Tecnicas_KBls'],
                                                    boton_nombre = 'Estimado_Tecnico_Volumen_Produccion')
    
    
    be_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = be_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Detallada_Historica_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Date',
                                                                        'OilRate_bls',
                                                                        'GasRate_Mscf',
                                                                        'WaterRate_Bls'],
                                                    boton_nombre = 'Historia_Produccion_Detallada')
    
    
    be_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = be_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Detallada_Proyectada_VolTecnicos_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Date',
                                                                        'Go_stb_d',
                                                                        'OilVol_stb',
                                                                        'Np_Mstb',
                                                                        'GOR_scf_bbl',
                                                                        'qg_Mscfd',
                                                                        'Gas_Vol_MMscf',
                                                                        'Gp_MMscf'],
                                                    boton_nombre = 'Estimado_Tecnico_Detallado')
    
    
    
    
    
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = nnn_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Gral_Historica_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Initial_Production_Date',
                                                                        'Final_Production_Date',
                                                                        'Cum_Oil_kBls',
                                                                        'Cum_Gas_MMscf',
                                                                        'Cum_Water_KBls',
                                                                        'Cum_Oil_kBls_Before1994',
                                                                        'Cum_Gas_MMscf_Before1994',
                                                                        'Cum_Water_KBls_Before1994',
                                                                        'Source_Volumes_Before1994'],
                                                    boton_nombre = 'Historia_Produccion_Total')
    
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = nnn_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Gral_Proyectada_VolTecnicos_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Area_acres_Teorico',
                                                                        'Espesor_Total_Teorico',
                                                                        'Espesor_Neto_ft_Teorico',
                                                                        'POR_frac_Teorico',
                                                                        'SW_frac_Teorico',
                                                                        'Presion_Inicial',
                                                                        'Presion_Actual',
                                                                        'Boi',
                                                                        'OOIP_KBls',
                                                                        'EUR_Actual_Kbls',
                                                                        'EUR_Oil_Rem_KBls',
                                                                        'RF_Porc',
                                                                        'Volumen_Reservas_Tecnicas_KBls'],
                                                    boton_nombre = 'Estimado_Tecnico_Volumen_Produccion')
    
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = nnn_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Detallada_Historica_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Date',
                                                                        'OilRate_bls',
                                                                        'GasRate_Mscf',
                                                                        'WaterRate_Bls'],
                                                    boton_nombre = 'Historia_Produccion_Detallada')
    
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.vincular_tabla_1_a_muchos (gdf_padre = nnn_pozos_prueba_piloto,
                                                    df_hijo = Produccion_Detallada_Proyectada_VolTecnicos_TB,
                                                    gdf_padre_Key = 'UWISuperf',
                                                    df_hijo_key = 'UWI_Superficie',
                                                    columnas_interes = ['ID_UWI',
                                                                        'UWI_Superficie',
                                                                        'Completed_Sands',
                                                                        'Date',
                                                                        'Go_stb_d',
                                                                        'OilVol_stb',
                                                                        'Np_Mstb',
                                                                        'GOR_scf_bbl',
                                                                        'qg_Mscfd',
                                                                        'Gas_Vol_MMscf',
                                                                        'Gp_MMscf'],
                                                    boton_nombre = 'Estimado_Tecnico_Detallado')
    
    
    
    
    
    
    
    
    
    
    print ('BLOQUE BE: ', be_bloque.columns)
    
    print ('BLOQUE NNN: ',nnn_bloque.columns)
    
    print ('Pozos BE:', be_pozos.columns)
    
    
    print ('Pozos (Budare Elotes): Prueba Piloto:', len (be_pozos_prueba_piloto))
    
    print ('Pozos (Nipa-Nardo-Nieblas): Prueba Piloto:', len (nnn_pozos_prueba_piloto))
    
    
    
    
    
    
    '''
        F- HIPERVÍNCULOS
    
    '''
    
        # 1- HIPERVINCULOS DE POZOS.
    
    campos_be = [
        'Diagrama_Pozo', 
        'Ficha_Completacion', 
        'Historia_Pozo', 
        'Evaluacion_Formacion', 
        'Diagnostico_Ambiental_2024']
    
    
    campos_nnn = [
        'Diagrama_Pozo', 
        'Ficha_Completacion', 
        'Historia_Pozo', 
        'Evaluacion_Formacion', 
        'Diagnostico_Ambiental_2024']
    
    
        # 2- HIPERVINCULOS DE ESTACIONES.
        
    campos_be_estaciones = ['URL_DiagnosticoAmbiental2024']  
    campos_nnn_estaciones = ['URL_DiagnosticoAmbiental2024'] 
        
        
        
        # ---------------------------------------------------------------------------------
        
    
    columnas_hipervinculo = {'Pozos (Budare Elotes): Prueba Piloto': campos_be,                                        # Diccionario con el Nombre de Gdf y sus campos donde existe una Dirección URL para realizar los hipervinculos 
                             'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': campos_nnn,
                             'Estaciones Activas (Budare-Elotes)': campos_be_estaciones,
                             'Estaciones Activas (Nipa-Nardo-Nieblas)': campos_nnn_estaciones}                                    
    
    
    columnas_labels = {'Pozos (Budare Elotes): Prueba Piloto': 'UWI_Superficie',
                       'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': 'UWI_Superficie',
                       'Estaciones Activas (Budare-Elotes)': 'ID',
                       'Estaciones Activas (Nipa-Nardo-Nieblas)': 'ID'}
    
    
    '''
    
        G- DEFINICIÓN DE ESTILOS
    
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
            'campo': 'Categoria_Pozo',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                               },
        'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto':{
            'campo': 'Categoria_Pozo',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                                     },
        'Pozos (Budare Elotes): Priorizados. Versión No. 1 (18/02/2026)':{
            'campo': 'Categoria_Pozo',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                               },
        'Pozos (Nipa-Nardo-Nieblas): Priorizados. Versión No. 1 (18/02/2026)':{
            'campo': 'Categoria_Pozo',
             'mapeo': {
                 1: {'icon': 'play', 'color': 'green', 'prefix': 'fa', 'label': 'Pozo Categoria 1'},
                 2: {'icon': 'clock-o', 'color': 'orange', 'prefix': 'fa', 'label': 'Pozo Categoria 2'},
                 3: {'icon': 'ban', 'color': 'red', 'prefix': 'fa', 'label': 'Pozo Categoria 3'}
                      }
                                                     }
                           }
    
   
    '''
        H. GENERACIÓN DE GRÁFICAS (Plotlib)
    
    '''
    
    config_curvas_produccion = {'OilRate_bls': {'nombre': 'Crudo (Bls)',
                                                'color': '#15e653',
                                                'eje_secundario': False},
                                'GasRate_Mscf': {'nombre': 'Gas (Mscf)',
                                                 'color': '#ed1111',
                                                 'eje_secundario': True},
                                'WaterRate_Bls': {'nombre': 'Agua (Bls)',
                                                 'color': '#112eed',
                                                 'eje_secundario': False}
                                }
    
    
    
    
    be_pozos_prueba_piloto = analisis_geoespacial.vincular_grafico_plotly_1_a_muchos(gdf_1 = be_pozos_prueba_piloto, 
                                                                                     df_muchos = Produccion_Detallada_Historica_TB,
                                                                                     gdf_1_key = 'ID_UWI',
                                                                                     df_muchos_key = 'ID_UWI', 
                                                                                     col_x = 'Date', 
                                                                                     col_agrupacion = 'Completed_Sands', 
                                                                                     config_trazas = config_curvas_produccion,
                                                                                     eje_x_es_fecha = True,
                                                                                     nombre_col_html = 'Grafico_Interactivo')
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.vincular_grafico_plotly_1_a_muchos(gdf_1 = nnn_pozos_prueba_piloto, 
                                                                                     df_muchos = Produccion_Detallada_Historica_TB,
                                                                                     gdf_1_key = 'ID_UWI',
                                                                                     df_muchos_key = 'ID_UWI', 
                                                                                     col_x = 'Date', 
                                                                                     col_agrupacion = 'Completed_Sands', 
                                                                                     config_trazas = config_curvas_produccion,
                                                                                     eje_x_es_fecha = True,
                                                                                     nombre_col_html = 'Grafico_Interactivo')
    
    
    
    
    
    
     
    '''
        I. FILTRADO, RENOMBRE Y ORDENACIÓN DE COLUMNAS
    
    '''
    
    # 1. DICCIONARIO PARA POZOS BUDARE - ELOTES
    
    dicc_campos_pozos = {'ID_UWI': 'ID_UWI',
                         'UWISuperf': 'UWI_Superficie',
                         'ID_GIS': 'ID_GIS',
                         'ID_WellName': 'ID_Well_Name',
                         'Bloque': 'Bloque',
                         'Campo': 'Campo',
                         'Este_Regven': 'Este_SIRGAS_RegVen',
                         'Norte_Regven': 'Norte_SIRGAS_RegVen',
                         'Este_Canoa': 'Este_LaCanoa',
                         'Norte_Canoa': 'Norte_LaCanoa',
                         'Longitud': 'Longitud_Geografica',
                         'Latitud': 'Latitud_Geografica',
                         'CategIni': 'Categoria_Pozo',
                         'DescripPozo_PDVSA': 'Descripcion_Pozo_PDVSA',
                         'CategIniFuente': 'Fuente_Categoria',
                         'EstadoPozo_PDVSA': 'Estado_Pozo_PDVSA',
                         'SubEstadoPozo_PDVSA': 'SubEstado_Pozo_PDVSA',
                         'FluidoSigla_PDVSA': 'Fluido_PDVSA',
                         'FluidoTipoSigla_PDVSA': 'Tipo_Fluido_PDVSA',
                         'TipoCrudo_PDVSA': 'Tipo_Crudo_PDVSA',
                         'EstacFlujo': 'Estacion_Flujo',
                         'EstacDescarga': 'Estacion_Descarga',
                         'LevantaPozo_PDVSA': 'Levantamiento_Pozo_PDVSA',
                         'SubLevPozo_PDVSA': 'SubLevabtamiento_Pozo_PDVSA',
                         'URL_DiagramaPozo': 'Diagrama_Pozo',
                         'URL_FichaCompletacion': 'Ficha_Completacion',
                         'URL_HistoriaPozo': 'Historia_Pozo',
                         'URL_EvaluacionFormacion': 'Evaluacion_Formacion',
                         'InicioPerforacion': 'Inicio_Perforacion',
                         'FinPerforacion': 'Fin_Perforacion',
                         'Historia_Produccion_Total': 'Historia_Produccion_Total',
                         'Estimado_Tecnico_Volumen_Produccion':'Estimado_Tecnico_Volumen_Produccion',
                         'Grafico_Interactivo': 'Grafico_Interactivo',
                         'Historia_Produccion_Detallada': 'Historia_Produccion_Detallada',
                         'Estimado_Tecnico_Detallado': 'Estimado_Tecnico_Detallado',
                         'VisitaCampo': 'Visita_Campo_LNG',
                         'FechaVisita': 'Fecha_Visita_Campo',
                         'URL_DiagnosticoAmbiental2024': 'Diagnostico_Ambiental_2024',
                         'Prioridad': 'Prioridad',
                         'PrioridadVersion': 'Prioridad_Version',
                         'PrioridadClase': 'Prioridad_Clase',
                         'PruebaPiloto': 'Prueba_Piloto'}
    
    
    
    be_pozos = analisis_geoespacial.estructurar_columnas(gdf_df = be_pozos, 
                                                         dicc_columnas = dicc_campos_pozos)
    
    nnn_pozos = analisis_geoespacial.estructurar_columnas(gdf_df = nnn_pozos, 
                                                         dicc_columnas = dicc_campos_pozos)
    
    be_pozos_Priorizados_v1 = analisis_geoespacial.estructurar_columnas(gdf_df = be_pozos_Priorizados_v1, 
                                                         dicc_columnas = dicc_campos_pozos)
    
    nnn_pozos_Priorizados_v1 = analisis_geoespacial.estructurar_columnas(gdf_df = nnn_pozos_Priorizados_v1, 
                                                         dicc_columnas = dicc_campos_pozos)
    
    be_pozos_prueba_piloto = analisis_geoespacial.estructurar_columnas(gdf_df = be_pozos_prueba_piloto, 
                                                         dicc_columnas = dicc_campos_pozos)
    
    nnn_pozos_prueba_piloto = analisis_geoespacial.estructurar_columnas(gdf_df = nnn_pozos_prueba_piloto, 
                                                         dicc_columnas = dicc_campos_pozos)
    
    
        
    
    '''
        J. GENERACIÓN DEL MAPA
    '''
    
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
                  'Pozos (Nipa-Nardo-Nieblas): Prueba Piloto': nnn_pozos_prueba_piloto,
                  'Lineas de Flujo Conceptuales':be_nnn_lineasflujo_ini 
                  }
    
    
    
    visor_geografico.generacion_mapa(capas_dicc = capas_dicc,                           # Se envían las capas que se incluirán en el Objeto Mapa
                                     columnas_enlaces = columnas_hipervinculo,
                                     columnas_labels = columnas_labels,
                                     capa_estilos = capas_estilos,
                                     capa_iconos = capas_iconos_config)         
    
    
    
    print ('    ✅ Modelo Ejecutado')
    
    
if __name__ == '__main__':              # Modismo de Python que se utiliza para garantizar que la función principal del programa (inicio_modelo_visor_geografico ()) solo se ejecute cuando el script se esté corriendo directamente, y no cuando el script sea importado como un módulo en otro programa. 

    
    inicio_modelo_visor_geografico ()