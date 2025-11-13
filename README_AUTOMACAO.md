⚙️ README – Automação com Docker + n8n
📦 1. Requisitos

Docker Desktop

n8n instalado via:

npm install -g n8n


ou via execução local:

npx n8n

🐳 2. Construir a imagem Docker do projeto

Na pasta raiz onde está o Dockerfile, execute:

docker build -t analisador:latest .

▶️ 3. Testar execução via Docker
docker run --rm -v "CAMINHO_DO_PROJETO:/app" -w /app analisador:latest python manage.py run_analyzer --dry-run


Exemplo:

docker run --rm -v "C:\Users\mathz\OneDrive\Área de Trabalho\Projeto BelMicro Final:/app" -w /app analisador:latest python manage.py run_analyzer --dry-run

🔄 4. Criar automação com n8n
➤ 4.1 Abrir o n8n
npx n8n


Painel disponível em:

http://localhost:5678

⚡ 4.2 Criar workflow automatico

Clique em Create Workflow

Adicione um nó Schedule Trigger

Configure para executar:

Every 1 hour
ou

Daily → 03:00

Adicione o nó Execute Command

Coloque o comando:

docker run --rm -v "CAMINHO:/app" -w /app analisador:latest python manage.py run_analyzer --dry-run


Clique em Execute Step para testar

Clique em Save

Clique em Activate

Agora o projeto rodará automaticamente no intervalo definido.

⏸ 5. Como pausar a automação
Método 1 — no n8n (recomendado)

Abra o workflow

Clique em Deactivate

Método 2 — parar o n8n inteiro

No terminal onde ele está rodando:

CTRL + C

▶️ 6. Como reativar a automação

Para abrir novamente:

npx n8n


Se o workflow estiver ativado, ele volta a rodar automaticamente.