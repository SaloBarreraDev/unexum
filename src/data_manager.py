from kivy.utils import platform
from kivy.logger import Logger
from kivy.config import Config
import json
from os.path import exists, join
from os import remove, makedirs
from models import Materia, Evaluacion
Config.set('kivy', 'log_level', 'info')

RUTA_ARCHIVOS = None
if platform=="android":
    from android import mActivity # type: ignore
    context = mActivity.getApplicationContext()
    result =  context.getExternalFilesDir(None)
    if result:
        RUTA_ARCHIVOS =  str(result.toString())
elif platform=="win":
    RUTA_ARCHIVOS= "."
RUTA_DATOS = join(RUTA_ARCHIVOS, "datos_usuario")
makedirs(RUTA_DATOS, exist_ok = True)

def cargar_datos(self):
    Materia.materias = []
    Materia.electivas = []
    Materia.agregar_electivas = False
    archivo_materias = None  
    archivo_electivas = None

    especialidad_to_archivo = {"Ing. Industrial": "industrial",
        "Ing. Eléctrica": "electrica",
        "Ing. Mecánica": "mecanica",
        "Ing. Química": "quimica",
        "Ing. Metalúrgica": "metalurgica",
        "Comunicaciones":"electronica_comunicaciones",
        "Computación": "electronica_computacion",
        "Control": "electronica_control"}
    nombre_archivo = ""
    if self.texto_mencion in especialidad_to_archivo:
        nombre_archivo = especialidad_to_archivo[self.texto_mencion]
    else:
        nombre_archivo = especialidad_to_archivo[self.texto_especialidad]

    path_archivo_materias_txt = join(RUTA_ARCHIVOS, f"materias_{nombre_archivo}.txt")
    path_archivo_materias_json = join(RUTA_DATOS, f"materias_{nombre_archivo}.json")
    path_archivo_electivas_json = join(RUTA_DATOS, f"electivas_{nombre_archivo}.json")


    if exists(path_archivo_materias_json):
        Logger.info("Cargando archivo de materias desde archivo json")
        lista_materias = []
        with open(path_archivo_materias_json,"r", encoding = "utf-8") as archivo_materias:
            lista_materias = json.load(archivo_materias)
        for materia in lista_materias:
            Materia(materia["semestre"],
                    materia["codigo"],
                    materia["nombre"],
                    materia["ht"],
                    materia["ha"],
                    materia["hl"],
                    materia["uc"],
                    materia["nota"],
                    materia["aprobada"],
                    materia["disponible"],
                    materia["pre1"],
                    materia["pre2"],
                    materia["coreq"],
                    materia["inscrita"],
                    [Evaluacion(e["identificador"], e["nota"], e["ponderacion"], e["extra"]) for e in materia["evaluaciones"]],
                    materia["porcentual"],
                    materia["pre3"])
        Logger.info("Finalizó el cargado de materias desde archivo json")
        return Materia.materias[:]

    #Si no hay archivo materias json se cargan los datos por defecto
        
    lista_materias = cargar_datos_defecto(self.texto_especialidad, self.texto_mencion)
    lista_diccionarios_electivas = []
    for materia in Materia.electivas:
        lista_diccionarios_electivas.append(materia.to_dict())
    with open(path_archivo_electivas_json, "w", encoding = "utf-8") as archivo_electivas:
        json.dump(lista_diccionarios_electivas, archivo_electivas, indent = 4)
            
    return lista_materias
            
