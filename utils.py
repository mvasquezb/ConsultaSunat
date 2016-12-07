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
        return json.CustomJSONEncoder


class DateJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if not (isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime)):
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
    def __init__(self, codigo, descripcion, revision=3):
        self.codigo= codigo
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
        tokens = [ token.strip() for token in ciiu_str.split('-') ]

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

class DeudaCoactiva(JSONEnabled):
    """
    Representa la deuda coactiva de un contribuyente
    """
    def __init__(self, monto, periodo_tributario, fecha_inicio, entidad_asociada):
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
            "periodo_tributario": datetime_encode.default(self.periodo_tributario),
            "fecha_inicio": datetime_encode.default(self.fecha_inicio),
            "entidad_asociada": self.entidad_asociada
        }
    
