
### uso:
+ crear venv
python3 -m venv venv 

+ instalar librerías
pip install -r requirements.txt 

+ procesar csv
python3 main.py ARCHIVO.csv 

+ chequear archivo exportado
cat somosmuchas-importacion.sql 

+ correr archivo en mysql de container
docker -i exec NOMBRE_DE_CONTAINER mysql -proot --default-character-set=utf8 causascomunes < somosmuchas-importacion.sql

notas: -i es importante sino no toma el pipe <. lo del character set es importante sino las tildes se rompen.
