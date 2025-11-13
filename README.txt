/*Iniciar servidor*/
python manage.py runserver
//-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --//

/*Iniciar redis*/
#No diretorio do arquivo
cd Redis-x64-3.0.504
.\redis-server.exe
redis-cli.exe -h 127.0.0.1 -p 6379 ping
.\redis-cli.exe

//-- -- -- -- -- -- -- -- -- -- -- -- -- -- --//

/*Inicia o ollama, model: gemma:2b*/
ollama run mistral
$env:OLLAMA_HOST = "127.0.0.1:11435"
ollama serve
//-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --//

/*Dependencias a instalar*/
#instalar o python
pip install playwright
playwright install
get-pip.py
py -m pip install Django==5.2.5
pip install redis
pip install pandas 
pip install pyarrow
pip install mysqlclient
pip install psycopg2-binary
pip install groq
//-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --//

/*Banco de dados*/
python manage.py makemigrations 
python manage.py makemigrations siteweb
python manage.py migrate
//-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --//

O banco de dados utilizado foi o postgree
 cd "C:\Program Files\PostgreSQL\17\bin"
//-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --//

.\psql -U postgres -d trabamazon;
senha: 123



