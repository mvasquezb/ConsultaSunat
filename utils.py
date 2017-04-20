import json
import datetime
from abc import ABCMeta, abstractmethod


class JSONEnabled(metaclass=ABCMeta):
    @abstractmethod
    def _json(self):
        """To override"""
        pass

    @property
    def json_class(self):
        return json.JSONEncoder


class DateJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if not (isinstance(obj, datetime.date) or
                isinstance(obj, datetime.datetime)):
            return json.dumps(obj, indent=2, ensure_ascii=False)
        return {
            "year": obj.year,
            "month": obj.month
        }


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, JSONEnabled):
            return json.dumps(obj, indent=2, ensure_ascii=False)
        return obj._json()


class CIIU(JSONEnabled):
    """
    Tipo CIIU que define una actividad economica de un contribyente
    """
    def __init__(self, codigo=0, descripcion="", revision=3):
        self.codigo = codigo
        self.descripcion = descripcion
        self.revision = revision

    def json_class(self):
        return CustomJSONEncoder

    def _json(self):
        return {
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "revision": self.revision
        }

    @classmethod
    def from_string(cls, ciiu_str):
        tokens = [token.strip() for token in ciiu_str.split('-')]

        desc = tokens[-1]
        codigo = tokens[-2]

        if codigo.startswith('CIIU'):
            codigo = codigo[len('CIIU'):]
        codigo = int(codigo)

        return cls(codigo, desc)

    def __eq__(self, other):
        return self.codigo == other.codigo

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return str(self._json())


class DeudaCoactiva(JSONEnabled):
    """
    Representa la deuda coactiva de un contribuyente
    """
    def __init__(self,
                 monto=0,
                 periodo_tributario=None,
                 fecha_inicio=None,
                 entidad_asociada=""):
        self.monto = monto
        self.periodo_tributario = periodo_tributario
        self.fecha_inicio = fecha_inicio
        self.entidad_asociada = entidad_asociada

    def json_class(self):
        return CustomJSONEncoder

    def _json(self):
        datetime_encode = DateJSONEncoder()
        return {
            "monto": self.monto,
            "periodo_tributario": datetime_encode.default(
                self.periodo_tributario
            ),
            "fecha_inicio": datetime_encode.default(self.fecha_inicio),
            "entidad_asociada": self.entidad_asociada
        }

    def __repr__(self):
        return str(self._json())


class OmisionTributaria(JSONEnabled):
    """
    Representa la omision tributaria de un contribuyente
    """
    def __init__(self, periodo_tributario=None, tributo=""):
        self.periodo_tributario = periodo_tributario
        self.tributo = tributo

    def json_class(self):
        return CustomJSONEncoder

    def _json(self):
        datetime_encode = DateJSONEncoder()
        return {
            "periodo_tributario": datetime_encode.default(
                self.periodo_tributario
            ),
            "tributo": self.tributo
        }

    def __repr__(self):
        return str(self._json())


class Contribuyente(JSONEnabled):
    def __init__(self,
                 ruc=None,
                 nombre='-',
                 nombre_comercial='-',
                 condicion='',
                 estado='',
                 deuda_coactiva=[],
                 omision_tributaria=[],
                 ciiu=[]):
        self.ruc = ruc
        self.nombre = nombre
        self.nombre_comercial = nombre_comercial
        self.condicion = condicion
        self.estado = estado
        self.deuda_coactiva = deuda_coactiva
        self.omision_tributaria = omision_tributaria
        self.ciiu = ciiu

    def json_class(self):
        return CustomJSONEncoder

    def _json(self):
        encoder = self.json_class()()
        return {
            "ruc": int(self.ruc),
            "nombre": self.nombre,
            "nombre_comercial": self.nombre_comercial,
            "condicion": self.condicion,
            "estado": self.estado,
            "deuda_coactiva": [
                encoder.default(dc) for dc in self.deuda_coactiva
            ],
            "omision_tributaria": [
                encoder.default(ot) for ot in self.omision_tributaria
            ],
            "ciiu": [encoder.default(ci) for ci in self.ciiu],
        }

    def __repr__(self):
        if self.ruc is None:
            return "Contribuyente inválido"
        return str(self._json())
