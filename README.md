# WebScraping BTPUCP

Proyecto que busca obtener convocatorias de trabajo de diferentes centros de empleo a través de la página web de cada uno.    

## Requerimientos
Este es un proyecto en Python 3 y hace uso de Cassandra como base de datos.

Además, se usan varias bibliotecas de Python. Se incluye el archivo `pip-requirements.txt`, de tal manera que instalarlas sea cuestión de ejecutar el comando:

    pip install -r pip-requirements.txt

Utilizar `pip` o `pip3` según corresponda para instalar las bibliotecas para Python 3.

## Configuración

### Global

Para notificar al usuario, se envía un correo al finalizar la ejecución del programa, donde se incluyen los resultados del web scraping.
El envío de este correo se puede configurar a través del archivo de `config`, que tiene los siguientes campos:

* Remitente:

        correo-envio@correo.com

* Contraseña de la cuenta de correo del remitente

        mi_contraseña

* Destinatario

        correo-recepcion@correo.com

* Archivo de reporte detallado

        salida-detalle.txt

* Lista de archivos de plantilla (buscados en Templates)

        centro1.txt
        centro2.txt

El formato de este archivo sigue las pautas expuestas en la siguiente sección.

### Por centro de empleo

Para ajustar el proceso de extracción a cada centro de empleo (y a sus sitios web), se hace uso de una plantilla donde se especifica dónde encontrar las funciones específicas de ese centro, dónde encontrar las convocatorias, etc.

Cada línea que contiene datos debe contener un indicador del dato que se va a definir y el dato encerrado en barras verticales: `|`.
Dependiendo del centro de empleo, algunos datos son opcionales. Por ejemplo, si la página no lo soporta.
Para definir un dato opcional, se agrega al inicio (entre las barras verticales) la palabra `optional`. 
Si un dato es opcional, no es necesario definirlo:

    Nombre del Valor:         |optional|

La estructura que se espera de las convocatorias (la que el programa sigue para obtener los datos) es esta:
Por cada área de desempeño, se busca por cada periodo de publicación, todas las convocatorias.

### Tipos de dato soportados

* Texto plano
* Números enteros
* URLs
* Listas (con el formato de python)
* Estructura html

#### Datos de texto plano

Los datos de texto plano tiene una restricción en que no pueden contener una barra vertical, pues esto impide el correcto procesamiento del archivo

#### Datos enteros

Estos datos son simples enteros, cualquier caracter no numérico invalida el dato

#### Datos url

Estos datos son evaluados usando la clase `django.core.validators.URLValidator`, por lo que debe ser las reglas impuestas por este. [Más información](https://docs.djangoproject.com/en/1.10/ref/validators/#urlvalidator)

#### Datos tipo lista

Estos datos son listas: valores separados por comas, encerrados entre corchetes `[]`:

    []
    ['']
    ['titulo', 'descripción']
    [3, 4]

#### Datos html

Los datos de tipo HTML (estructura donde encontrar ciertos datos) siguen algunas reglas:
El símbolo `->` define un nivel más profundo de jerarquía.
Cada etiqueta (nivel) tiene dos partes, la ocurrencia de la etiqueta que se busca:

    1 (primera)
    2 (segunda)
    * (todas las ocurrencias)

y el detalle de la etiqueta.
Este detalle consiste de tres partes: 

1. El nombre de la etiqueta:

        ul
        div
        * (todas las etiquetas)

2. Las características de la etiqueta en forma de diccionario:

        { class='job_box' }
        { class='textoTitulo', data-target='modal' }

3. El atributo que se desea obtener (vacío si se desea obtener el contenido de la etiqueta):

        href
        data-target

##### Ejemplo completo:

    1 ul\{"data-key":"areas"}\->* label\{}\->1 input\{}\value

Con este formato se obtiene el primer elemento `ul` (lista no ordenada) cuyo atributo `data-key` tenga el valor `areas`. 
En su contenido se buscan todos los label (diccionario vacío => sin restricción). 
Dentro de cada `label` se busca el primer `input` y se obtiene el valor de su atributo `value`.
Se obtiene la lista de estos valores.

### Ejemplo

Se muestra un ejemplo completo en el archivo `Templates/example.txt`

## Uso

Para ejecutar este programa, debe trasladarse al directorio `Code/View` y ejecutar el script `webScraping.py`.

    cd Code/View
    python webScraping.py

Utilizar `python` o `python3` según corresponda para ejecutar Python 3.

Se pueden ver los resultados en los archivos `View/summary.txt` y aquel definido en el archivo de configuración.