# Manual de Operação Docker - ONR MultiCartórios

Este manual descreve como configurar e rodar o sistema utilizando Docker e Docker Compose.

## 1. Pré-requisitos

Certifique-se de ter instalado em sua máquina:
*   **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux)
*   **Git** (para clonar o repositório)

## 2. Instalação e Configuração

### 2.1. Clonar o Repositório
Abra o seu terminal ou PowerShell e rode o comando:

```bash
git clone https://github.com/Feitosa98/IAgo_Cart.git
cd IAgo_Cart
```

### 2.2. Configuração de Ambiente

Antes de subir os containers, você precisa configurar as variáveis de ambiente.

1.  Na pasta raiz do projeto, localize o arquivo `.env.example`.
2.  Faça uma cópia deste arquivo e renomeie para `.env`.
    *   **Windows (PowerShell)**: `copy .env.example .env`
    *   **Linux/Mac**: `cp .env.example .env`
3.  Edite o arquivo `.env` com suas configurações (se necessário). As padrões geralmente funcionam para desenvolvimento local.

## 3. Comandos Principais

Abra o terminal na pasta do projeto para executar os comandos abaixo.

### Iniciar o Sistema
Para baixar as imagens, construir o projeto e iniciar os serviços:

```bash
docker-compose up --build
```
*   O sistema estará acessível em: `http://localhost:5000`
*   O terminal mostrará os logs de todos os serviços (web, worker, redis, db).

### Iniciar em Segundo Plano (Detached)
Para liberar o terminal enquanto o sistema roda:

```bash
docker-compose up -d
```

### Parar o Sistema
Para parar e remover os containers:

```bash
docker-compose down
```

### Ver Logs
Se rodou em modo detached (`-d`), use este comando para ver os logs:

```bash
# Todos os serviços
docker-compose logs -f

# Apenas o Worker (OCR)
docker-compose logs -f worker

# Apenas a Web
docker-compose logs -f web
```

## 4. Estrutura dos Serviços

*   **web**: A aplicação Flask principal.
*   **worker**: O processo Celery responsável por tarefas pesadas (OCR) em segundo plano.
*   **redis**: Banco de dados em memória usado como fila de mensagens para o Celery.
*   **db** (opcional/externo): Se configurado no docker-compose, é o banco PostgreSQL. *Nota: Atualmente o projeto pode estar apontando para um banco externo via .env.*

## 5. Solução de Problemas Comuns

**Erro: Porta em uso**
Se vir um erro como `Bind for 0.0.0.0:5000 failed: port is already allocated`:
1.  Verifique se não há outro processo rodando na porta 5000.
2.  Ou altere a porta no `docker-compose.yml` (ex: `5001:5000`).

**Erro de Conexão com Banco**
Verifique se as credenciais no arquivo `.env` estão corretas e se o container `web` consegue alcançar o host do banco de dados (especialmente se for um banco local fora do Docker, use `host.docker.internal` no host).

**Alterações no Código**
Em desenvolvimento, o volume está mapeado, então alterações no código (exceto instalação de novas libs) devem recarregar automaticamente o serviço `web`. Para o `worker`, pode ser necessário reiniciar para pegar novas tarefas:
```bash
docker-compose restart worker
```
