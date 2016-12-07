# Consulta SUNAT

Proyecto para realizar consultas a SUNAT por RUC sin pasar por el captcha.

## Requerimientos
Este es un proyecto en Python 3. Es necesario instalar tesseract y su data de
entrenamiento (solo inglés es necesario), así como PhantomJS (Deben estar en su PATH).    
Para instalarlos en Ubuntu y derivados:

    sudo apt-get install tesseract-ocr tesseract-data-eng phantomjs

Además se hace uso de varias bibliotecas de Python, que se pueden instalar con `pip`:

    pip install -r pip-requirements.txt

Usar `pip` o `pip3` según corresponda para instalar los paquetes para Python 3.

## Uso
Solo un parámetro es requerido para ejecutar la aplicación, una lista de RUCs 
que se van a consultar. Además, acepta parámetros opcionales, como el número de intentos
a ejecutar por RUC en la lista y el nombre del archivo donde guardar los resultados.
Más detalladamente:

|Parámetro|Descripción|
|---------|-----------|
|ruc|Lista de rucs a consultar (1 o más)|
|--retries retries|Límite de intentos de consulta por RUC (Default: `5`)|
|-o FILE<br>    --outfile FILE|Nombre del archivo donde guardar los resultados (Default: `sunat-results.txt`)|

Se puede hacer uso de esta aplicación de manera independiente:

    python app.py ruc1 ruc2 --retries 3 -o resultados.txt

Asimismo, se puede importar como módulo dentro de otro script de Python:

    import app
    data = app.main(['ruc1', 'ruc2', 'ruc3', '--retries', '5', '--outfile', 'resultados.txt'])
    print(data)


