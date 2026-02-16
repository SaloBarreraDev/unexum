class Evaluacion:
    
    def __init__(self, identificador, nota = 0, ponderacion = 25, extra = False):
        self.identificador = identificador
        self.nota = nota
        self.ponderacion = ponderacion
        self.extra = extra
        
    def __str__(self):
        return f"Evaluacion({(repr(self.identificador) if isinstance(self.identificador, str) else self.identificador)}, {(repr(self.nota) if isinstance(self.nota, str) else self.nota)}, {self.ponderacion}, {self.extra})"

    def to_dict(self):
        datos = {"identificador": self.identificador,
                "nota": self.nota,
                "ponderacion": self.ponderacion,
                "extra": self.extra}
        return datos

class Materia:
    materias = []
    electivas = []
    agregar_electivas = False
    
    def __init__(self, semestre, codigo, nombre, ht, ha, hl, uc, nota, aprobada, disponible, pre1, pre2, coreq, inscrita=False, evaluaciones = [], porcentual = False, pre3 = "''"):
        self.semestre = semestre
        self.codigo = codigo
        self.nombre = nombre
        self.ht=ht
        self.ha=ha
        self.hl=hl
        self.HT=ht+ha+hl
        self.uc = uc
        self.nota=nota
        self.aprobada=aprobada
        self.disponible=disponible
        self.pre1=pre1
        self.pre2=pre2
        self.coreq=coreq
        self.inscrita = inscrita
        self.evaluaciones = []
        for e in evaluaciones:
            if not isinstance(e,str):
                self.evaluaciones.append(e)
            else:
                self.evaluaciones.append(eval(e))
        self.porcentual = porcentual
        self.pre3 = pre3
        
        if Materia.agregar_electivas:
            Materia.electivas.append(self)
        else:
            Materia.materias.append(self)
        
        if self.pre1=="Aprobar todo el pensum":
            Materia.agregar_electivas = True
            
    def __str__(self):
        return f'Materia("{self.semestre}","{self.codigo}","{self.nombre}",{self.ht},{self.ha},{self.hl},{self.uc},{self.nota},{self.aprobada},{self.disponible},"{self.pre1}","{self.pre2}","{self.coreq}",{self.inscrita}, {self.evaluaciones}, {self.porcentual}, "{self.pre3}")'

    def __eq__(self,otra_materia):
        return self.codigo == otra_materia.codigo
    
    def to_dict(self):
        datos = {"semestre": self.semestre,
                "codigo": self.codigo,
                "nombre": self.nombre,
                "ht": self.ht,
                "ha": self.ha,
                "hl": self.hl,
                "uc": self.uc,
                "nota": self.nota,
                "aprobada": self.aprobada,
                "disponible": self.disponible,
                "pre1": self.pre1,
                "pre2": self.pre2,
                "coreq": self.coreq,
                "inscrita": self.inscrita,
                "evaluaciones": [evaluacion.to_dict() for evaluacion in self.evaluaciones],
                "porcentual": self.porcentual,
                "pre3": self.pre3}
        return datos