def cargar_datos_defecto(especialidad, mencion = "No Aplica"):
    Materia.materias = []
    Materia.electivas = []
    Materia.agregar_electivas = False
    Logger.info("Cargando materias por defecto")
    
    if especialidad=="Ing. Industrial":
        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"EB1125","''","EB2124")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","II2311","Iniciación Profesional",1,0,0,1,"''",False,False,"30","U.C.","''")
        Materia("III","IM1022","Dibujo De Máquina",1,3,0,2,"''",False,False,"EB3122","''","''")
        #Semestre IV
        Materia("IV","EB1154","Matemáticas Especiales",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","IM1043","Mecánica Aplicada",3,1,0,3,"''",False,False,"EB1213","EB3122","''")
        Materia("IV","IQ4063","Termodinámica",3,1,0,3,"''",False,False,"EB1134","IQ5113","''")
        Materia("IV","IQ4093","Ingeniería Química",2,2,0,3,"''",False,False,"EB1134","IQ5113","''")
        Materia("IV","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        #Semestre V
        Materia("V","IQ4073","Fenómenos De Transporte",3,1,0,3,"''",False,False,"IQ4063","IQ4093","''")
        Materia("V","II2322","Plantas Industriales Y Man. De Materiales",1,3,0,2,"''",False,False,"II2311","''","''")
        Materia("V","IE5014","Fundamentos De Ing. Eléctrica",3,0,2,4,"''",False,False,"EB2211","EB1134","''")
        Materia("V","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("V","IM1054","Resistencia Y Ensayo De Materiales",3,1,2,4,"''",False,False,"IM1043","''","''")
        Materia("V","II3114","Estadística Industrial",3,3,0,4,"''",False,False,"EB1154","EB1312","''")
        #Semestre VI
        Materia("VI","IM1063","Elementos De Máquina",3,1,0,3,"''",False,False,"IM1022","IM1054","''")
        Materia("VI","IM2014","Tecnología De Fabricación I",3,0,3,4,"''",False,False,"IM1054","''","''")
        Materia("VI","IQ4003","Transferencia De Calor",3,1,0,3,"''",False,False,"IQ4073","''","''")
        Materia("VI","II2113","Ingeniería Del Trabajo",3,1,0,3,"''",False,False,"II2322","II3114","''")
        Materia("VI","II2121","Lab. De Ingeniería Del Trabajo",0,0,3,1,"''",False,False,"''","''","II2113")
        Materia("VI","MT1015","Tecnología De Materiales",4,0,2,5,"''",False,False,"IM1054","''","''")
        #Semestre VII
        Materia("VII","IQ4031","Lab. De Fenómenos De Transporte",0,0,3,1,"''",False,False,"IQ4003","''","''")
        Materia("VII","EL3034","Instrumentación Y Control",3,0,2,4,"''",False,False,"IE5014","''","''")
        Materia("VII","II1114","Investigación De Operaciones I",3,2,0,4,"''",False,False,"II2113","''","''")
        Materia("VII","II1213","Control De Calidad",3,1,0,3,"''",False,False,"II3114","''","''")
        Materia("VII","II1313","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II2113","''","''")
        Materia("VII","II3214","Ingeniería De Costo",3,2,0,4,"''",False,False,"II2113","''","''")
        #Semestre VIII
        Materia("VIII","II3223","Ingeniería Económica",3,1,0,3,"''",False,False,"II3214","''","''")
        Materia("VIII","II1123","Investigación De Operaciones II",3,1,0,3,"''",False,False,"II1114","''","''")
        Materia("VIII","II1323","Mantenimiento Industrial",3,1,0,3,"''",False,False,"II1114","''","''")
        Materia("VIII","II1332","Trabajo Especial I",2,0,0,2,"''",False,False,"II1313","II1213","''")
        Materia("VIII","II2213","Higiene Y Seguridad Industrial",3,1,0,3,"''",False,False,"II2113","''","''")
        Materia("VIII","Según Materia I","Electiva Profesional I",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre IX
        Materia("IX","II1393","Trabajo Especial II",3,0,0,3,"''",False,False,"II1332","''","''")
        Materia("IX","II2333","Instalaciones Industriales",3,0,0,3,"''",False,False,"II1323","''","''")
        Materia("IX","II3263","Teoría De Decisiones",3,1,0,3,"''",False,False,"II3223","''","''")
        Materia("IX","II3243","Proyectos Industriales",3,1,0,3,"''",False,False,"II3223","''","''")
        Materia("IX","II3313","Gerencia De Recursos Humanos",3,0,0,3,"''",False,False,"II1332","''","''")
        Materia("IX","Según Materia II","Electiva Profesional II",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","II24216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")
        
        #Seccion producción
        Materia("Sección Producción","II1363","Diseño De Experimentos",3,0,0,3,"''",False,False,"II1213","''","''")
        Materia("Sección Producción","II1353","Gerencia De Producción",3,0,0,3,"''",False,False,"II1313","''","''")
        Materia("Sección Producción","II1383","Logística Industrial",3,0,0,3,"''",False,False,"II1313","''","''")
        Materia("Sección Producción","II1373","Gestión Y Aseguramiento De La Calidad",3,0,0,3,"''",False,False,"II1213","''","''")
        #Sección Tecnología y entrenamiento industrial
        Materia("Sección Tecnología y Entrenamiento Industrial","II2133","Tópicos De Ingeniería De Métodos",3,0,0,3,"''",False,False,"II3223","''","''")
        Materia("Sección Tecnología y Entrenamiento Industrial","II2223","Elaboración De Programas De Higiene Y Seguridad",3,0,0,3,"''",False,False,"II2213","''","''")
        Materia("Sección Tecnología y Entrenamiento Industrial","II2233","Higiene Industrial E Ingeniería Sanitaria",3,0,0,3,"''",False,False,"II2213","''","''")
        Materia("Sección Tecnología y Entrenamiento Industrial","II2243","Gestión Ambiental",3,0,0,3,"''",False,False,"II2213","''","''")
        #Sección Administración
        Materia("Sección Administración","II3123","Probabilidad Y Estadística Aplicada",3,0,0,3,"''",False,False,"II1213","''","''")
        Materia("Sección Administración","II3253","Finanzas Empresariales",3,0,0,3,"''",False,False,"II3223","''","''")
        Materia("Sección Administración","II3323","Gerencia Y Productividad",3,0,0,3,"''",False,False,"II1213","II1313","''")
        Materia("Sección Administración","II3333","Investigación De Mercado",3,0,0,3,"''",False,False,"II3223","''","''")
        #Entrenamiento Industrial opcional
        Materia("Opcional","II2418","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"II1213","II1313","''", pre3 = "II3214")
        
    elif especialidad=="Ing. Electrónica" and mencion=="Comunicaciones":
        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"''","''","EB2124")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","IE5114","Circuitos Eléctricos I",4,0,0,4,"''",False,False,"EB1125","''","''")
        #Semestre IV
        Materia("IV","EB1144","Cálculo IV",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        Materia("IV","EL1142","Mediciones Eléctricas",1,0,3,2,"''",False,False,"EB2211","''","IE5124")
        Materia("IV","EL1154","Electrónica I",4,0,0,4,"''",False,False,"EB2124","IE5114","''")
        Materia("IV","IE5124","Circuitos Eléctricos II",4,0,0,4,"''",False,False,"IE5114","''","''")
        Materia("IV","IE5131","Lab. De Circuitos Eléctricos",0,0,3,1,"''",False,False,"''","''","IE5124")
        #Semestre V
        Materia("V","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("V","EL1123","Tecnología Electrónica",2,0,3,3,"''",False,False,"EL1154","''","''")
        Materia("V","EL1161","Laboratorio I De Electrónica",0,0,3,1,"''",False,False,"EL1142","''","EL1183")
        Materia("V","EL1183","Electrónica II",3,1,0,3,"''",False,False,"EL1154","''","''")
        Materia("V","EL2113","Análisis De Señales",3,1,0,3,"''",False,False,"EB1144","IE5114","''")
        Materia("V","EL3213","Circuitos Digitales I",3,1,0,3,"''",False,False,"EL1154","''","''")
        Materia("V","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1134","EB1312","''")
        #Semestre VI
        Materia("VI","EL0000","Servicio Comunitario",0,0,0,0,"''",False,False,"87","U.C.","''")
        Materia("VI","EL1181","Lab. II De Electrónica",0,0,3,1,"''",False,False,"EL1161","''","EL1313")
        Materia("VI","EL1313","Electrónica III",3,1,0,3,"''",False,False,"EL1183","''","''")
        Materia("VI","EL2124","Sistemas De Comunicaciones I",3,1,3,4,"''",False,False,"EL2113","''","''")
        Materia("VI","EL2213","Teoría Electromagnética",3,1,0,3,"''",False,False,"EB1144","EB2124","''")
        Materia("VI","EL3163","Teoría De Control",3,1,0,3,"''",False,False,"EL2113","''","''")
        Materia("VI","EL3221","Lab. De Circuitos Digitales I",0,0,3,1,"''",False,False,"EL3213","''","''")
        #Semestre VII
        Materia("VII","EL2223","Radiación Y Propagación",3,1,0,3,"''",False,False,"EL2124","EL2213","''")
        Materia("VII","EL2263","Líneas De Transmisión",3,0,0,3,"''",False,False,"EL2124","EL2213","''")
        Materia("VII","EL2313","Telefonía I",3,0,0,3,"''",False,False,"EL3213","''","''")
        Materia("VII","EL3121","Lab. I De Sistemas De Control",0,0,3,1,"''",False,False,"EL3163","''","''")
        Materia("VII","EL3234","Microprocesadores Y Microcontroladores",3,1,3,4,"''",False,False,"EB1312","EL3221","''")
        Materia("VII","EL3333","Instrumentación Electrónica",2,0,3,3,"''",False,False,"EB1312","EL3221","''")
        #Semestre VIII
        Materia("VIII","EL2153","Sistemas De Comunicaciones I",3,1,0,3,"''",False,False,"EL2124","''","''")
        Materia("VIII","EL2164","Redes De Computadoras",4,0,0,4,"''",False,False,"EL2124","EL3221","''")
        Materia("VIII","EL2273","Comunicaciones Móviles",3,1,0,3,"''",False,False,"EL2263","''","''")
        Materia("VIII","EL2281","Lab. De Microondas",0,0,3,1,"''",False,False,"EL2263","''","''")
        Materia("VIII","EL5112","Trabajo Especial I",2,0,0,2,"''",False,False,"EL3234","EL2223","''")
        Materia("VIII","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        #Semestre IX
        Materia("IX","EL2333","Telefonía II",3,0,0,3,"''",False,False,"EL2313","''","''")
        Materia("IX","EL5123","Trabajo Especial II",3,0,0,3,"''",False,False,"EL5112","''","''")
        Materia("IX","II1033","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("IX","Según Materia I","Electiva Profesional I",0,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia II","Electiva Profesional II",0,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",0,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","EL52216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")
        
        #Electivas
        Materia("*Electiva","EL1623","Análisis De Circuitos Electrónicos Asistido Por Computador",3,0,0,3,"''",False,False,"EL1181","''","''")
        Materia("*Electiva","EL1633","Tópicos Especiales En Electrónica",3,0,0,3,"''",False,False,"EL1313","''","''")
        Materia("*Electiva","EL1643","Electrónica Industrial I",3,0,0,3,"''",False,False,"EL1313","''","''")
        Materia("*Electiva","EL2633","Comunicaciones Vía Satélite",3,1,0,3,"''",False,False,"EL2124","EL2213","''")
        Materia("*Electiva","EL2643","Análisis De Circuitos Electrónicos Para Comunicaciones",3,0,0,3,"''",False,False,"EL1313","EL2124","''")
        Materia("*Electiva","EL2653","Televisión",3,0,0,3,"''",False,False,"EL2124","''","''")
        Materia("*Electiva","EL2673","Ingeniería De Transmisión",3,0,0,3,"''",False,False,"EL2124","''","''")
        Materia("*Electiva","EL2683","Telefonía Móvil Celular",3,0,0,3,"''",False,False,"EL2273","EL2313","''")
        Materia("*Electiva","EL2693","Tópicos Especiales En Comunicaciones",3,0,0,3,"''",False,False,"EL2153","''","''")
        Materia("*Electiva","EL3624","Instrumentación Industrial",3,0,2,4,"''",False,False,"EL3163","''","''")
        Materia("*Electiva","EL3662","Controladores Lógicos Programables",1,0,3,2,"''",False,False,"EL3234","EL3121","''")
        Materia("*Electiva","EL3663","Controladores Lógicos Programables (PLC)",2,0,2,3,"''",False,False,"EL3234","EL3121","''")
        Materia("*Electiva","EL4633","Robótica",2,0,2,3,"''",False,False,"EL3163","EL3234","''")
        Materia("*Electiva","EL4653","Algoritmo Genético Y Sistema De Entrenamiento",3,0,0,3,"''",False,False,"EL3221","EB1312","''")
        Materia("*Electiva","EL4673","Arquitectura Del Computador",3,0,0,3,"''",False,False,"EL3234","''","''")
        Materia("*Electiva","EL4683","Diseño De Sistemas De Computación",3,1,0,3,"''",False,False,"EL3234","''","''")
        Materia("*Electiva","EL4693","Programación II",2,2,0,3,"''",False,False,"EB1312","''","''")
        #Entrenamiento Industrial opcional
        Materia("Opcional","EL5218","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"EL1181","EL3221","''")
    
    
    elif especialidad=="Ing. Electrónica" and mencion=="Computación":

        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"''","''","EB2124")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","IE5114","Circuitos Eléctricos I",4,0,0,4,"''",False,False,"EB1125","''","''")
        #Semestre IV
        Materia("IV","EB1144","Cálculo IV",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        Materia("IV","EL1142","Mediciones Eléctricas",1,0,3,2,"''",False,False,"EB2211","''","IE5124")
        Materia("IV","EL1154","Electrónica I",4,0,0,4,"''",False,False,"EB2124","IE5114","''")
        Materia("IV","IE5124","Circuitos Eléctricos II",4,0,0,4,"''",False,False,"IE5114","''","''")
        Materia("IV","IE5131","Lab. De Circuitos Eléctricos",0,0,3,1,"''",False,False,"''","''","IE5124")
        #Semestre V
        Materia("V","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("V","EL1123","Tecnología Electrónica",2,0,3,3,"''",False,False,"EL1154","''","''")
        Materia("V","EL1161","Laboratorio I De Electrónica",0,0,3,1,"''",False,False,"EL1142","''","EL1183")
        Materia("V","EL1183","Electrónica II",3,1,0,3,"''",False,False,"EL1154","''","''")
        Materia("V","EL2113","Análisis De Señales",3,1,0,3,"''",False,False,"EB1144","IE5114","''")
        Materia("V","EL3213","Circuitos Digitales I",3,1,0,3,"''",False,False,"EL1154","''","''")
        Materia("V","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1312","EB1134","''")
        #Semestre VI
        Materia("VI","EL0000","Servicio Comunitario",0,0,0,0,"''",False,False,"87","U.C.","''")
        Materia("VI","EL1181","Laboratorio II De Electrónica",0,0,3,1,"''",False,False,"EL1161","''","EL1313")
        Materia("VI","EL1313","Electrónica III",3,1,0,3,"''",False,False,"EL1183","''","''")
        Materia("VI","EL2124","Sistemas De Comunicaciones I",3,1,3,4,"''",False,False,"EL2113","''","''")
        Materia("VI","EL3163","Teoría De Control",3,0,0,3,"''",False,False,"EL2113","''","''")
        Materia("VI","EL3221","Lab. De Circuitos Digitales ",0,0,3,1,"''",False,False,"EL3213","''","''")
        Materia("VI","EL4143","Programación II",2,2,0,3,"''",False,False,"EB1213","''","''")
        #Semestre VII
        Materia("VII","EL3121","Lab I De Sits. De Control",0,0,3,1,"''",False,False,"EL3163","''","''")
        Materia("VII","EL3183","Control Digital",3,0,0,3,"''",False,False,"EL3163","''","''")
        Materia("VII","EL3234","Microprocesadores Y Microcontroladores",3,1,3,4,"''",False,False,"EL3221","EB1312","''")
        Materia("VII","EL3333","Instrumentación Electrónica",2,0,3,3,"''",False,False,"EL1313","EL3221","''")
        Materia("VII","EL4153","Estructuras De Datos",2,2,0,3,"''",False,False,"EL4143","''","''")
        Materia("VII","EL4172","Análisis Numérico",2,1,0,2,"''",False,False,"EB1144","EL4143","''")
        #Semestre VIII
        Materia("VIII","EL2164","Redes De Computadoras",4,0,0,4,"''",False,False,"EL2124","EL3221","''")
        Materia("VIII","EL4183","Sistemas Operativos",2,2,0,3,"''",False,False,"EL4153","EL3234","''")
        Materia("VIII","EL4333","Diseño De Sistemas De Computación",3,1,0,3,"''",False,False,"EL3234","''","''")
        Materia("VIII","EL5112","Trabajo Especial I",2,0,0,2,"''",False,False,"EL3234","EL4153","''")
        Materia("VIII","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        Materia("VIII","Según Materia I","Electiva Profesional I",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre IX
        Materia("IX","EL4341","Laboratorio Diseño De Sistemas De Computación",0,0,3,1,"''",False,False,"EL4333","''","''")
        Materia("IX","EL4373","Arquitectura Del Computador",3,0,0,3,"''",False,False,"EL3234","''","''")
        Materia("IX","EL5123","Trabajo Especial II",3,0,0,3,"''",False,False,"EL5112","''","''")
        Materia("IX","II1033","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("IX","Según Materia II","Electiva Profesional II",3,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","EL52216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")

        #Electivas
        Materia("*Electiva","EL1623","Análisis De Circuitos Electrónicos Asistido Por Computador",3,0,0,3,"''",False,False,"EL1181","''","''")
        Materia("*Electiva","EL1633","Tópicos Especiales En Electrónica",3,0,0,3,"''",False,False,"EL1313","''","''")
        Materia("*Electiva","EL1643","Electrónica Industrial I",3,0,0,3,"''",False,False,"EL1313","''","''")
        Materia("*Electiva","EL2643","Análisis Circuitos Electrónicos Para Comunicaciones",3,0,0,3,"''",False,False,"EL1313","EL2124","''")
        Materia("*Electiva","EL2653","Televisión",3,0,0,3,"''",False,False,"EL2124","''","''")
        Materia("*Electiva","EL2673","Ingeniería De Transmisión",3,0,0,3,"''",False,False,"EL2124","''","''")
        Materia("*Electiva","EL3624","Instrumentación Industrial",3,0,2,4,"''",False,False,"EL3163","''","''")
        Materia("*Electiva","EL3653","Control De Sistemas a Eventos Discretos",3,1,0,3,"''",False,False,"EL3163","''","''")
        Materia("*Electiva","EL3662","Controladores Lógicos Programables",1,0,3,2,"''",False,False,"EL3234","EL3121","''")
        Materia("*Electiva","EL3663","Controladores Lógicos Programables (PLC)",2,0,2,3,"''",False,False,"EL3234","EL3121","''")
        Materia("*Electiva","EL3683","Sistemas De Control En Tiempo Continuo",3,1,0,3,"''",False,False,"EL3163","''","''")
        Materia("*Electiva","EL3693","Sistemas De Control En Tiempo Discreto",3,1,0,3,"''",False,False,"EL3163","EL3234","''")
        Materia("*Electiva","EL4603","Tópicos Especiales En Computación",3,0,0,3,"''",False,False,"EL4333","''","''")
        Materia("*Electiva","EL4633","Robótica",2,0,2,3,"''",False,False,"EL3163","EL3234","''")
        Materia("*Electiva","EL4643","Diseño De Software",2,2,0,3,"''",False,False,"EL4143","''","''")
        Materia("*Electiva","EL4653","Algoritmo Genético Y Sistema De Entrenamiento",3,0,0,3,"''",False,False,"EL3221","EB1312","''")
        
        #Entrenamiento Industrial opcional
        Materia("Opcional","EL5218","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"EL1181","EL3221","''")
    
    elif especialidad=="Ing. Electrónica" and mencion=="Control":
        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"''","''","EB2124")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","IE5114","Circuitos Eléctricos I",4,0,0,4,"''",False,False,"EB1125","''","''")
        #Semestre IV
        Materia("IV","EB1144","Cálculo IV",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        Materia("IV","EL1142","Mediciones Eléctricas",1,0,3,2,"''",False,False,"EB2211","''","IE5124")
        Materia("IV","EL1154","Electrónica I",4,0,0,4,"''",False,False,"EB2124","IE5114","''")
        Materia("IV","IE5124","Circuitos Eléctricos II",4,0,0,4,"''",False,False,"IE5114","''","''")
        Materia("IV","IE5131","Lab. De Circuitos Eléctricos",0,0,3,1,"''",False,False,"''","''","IE5124")
        #Semestre V
        Materia("V","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("V","EL1123","Tecnología Electrónica",2,0,3,3,"''",False,False,"EL1154","''","''")
        Materia("V","EL1161","Laboratorio I De Electrónica",0,0,3,1,"''",False,False,"EL1142","''","EL1183")
        Materia("V","EL1183","Electrónica II",3,1,0,3,"''",False,False,"EL1154","''","''")
        Materia("V","EL2113","Análisis De Señales",3,1,0,3,"''",False,False,"EB1144","IE5114","''")
        Materia("V","EL3213","Circuitos Digitales",3,1,0,3,"''",False,False,"EL1154","''","''")
        Materia("V","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1312","EB1134","''")
        #Semestre VI
        Materia("VI","EL0000","Servicio Comunitario",0,0,0,0,"''",False,False,"87","U.C.","''")
        Materia("VI","EL1181","Lab II De Electrónica",0,0,3,1,"''",False,False,"EL1161","''","EL1313")
        Materia("VI","EL1313","Electrónica III",3,1,0,3,"''",False,False,"EL1183","''","''")
        Materia("VI","EL2124","Sistemas De Comunicaciones I",3,1,3,4,"''",False,False,"EL2113","''","''")
        Materia("VI","EL3163","Teoría De Control",3,1,0,3,"''",False,False,"EL2113","''","''")
        Materia("VI","EL3221","Lab. De Circuitos Digitales I",0,0,3,1,"''",False,False,"EL3213","''","''")
        Materia("VI","IE6013","Máquinas Eléctricas",3,0,0,3,"''",False,False,"IE5124","''","''")
        #Semestre VII
        Materia("VII","EL1223","Electrónica Industrial I",3,0,0,3,"''",False,False,"EL1313","''","''")
        Materia("VII","EL3121","Laboratorio I De Sistemas De Control",0,0,3,1,"''",False,False,"EL3163","''","''")
        Materia("VII","EL3173","Sistemas De Control En Tiempo Contínuo",3,1,0,3,"''",False,False,"EL3163","''","''")
        Materia("VII","EL3234","Microprocesadores Y Microcontroladores",3,1,3,4,"''",False,False,"EB1312","EL3221","''")
        Materia("VII","EL3333","Instrumentación Electrónica",2,0,3,3,"''",False,False,"EL1313","EL3221","''")
        Materia("VII","IE6021","Laboratorio De Máquinas Eléctricas",0,0,3,1,"''",False,False,"EL1142","IE6013","''")
        #Semestre VIII
        Materia("VIII","EL1243","Electrónica Industrial II",3,1,0,3,"''",False,False,"EL1223","''","''")
        Materia("VIII","EL3142","Laboratorio II De Sistemas De Control",1,0,3,2,"''",False,False,"EL3121","EL3221","EL3193")
        Materia("VIII","EL3193","Sistemas De Control En Tiempo Discreto",3,1,0,3,"''",False,False,"EL3173","EL3234","''")
        Materia("VIII","EL5112","Trabajo Especial I",2,0,0,2,"''",False,False,"EL3234","EL1223","''")
        Materia("VIII","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        Materia("VIII","Según Materia I","Electiva Profesional I",0,0,0,3,"''",False,False,"''","''","''")
        #Semestre IX
        Materia("IX","EL1252","Laboratorio De Electrónica Industrial",1,0,3,2,"''",False,False,"''","''","EL1243")
        Materia("IX","EL3324","Instrumentación Industrial",3,0,2,4,"''",False,False,"EL3163","''","''")
        Materia("IX","EL5123","Trabajo Especial II",3,0,0,3,"''",False,False,"EL5112","''","''")
        Materia("IX","II1033","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("IX","Según Materia II","Electiva Profesional II",0,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",0,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","EL52216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")
            
        #Electivas
        Materia("*Electiva","EL1623","Análisis De Circuitos Electrónicos Asistido Por Computador",3,0,0,3,"''",False,False,"EL1181","''","''")
        Materia("*Electiva","EL1633","Tópicos Especiales En Electrónica",3,0,0,3,"''",False,False,"EL1313","''","''")
        Materia("*Electiva","EL2653","Televisión",3,0,0,3,"''",False,False,"EL2124","''","''")
        Materia("*Electiva","EL2664","Redes De Computadoras",3,1,0,3,"''",False,False,"EL2124","EL3221","''")
        Materia("*Electiva","EL2643","Análisis Circuitos Eléctricos Para Comunicaciones",3,0,0,3,"''",False,False,"EL1313","EL2124","''")
        Materia("*Electiva","EL2673","Ingeniería De Transmisión",3,0,0,3,"''",False,False,"EL2124","''","''")
        Materia("*Electiva","EL3613","Tópicos Especiales En Control",3,0,0,3,"''",False,False,"EL3193","''","''")
        Materia("*Electiva","EL3653","Control De Sistemas a Eventos Discretos",3,1,0,3,"''",False,False,"EL3163","''","''")
        Materia("*Electiva","EL3662","Controladores Lógicos Programables",1,0,3,2,"''",False,False,"EL3234","EL3121","''")
        Materia("*Electiva","EL3663","Controladores Lógicos Programables (PLC)",2,0,2,3,"''",False,False,"EL3234","EL3121","''")
        Materia("*Electiva","EL4633","Robótica",2,0,2,3,"''",False,False,"EL3163","EL3234","''")
        Materia("*Electiva","EL4653","Algoritmo Genético Y Sistema De Entrenamiento",3,0,0,3,"''",False,False,"EL3221","EB1312","''")
        Materia("*Electiva","EL4673","Arquitectura Del Computador",3,0,0,3,"''",False,False,"EL3234","''","''")
        Materia("*Electiva","EL4683","Diseño De Sistemas De Computación",3,1,0,3,"''",False,False,"EL3234","''","''")
        Materia("*Electiva","EL4693","Programación II",2,2,0,3,"''",False,False,"EB1312","''","''")
    
        #Entrenamiento Industrial opcional
        Materia("Opcional","EL5218","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"EL1181","EL3221","''")
    
    elif especialidad=="Ing. Eléctrica":
        
        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"''","''","EB2124")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","IE5114","Circuitos Eléctricos I",4,0,0,4,"''",False,False,"EB1125","''","''")
        #Semestre IV
        Materia("IV","EB1144","Cálculo IV",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","IE5124","Circuitos Eléctricos II",4,0,0,4,"''",False,False,"IE5114","''","EB1144")
        Materia("IV","IE5213","Electrometría",3,0,0,3,"''",False,False,"IE5114","''","''")
        Materia("IV","IE5221","Laboratorio Electrometría",0,0,3,1,"''",False,False,"EB2211","''","IE5213")
        Materia("IV","IE6112","Máquinas Eléctricas I",2,1,0,2,"''",False,False,"IE5114","''","''")
        Materia("IV","EB6542","Introducción A La Administracion",2,0,0,2,"''",False,False,"40","U.C.","''")
        #Semestre V
        Materia("V","EL1013","Electrónica Analógica",3,1,0,3,"''",False,False,"IE5114","''","''")
        Materia("V","EL3013","Teoría De Control",3,1,0,3,"''",False,False,"IE5114","EB1144","''")
        Materia("V","IE5131","Laboratorio Circuitos Eléctricos",0,0,3,1,"''",False,False,"IE5124","IE5221","''")
        Materia("V","IE5313","Teoría Electromagnética",3,1,0,3,"''",False,False,"EB1144","EB2124","''")
        Materia("V","IE6122","Maquinas Eléctricas II",2,1,0,2,"''",False,False,"IE5124","IE6112","''")
        Materia("V","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1134","EB1312","''")
        #Semestre VI
        Materia("VI","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        Materia("VI","EL1033","Circuitos Digitales I",3,0,0,3,"''",False,False,"EL1013","''","''")
        Materia("VI","EL1041","Lab. De Electrónica",0,0,3,1,"''",False,False,"IE5131","''","EL1033")
        Materia("VI","IE6134","Máquinas Electricas III",4,0,0,4,"''",False,False,"IE6122","''","''")
        Materia("VI","IE6214","Materiales Eléctricos",3,0,2,4,"''",False,False,"IE5313","IE6122","''")
        Materia("VI","IE7113","Transmisión Energía Eléctrica I",3,0,0,3,"''",False,False,"IE5124","''","''")
        Materia("VI","IE7514","Instalaciones Electricas I",4,0,0,4,"''",False,False,"IE5124","IE6122","''")
        #Semestre VII
        Materia("VII","EL1054","Electrónica Industrial",3,0,3,4,"''",False,False,"EL1033","EL1041","''")
        Materia("VII","IE6142","Laboratorio De Máquinas Eléctricas",0,0,5,2,"''",False,False,"IE6134","IE5131","''")
        Materia("VII","IE7213","Análisis Sistemas Eléctricos De Potencia I",3,1,0,3,"''",False,False,"IE7113","IE6134","''")
        Materia("VII","IE7523","Instalaciones Electricas II",3,0,0,3,"''",False,False,"IE7514","''","''")
        Materia("VII","IE7613","Redes Eléctricas",3,0,0,3,"''",False,False,"IE7514","''","''")
        Materia("VII","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        #Semestre VIII
        Materia("VIII","II1043","Gestión De Mantenimiento",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("VIII","IE6314","Controles Eléctricos",3,0,3,4,"''",False,False,"IE6142","''","''")
        Materia("VIII","IE7313","Protección De Sistemas Eléctricos De Potencia",3,0,0,3,"''",False,False,"IE7213","''","''")
        Materia("VIII","IE8212","Trabajo Especial I",2,0,0,2,"''",False,False,"IE7213","IE7613","''")
        Materia("VIII","Según Materia I","Electiva Profesional I",3,0,0,3,"''",False,False,"''","''","''")
        Materia("VIII","Según Materia II","Electiva Profesional II",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre IX
        Materia("IX","IE7321","Lab. Protección Sistemas De Potencia",0,0,3,1,"''",False,False,"IE7313","''","''")
        Materia("IX","IE7413","Plantas Eléctricas Y Subestaciones",3,1,0,3,"''",False,False,"IE6134","IE7313","''")
        Materia("IX","IE8223","Trabajo Especial II",3,0,0,3,"''",False,False,"IE8212","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",3,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia IV","Electiva Profesional IV",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","IE81116","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")
        #Electivas
        Materia("*Electiva","EL3034","Instrumentación Industrial",3,0,3,4,"''",False,False,"EL1054","''","''")
        Materia("*Electiva","IE7753","Controles Eléctricos II",2,0,3,3,"''",False,False,"IE6314","''","''")
        Materia("*Electiva","IE7713","Transmisión Energía Eléctrica II",3,0,0,3,"''",False,False,"IE7113","''","''")
        Materia("*Electiva","IE7723","Análisis Sistemas Eléctricos De Potencia II",3,1,0,3,"''",False,False,"IE7213","''","''")
        Materia("*Electiva","IE7733","Técnicas De Alta Tensión",2,0,3,3,"''",False,False,"IE6214","IE5313","''")
        Materia("*Electiva","IE7763","Control Y Operación De Sistemas De Potencia",3,1,0,3,"''",False,False,"IE6134","''","''")
        Materia("*Electiva","IE7743","Planificación Sistemas De Potencia",3,0,0,3,"''",False,False,"IE7213","''","''")
        Materia("*Electiva Producción","II1033","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva Producción","II1053","Control De Calidad",3,0,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva Producción","II3013","Ingeniería De Costos",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva Producción","II1073","Diseño De Experimentos",3,0,0,3,"''",False,False,"II1053","''","''")
        #Entrenamiento Industrial opcional
        Materia("Opcional","IE8128","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"IE7213","IE7613","''")
        
    
    elif especialidad=="Ing. Mecánica":
        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"EB1125","''","EB2124")
        Materia("III","IM1112","Dibujo De Máquina",1,3,0,2,"''",False,False,"EB3122","''","''")
        Materia("III","IM1253","Mecánica Aplicada I",3,1,0,3,"''",False,False,"EB1125","EB2115","''")
        #Semestre IV
        Materia("IV","EB1154","Matemáticas Especiales",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("IV","IE5014","Fundamentos De Ingeniería Eléctrica",3,0,2,4,"''",False,False,"EB1134","EB2211","''")
        Materia("IV","IM1263","Mecánica Aplicada II",3,1,0,3,"''",False,False,"IM1253","''","''")
        #Semestre V
        Materia("V","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1134","EB1312","''")
        Materia("V","IM1273","Mecanismos",3,1,0,3,"''",False,False,"IM1263","''","''")
        Materia("V","IM1324","Resistencia De Materiales",4,0,0,4,"''",False,False,"IM1253","''","''")
        Materia("V","IM1331","Ensayos Resistencia De Materiales",0,0,2,1,"''",False,False,"IM1253","''","IM1324")
        Materia("V","IM2114","Máquinas Herramientas",2,0,6,4,"''",False,False,"IM1112","''","''")
        Materia("V","IM3153","Termodinámica I",3,0,0,3,"''",False,False,"EB1154","EB2211","''")
        #Semestre VI
        Materia("VI","IM1443","Elementos De Máquinas I",3,1,0,3,"''",False,False,"IM1273","IM1324","''")
        Materia("VI","IM2314","Metrología Y Calidad",3,0,2,4,"''",False,False,"IM2114","II3043","''")
        Materia("VI","IM3163","Termodinámica II",3,0,0,3,"''",False,False,"IM3153","''","''")
        Materia("VI","IM3224","Mecánica De Fluidos",3,2,1,4,"''",False,False,"IM3153","''","''")
        Materia("VI","MT1015","Tecnología De Materiales",4,0,2,5,"''",False,False,"IM1331","''","''")
        Materia("VI","IM0000","Servicio Comunitario",0,0,0,0,"''",False,False,"89","U.C.","''")
        #Semestre VII
        Materia("VII","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("VII","EL3034","Instrumentación Y Control",3,0,2,4,"''",False,False,"IE5014","''","''")
        Materia("VII","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        Materia("VII","IM1453","Elementos De Máquinas II",3,0,0,3,"''",False,False,"IM1443","''","''")
        Materia("VII","IM2234","Tecnología Mecánica I",3,0,2,4,"''",False,False,"IM2314","''","''")
        Materia("VII","IM3234","Máquinas E Instalaciones Hidráulicas",3,0,2,4,"''",False,False,"IM3224","''","''")
        #Semestre VIII
        Materia("VIII","IM1463","Vibraciones Y Balanceo",3,0,0,3,"''",False,False,"IM1453","''","''")
        Materia("VIII","IM2244","Tecnología Mecánica II",3,0,3,4,"''",False,False,"IM2234","''","''")
        Materia("VIII","IM3173","Máquinas Térmicas I",3,0,0,3,"''",False,False,"IM3234","IM3163","''")
        Materia("VIII","IM3323","Transferencia De Calor",3,1,0,3,"''",False,False,"IM1154","IM3234","''")
        Materia("VIII","IM4112","Trabajo Especial I",2,0,0,2,"''",False,False,"IM1453","IM3234","''")
        Materia("VIII","MT4053","Soldadura",2,0,2,3,"''",False,False,"MT1015","''","''")
        #Semestre IX
        Materia("IX","II1043","Gestión De Mantenimiento",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("IX","IM3184","Máquinas Térmicas II",3,0,2,4,"''",False,False,"IM3173","''","''")
        Materia("IX","IM4123","Trabajo Especial II",3,0,0,3,"''",False,False,"IM4112","''","''")
        Materia("IX","Según Materia I","Electiva Profesional I",4,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia II","Electiva Profesional II",4,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",4,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","IM51216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")

        #Electivas
        Materia("*Electiva","II1053","Control De Calidad",3,0,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva","II3013","Costos",3,1,0,3,"''",False,False,"II3023","''","''")
        Materia("*Electiva","IM3253","Neumática",3,0,1,3,"''",False,False,"IM3234","IM3163","''")
        Materia("*Electiva","IM3633","Tribología",3,0,1,3,"''",False,False,"IM1453","''","''")
        Materia("*Electiva","MT2013","Corrosión",2,0,2,3,"''",False,False,"MT1015","''","''")
        Materia("*Electiva","MT1223","Ensayos No Destructivos",2,0,2,3,"''",False,False,"MT4053","''","''")
        Materia("*Electiva","MT4023","Fundición",2,0,3,3,"''",False,False,"MT1015","''","''")
        Materia("*Electiva","MT1013","Tratamientos Térmicos",2,0,2,3,"''",False,False,"MT1015","''","''")
        Materia("*Electiva","IM3333","Refrigeración Y Aire Acondicionado",3,0,1,3,"''",False,False,"IM3323","''","''")
        Materia("*Electiva","IM2433","Control Numérico",3,1,0,3,"''",False,False,"IM2244","''","''")
        Materia("*Electiva","IM2413","Mantenimiento Mecánico",3,1,0,3,"''",False,False,"IM2244","''","''")
        Materia("*Electiva","IM3243","Sistemas Hidráulicos",3,0,1,3,"''",False,False,"IM3234","''","''")
        #Entrenamiento Industrial opcional
        Materia("Opcional","IM5118","Entrenamiento Industrial Opcional",0,40,0,8,"''",False,False,"IM1453","IM3234","''", pre3 = "125")
        
        
    elif especialidad=="Ing. Química":
        
        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","IQ3121","Lab. De Química General",0,0,3,1,"''",False,False,"''","''","IQ3213")
        Materia("III","IQ3213","Química Analítica",3,1,0,3,"''",False,False,"IQ5113","EB1125","''")
        #Semestre IV
        Materia("IV","EB1154","Matemáticas Especiales",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1213","EB1125","''")
        Materia("IV","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"''","''","EB2124")
        Materia("IV","IQ3113","Elementos De Físico-Química",3,1,0,3,"''",False,False,"EB1125","IQ5113","''")
        Materia("IV","IQ3222","Lab. De Química Analítica",0,0,6,2,"''",False,False,"IQ3213","IQ3121","''")
        Materia("IV","IQ4113","Principios De Ingeniería Química",3,1,0,3,"''",False,False,"EB1134","IQ3213","IQ3113")
        #Semestre V
        Materia("V","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        Materia("V","IE5014","Fundamentos De Ingeniería Eléctrica",3,0,2,4,"''",False,False,"EB2211","EB1134","''")
        Materia("V","IM1013","Fundamentos De Resistencia De Materiales",3,0,0,3,"''",False,False,"EB2211","EB1134","''")
        Materia("V","IQ3313","Química Orgánica I",3,1,0,3,"''",False,False,"IQ3113","IQ3213","''")
        Materia("V","IQ4213","Termodinánica I",3,1,0,3,"''",False,False,"IQ4113","''","''")
        Materia("V","IQ4313","Fenómenos De Transporte I",3,1,0,3,"''",False,False,"''","''","IQ4213")
        #Semestre VI
        Materia("VI","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("VI","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        Materia("VI","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1134","EB1312","''")
        Materia("VI","IQ3233","Análisis Instrumental",3,0,0,3,"''",False,False,"EB2211","''","IQ3323")
        Materia("VI","IQ3323","Química Orgánica II",3,0,0,3,"''",False,False,"IQ3313","IQ3222","''")
        Materia("VI","IQ4224","Termodinánica II",4,0,0,4,"''",False,False,"IQ4213","EB1154","''")
        Materia("VI","IQ4334","Fenómenos De Transporte II",4,0,0,4,"''",False,False,"IQ4313","''","IQ4224")
        Materia("VI","IQ0000","Servicio Comunitario",0,0,0,0,"''",False,False,"87","U.C.","''")
        #Semestre VII
        Materia("VII","II1053","Control De Calidad",3,0,0,3,"''",False,False,"II3043","''","''")
        Materia("VII","IQ3241","Lab. De Análisis Intrumental",0,0,3,1,"''",False,False,"IQ3233","''","''")
        Materia("VII","IQ3332","Lab. De Química Orgánica",0,0,6,2,"''",False,False,"IQ3323","''","IQ3241")
        Materia("VII","IQ3413","Cinética Química",3,0,0,3,"''",False,False,"IQ3323","IQ4334","''")
        Materia("VII","IQ4331","Lab. De Fenómenos De Transporte",0,0,3,1,"''",False,False,"IQ4334","''","''")
        Materia("VII","IQ4414","Operaciones Unitarias I",4,0,0,4,"''",False,False,"IQ4334","IQ4224","''")
        #Semestre VIII
        Materia("VIII","EL3034","Instrumentación Y Control",3,0,2,4,"''",False,False,"IE5014","IQ4331","''")
        Materia("VIII","III1033","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("VIII","IQ3421","Lab. De Termodinánica Y Cinética",0,0,3,1,"''",False,False,"IQ3413","IQ4224","''")
        Materia("VIII","IQ4424","Operaciones Unitarias II",4,0,0,4,"''",False,False,"IQ4414","''","''")
        Materia("VIII","IQ4513","Reactores Químicos",3,1,0,3,"''",False,False,"IQ3413","IQ4224","''")
        Materia("VIII","IQ4532","Trabajo Especial I",2,0,0,2,"''",False,False,"IQ3241","IQ4414","''")
        Materia("VIII","Según Materia I","Electiva Profesional I",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre IX
        Materia("IX","IQ4432","Lab. De Operaciones Unitarias",0,0,5,2,"''",False,False,"IQ4424","IQ4331","''")
        Materia("IX","IQ4523","Ingeniería De Procesos",3,1,0,3,"''",False,False,"IQ4513","IQ4414","''")
        Materia("IX","IQ4543","Trabajo Especial II",3,0,0,3,"''",False,False,"IQ4532","''","IQ4432")
        Materia("IX","Según Materia II","Electiva Profesional II",3,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","IQ47216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")
        
        #Electivas
        Materia("*Electiva","IQ3613","Química De Alimentos",3,0,0,3,"''",False,False,"IQ3323","IQ4334","''")
        Materia("*Electiva","IQ3623","Introducción A La Tecnología De Alimentos",3,0,0,3,"''",False,False,"IQ3613","''","''")
        Materia("*Electiva","IQ4613","Introducción A La Ingeniería Ambiental",3,0,0,3,"''",False,False,"IQ3323","IQ4334","''")
        Materia("*Electiva","IQ4623","Tratamiento De Aguas",3,0,0,3,"''",False,False,"IQ4613","''","''")
        Materia("*Electiva","IQ4633","Tratamiento De Aguas Residuales",3,0,0,3,"''",False,False,"IQ4613","''","''")
        Materia("*Electiva","IQ4653","Refinación De Petróleo I",3,0,0,3,"''",False,False,"IQ3323","''","IQ4513")
        Materia("*Electiva","IQ4663","Refinación De Petróleo II",3,0,0,3,"''",False,False,"IQ4653","''","''")
        Materia("*Electiva","IQ4673","Control De Procesos",3,0,0,3,"''",False,False,"EL3034","IQ4513","''")
        Materia("*Electiva","IQ4683","Simulación De Procesos Químicos",3,0,0,3,"''",False,False,"IQ4513","IQ4424","IQ4523")
        Materia("*Electiva","IQ3633","Procesos, Mejoramiento De Crudos Pesados, Extra-Pesados Y Residuales",3,0,0,3,"''",False,False,"IQ3323","IQ3233","''")
        Materia("*Electiva","IQ4693","Petroquímica",3,0,0,3,"''",False,False,"IQ3332","''","IQ4513")
        Materia("*Electiva","IQ4643","Tratamiento De Desechos Sólidos",3,3,0,3,"''",False,False,"IQ4613","''","''")
        #Entrenamiento Industrial opcional
        Materia("Opcional","IQ4718","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"IQ3241","IQ4414","''")
        
    
    elif especialidad=="Ing. Metalúrgica":

        #Semestre I
        Materia("I","EB1115","Cálculo I",4,2,0,5,"''",False,True,"''","''","''")
        Materia("I","EB3112","Dibujo I",1,3,0,2,"''",False,True,"''","''","''")
        Materia("I","EB4121","Inglés Técnico I",0,3,0,1,"''",False,True,"''","''","''")
        Materia("I","EB6113","Lenguaje Y Redacción",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","EB6411","Actividades Complementarias",0,2,0,1,"''",False,True,"''","''","''")
        Materia("I","EB7113","DHP I",3,0,0,3,"''",False,True,"''","''","''")
        Materia("I","IQ5113","Química General",3,1,0,3,"''",False,True,"''","''","''")
        #Semestre II
        Materia("II","EB1125","Cálculo II",4,2,0,5,"''",False,False,"EB1115","''","''")
        Materia("II","EB2115","Física I",5,1,0,5,"''",False,False,"''","''","EB1125")
        Materia("II","EB3122","Dibujo II",1,3,0,2,"''",False,False,"EB3112","''","''")
        Materia("II","EB4131","Inglés Técnico II",0,3,0,1,"''",False,False,"EB4121","''","''")
        Materia("II","EB7123","DHP II",3,0,0,3,"''",False,False,"EB7113","''","''")
        Materia("II","EB7212","Lectura Crítica",1,2,0,2,"''",False,False,"EB7113","''","''")
        #Semestre III
        Materia("III","EB1134","Cálculo III",3,3,0,4,"''",False,False,"EB1125","''","EB1213")
        Materia("III","EB1213","Álgebra Lineal",2,2,0,3,"''",False,False,"EB1115","''","''")
        Materia("III","EB2124","Física II",3,3,0,4,"''",False,False,"EB2115","EB1125","''")
        Materia("III","EB2211","Laboratorio De Física",0,0,3,1,"''",False,False,"EB1125","''","EB2124")
        Materia("III","EB7133","DHP III",3,0,0,3,"''",False,False,"EB7123","''","''")
        Materia("III","MT2103","Físico - Química",3,0,0,3,"''",False,False,"IQ5113","EB1125","''")
        #Semestre IV
        Materia("IV","EB1154","Matemáticas Especiales",3,3,0,4,"''",False,False,"EB1134","EB1213","''")
        Materia("IV","EB1312","Programación",1,2,0,2,"''",False,False,"EB1125","EB1213","''")
        Materia("IV","EB6542","Introducción A La Administración",2,0,0,2,"''",False,False,"40","U.C.","''")
        Materia("IV","IM1043","Mecánica Aplicada",3,1,0,3,"''",False,False,"EB1213","EB3122","''")
        Materia("IV","IQ3022","Análisis Químico Metalúrgico",0,0,5,2,"''",False,False,"MT2103","''","''")
        Materia("IV","MT2133","Procesos Metalúrgicos",3,0,0,3,"''",False,False,"MT2103","EB2124","''")
        Materia("IV","MT2143","Termodinámica Metalúrgica",3,1,0,3,"''",False,False,"EB1134","MT2103","''")
        #Semestre V
        Materia("V","IE5014","Fundamentos De Ing. Eléctrica",3,0,2,4,"''",False,False,"EB2211","EB1134","''")
        Materia("V","II3043","Probabilidad Y Estadística",3,1,0,3,"''",False,False,"EB1134","EB1312","''")
        Materia("V","IM1054","Resistencia Y Ensayo De Materiales",3,1,2,4,"''",False,False,"IM1043","''","''")
        Materia("V","IQ4013","Fenómenos De Transporte I",3,1,0,3,"''",False,False,"MT2143","EB1154","''")
        Materia("V","MT1134","Metalurgia Física I",3,0,2,4,"''",False,False,"EB1154","MT2143","''")
        Materia("V","MT2212","Metalurgia Extractiva I",2,0,0,2,"''",False,False,"MT2133","''","''")
        #Semestre VI
        Materia("VI","EB6552","Administración De Empresas",2,0,0,2,"''",False,False,"60","U.C.","''")
        Materia("VI","II3023","Ingeniería Económica",3,0,0,3,"''",False,False,"EB1134","''","''")
        Materia("VI","IM2014","Tecnología De Fabricación I",3,0,3,4,"''",False,False,"IM1054","''","''")
        Materia("VI","IQ4034","Fenómenos De Transporte II",4,0,0,4,"''",False,False,"IQ4013","''","''")
        Materia("VI","MT1144","Metalurgia Física II",3,0,2,4,"''",False,False,"MT1134","''","''")
        Materia("VI","MT2222","Metalurgia Extractiva II",2,0,0,2,"''",False,False,"MT2212","IQ4013","''")
        #Semestre VII
        Materia("VII","II1053","Control De Calidad",3,0,0,3,"''",False,False,"II3043","''","''")
        Materia("VII","IM2054","Tecnología De Fabricación II",3,0,3,4,"''",False,False,"IM2014","''","''")
        Materia("VII","IQ4031","Lab. De Fenómenos De Transporte",0,0,3,1,"''",False,False,"IQ4034","''","''")
        Materia("VII","MT1313","Tratamientos Térmicos",2,0,2,3,"''",False,False,"MT1144","IQ4034","''")
        Materia("VII","MT2231","Lab. De Metalurgia Extractiva",0,0,3,1,"''",False,False,"MT2222","IQ3022","''")
        Materia("VII","MT4213","Fundición",2,0,3,3,"''",False,False,"IQ4034","MT1144","''")
        #Semestre VIII
        Materia("VIII","MT2323","Corrosión",2,0,2,3,"''",False,False,"MT1144","''","''")
        Materia("VIII","MT3112","Metalurgia Mecánica I",2,0,0,2,"''",False,False,"MT1144","IM1054","''")
        Materia("VIII","MT4123","Ingeniería De La Soldadura",2,0,2,3,"''",False,False,"MT4213","IE5014","''")
        Materia("VIII","MT4234","Siderúrgia",4,0,0,4,"''",False,False,"MT2222","IQ4034","''")
        Materia("VIII","MT5112","Trabajo Especial I",2,0,0,2,"''",False,False,"MT4213","MT1313","''", pre3 = "MT2231")
        Materia("VIII","Según Materia I","Electiva Profesional I",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre IX
        Materia("IX","MT1223","Ensayos No Destructivos",2,0,2,3,"''",False,False,"MT4123","''","''")
        Materia("IX","MT3132","Metalurgia Mecánica II",2,0,0,2,"''",False,False,"MT3112","IM2054","''")
        Materia("IX","MT5123","Trabajo Especial II",3,0,0,3,"''",False,False,"MT5112","''","''")
        Materia("IX","MT3111","Laboratorio Metalurgia Mecánica",0,0,2,1,"''",False,False,"MT3112","''","''")
        Materia("IX","Según Materia II","Electiva Profesional II",3,0,0,3,"''",False,False,"''","''","''")
        Materia("IX","Según Materia III","Electiva Profesional III",3,0,0,3,"''",False,False,"''","''","''")
        #Semestre X
        Materia("X","MT52216","Entrenamiento Industrial",40,0,0,16,"''",False,False,"Aprobar todo el pensum","''","''")
        
        #Electivas
        Materia("*Electiva","EL3034","Instrumentación Y Control",3,0,2,4,"''",False,False,"IE5014","''","''")
        Materia("*Electiva","II1033","Planificación Y Control De La Producción",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva","II1043","Gestión De Mantenimiento",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva","II1073","Diseño De Experimentos",3,0,0,3,"''",False,False,"II1053","''","''")
        Materia("*Electiva","II3013","Ingeniería De Costos",3,1,0,3,"''",False,False,"II3043","''","''")
        Materia("*Electiva","MT1613","Metalografía Industrial",2,0,2,3,"''",False,False,"MT1313","''","''")
        Materia("*Electiva","MT1623","Aceros Especiales",3,0,0,3,"''",False,False,"MT1313","''","''")
        Materia("*Electiva","MT3633","Analisis De Fallas",3,0,0,3,"''",False,False,"MT3112","''","''")
        Materia("*Electiva","MT4683","Colada Continua",3,0,0,3,"''",False,False,"MT4234","MT4213","''")
        Materia("*Electiva","MT2613","Tratamientos De Superficie",3,0,0,3,"''",False,False,"MT2323","''","''")
        Materia("*Electiva","MT2643","Concentración De Minerales",2,0,2,3,"''",False,False,"MT2231","''","''")
        Materia("*Electiva","MT3613","Metalurgia Del Mecanizado",3,0,0,3,"''",False,False,"IM2014","MT3112","''")
        Materia("*Electiva","IM3023","Tribologia",3,0,1,3,"''",False,False,"IM2054","''","''")
        Materia("*Electiva","MT4653","Fundición Avanzada",3,0,0,3,"''",False,False,"MT4213","''","''")
        Materia("*Electiva","MT4663","Materiales Refractarios",2,0,2,3,"''",False,False,"MT1144","MT2222","''")
        Materia("*Electiva","MT4673","Tecnología Del Aluminio",3,0,0,3,"''",False,False,"MT1144","MT2222","''")
        #Entrenamiento Industrial opcional
        Materia("Opcional","MT5218","Entrenamiento Industrial Opcional",0,0,0,8,"''",False,False,"MT1313","MT2231","''")

    
    Logger.info("Finalizó cargado de materias por defecto")
    return Materia.materias[:]

def migrar_datos(version_guardada):
    Logger.info("Iniciando migración de datos")
    version_entero = int(version_guardada[0] + version_guardada[2] + version_guardada[4:])
    
    lista_sufijos = {"industrial": "Ing. Industrial", "electronica_comunicaciones": "Comunicaciones", "electronica_computacion" : "Computación",
                     "electronica_control" : "Control", "electrica": "Ing. Eléctrica",
                     "mecanica" : "Ing. Mecánica", "metalurgica" : "Ing. Metalúrgica", "quimica": "Ing. Química"}
    
    for archivo, especialidad in lista_sufijos.items():
        mencion = ""
        if especialidad in ["Comunicaciones", "Computación", "Control"]:
            mencion = especialidad
            especialidad = "Ing. Electrónica"
            
        Materia.materias = []
        Materia.electivas = []
        Materia.agregar_electivas = False
        try:
            Logger.info(f"Cargando datos para {especialidad} {mencion}")
            materias_txt = join(RUTA_ARCHIVOS, f"materias_{archivo}.txt")
            materias_json = join(RUTA_DATOS, f"materias_{archivo}.json")

            if exists(materias_txt):
                with open(materias_txt, "r", encoding = "utf-8") as archivo_materias:
                    for linea in archivo_materias:
                        try:
                            eval(linea.replace("\n",""))
                        except Exception as e_eval:
                            Logger.error(f"Error evaluando línea de materia: {linea.strip()} - {e_eval}")
                            
            elif exists(materias_json):
                lista_materias = []
                with open(materias_json,"r", encoding = "utf-8") as archivo_materias:
                    lista_materias = json.load(archivo_materias)
                for materia in lista_materias:
                    Materia(materia["semestre"],
                            materia["codigo"],
                            materia["nombre"],
                            materia["ht"],
                            materia["ha"],
                            materia["hl"],
                            materia["uc"],
                            materia["nota"],
                            materia["aprobada"],
                            materia["disponible"],
                            materia["pre1"],
                            materia["pre2"],
                            materia["coreq"],
                            materia["inscrita"],
                            [Evaluacion(e["identificador"], e["nota"], e["ponderacion"], e["extra"]) for e in materia["evaluaciones"]],
                            materia["porcentual"],
                            materia["pre3"])

            else:
                Logger.warning(f"No se realizó la migración de datos para {especialidad} {mencion} - No hay archivo de datos")

            if exists(materias_txt) or exists(materias_json):
                lista_materias_archivo = Materia.materias[:]
                Logger.info("Cargando materias por defecto")
                lista_materias_defecto = cargar_datos_defecto(especialidad, mencion)
                Logger.info("Escribiendo electivas por defecto en archivo")
                electivas_diccionarios = []
                for electiva in Materia.electivas:
                    electivas_diccionarios.append(electiva.to_dict())
                with open(join(RUTA_DATOS, f"electivas_{archivo}.json"), "w", encoding = "utf-8") as archivo_electivas:
                    json.dump(electivas_diccionarios, archivo_electivas, indent = 4)
                Logger.info("Electivas por defecto escritas en archivo.")
                ruta_txt = f"{RUTA_ARCHIVOS}/electivas_{archivo}.txt"
                if exists(ruta_txt):
                    remove(ruta_txt)
                    Logger.debug("Se removió el txt de electivas")

                
                lista_electivas_defecto = Materia.electivas[:]
                dict_electivas_defecto = {materia.codigo : materia for materia in lista_electivas_defecto}
                
                lista_vieja = lista_materias_archivo + lista_electivas_defecto
                diccionario_viejo = {materia.codigo : materia for materia in lista_vieja}
                
                materias_migradas = []
                cod_electivas = ["Según Materia I","Según Materia II","Según Materia III","Según Materia IV"]
                entrenamiento_industrial = 0
                for materia_nueva in lista_materias_defecto:
                    materia_vieja = None
                    if materia_nueva.codigo in cod_electivas:
                        if especialidad == "Ing. Industrial":
                            indices_electivas = [49,55]
                        elif especialidad == "Ing. Eléctrica":
                            indices_electivas = [49,50,54,55]
                        elif especialidad == "Ing. Electrónica" and not mencion == "Comunicaciones" and version_entero <= 1410:
                            indices_electivas = [50,55,56]
                        elif especialidad == "Ing. Electrónica" and mencion == "Comunicaciones" and version_entero <= 1410:
                            indices_electivas = [54,55,56]
                        elif especialidad == "Ing. Electrónica" and not mencion == "Comunicaciones" and version_entero > 1410:
                            indices_electivas = [51,56,57]
                        elif especialidad == "Ing. Electrónica" and mencion == "Comunicaciones" and version_entero > 1410:
                            indices_electivas = [55,56,57]
                        elif especialidad == "Ing. Mecánica" and version_entero <= 1410:
                            indices_electivas = [51,52,53]
                        elif especialidad == "Ing. Mecánica" and version_entero == 1411:
                            indices_electivas = [45, 51]
                        elif especialidad == "Ing. Mecánica" and version_entero > 1411 and version_entero <= 1413:
                            indices_electivas = [51,52,53]
                        elif especialidad == "Ing. Mecánica" and version_entero > 1413:
                            indices_electivas = [52,53,54]
                        elif especialidad == "Ing. Metalúrgica":
                            indices_electivas = [49,54,55]
                        elif especialidad == "Ing. Química" and version_entero <= 1413:
                            indices_electivas = [50,54,55]
                        elif especialidad == "Ing. Química" and version_entero > 1413:
                            indices_electivas = [51,55,56]
                            
                        nro_electiva = cod_electivas.index(materia_nueva.codigo)
                        if nro_electiva <= len(indices_electivas) - 1:
                            materia_vieja = lista_materias_archivo[indices_electivas[nro_electiva] - entrenamiento_industrial]
                            if materia_vieja.semestre == "Opcional" and especialidad != "Ing. Mecánica":
                                entrenamiento_industrial = 1
                                if especialidad == "Ing. Electrónica" and not mencion == "Comunicaciones":
                                    indices_electivas = [51,56,57]
                                elif especialidad == "Ing. Electrónica" and mencion == "Comunicaciones":
                                    indices_electivas = [55,56,57]
                                elif especialidad == "Ing. Mecánica":
                                    indices_electivas = [52,53,54]
                                elif especialidad == "Ing. Química":
                                    indices_electivas = [51,55,56]
                                lista_materias_defecto.pop(indices_electivas[nro_electiva + 1])
                                
                            if materia_vieja.codigo not in cod_electivas:
                                if materia_vieja.codigo in dict_electivas_defecto.keys():
                                    materia_nueva = dict_electivas_defecto[materia_vieja.codigo]
                        
                    if materia_nueva.codigo in diccionario_viejo.keys():
                        if not materia_vieja:
                            materia_vieja = diccionario_viejo[materia_nueva.codigo]
                        materia_nueva.nota = materia_vieja.nota
                        materia_nueva.aprobada = materia_vieja.aprobada
                        materia_nueva.disponible = materia_vieja.disponible
                        materia_nueva.inscrita = materia_vieja.inscrita
                        materia_nueva.evaluaciones = materia_vieja.evaluaciones
                        materia_nueva.porcentual = materia_vieja.porcentual
                    
                    materias_migradas.append(materia_nueva)
                
                if materias_migradas:
                    Logger.info("Lista de materia migradas correcta. Iniciando copiado en archivo de materias")
                    lista_diccionarios = []
                    for materia_obj in materias_migradas:
                        lista_diccionarios.append(materia_obj.to_dict())
                    with open(join(RUTA_DATOS, f"materias_{archivo}.json"), "w", encoding = "utf-8") as archivo_materias:
                        json.dump(lista_diccionarios, archivo_materias, indent = 4)

                    ruta_txt = f"{RUTA_ARCHIVOS}/materias_{archivo}.txt"
                    if exists(ruta_txt):
                        remove(ruta_txt)
                        Logger.debug("Se removió el archivo txt viejo")

                    Logger.info("Finalizó la migración de datos para esta especialidad")
        except ValueError as e:
            Logger.error(f"Error en migración de datos {e}")
            
        