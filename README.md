# Sistema Indicador Real - ONR MultiCartórios

Sistema web para gestão de imóveis e integração com o ONR (Operador Nacional do Registro Eletrônico de Imóveis), suportando múltiplos cartórios (Multi-Tenant).

## 🚀 Funcionalidades

- **Multi-Tenant:** Isolamento de dados por cartório via Schemas PostgreSQL.
- **OCR Inteligente:** Extração automática de dados de matrículas (PDF/Imagens).
- **IA (IAGO):** Aprendizado de padrões para melhoria contínua da extração.
- **Exportação ONR:** Geração de arquivos XML/JSON no padrão exigido.
- **Gestão de Usuários:** Controle de acesso com níveis (Admin, Supervisor, Colaborador).

## 🛠️ Instalação

### Pré-requisitos
- Python 3.10+
- PostgreSQL
- Tesseract OCR (para funcionalidade de OCR)
- Poppler (para processamento de PDF)

### Passos

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/projeto-onr-multicartorios.git
   cd projeto-onr-multicartorios
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   - Copie o arquivo de exemplo:
     ```bash
     cp .env.example .env
     ```
   - Edite o arquivo `.env` com suas credenciais do banco de dados e chaves de segurança.

## ⚙️ Configuração (.env)

O sistema exige as seguintes variáveis no arquivo `.env`:

```ini
IAGO_DB_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=sua_chave_secreta_aqui
```

## ▶️ Executando

Para iniciar o servidor de desenvolvimento:

```bash
python imoveis_web_multi.py
```

O sistema estará acessível em `http://localhost:5000`.

## 🏥 Monitoramento

O sistema possui um endpoint de verificação de saúde:

- **GET /health**: Retorna status da aplicação e conexão com banco de dados.
  ```json
  {
    "status": "ok",
    "database": "connected",
    "timestamp": "2024-01-20T12:00:00+00:00"
  }
  ```

## 📂 Estrutura do Projeto

- `imoveis_web_multi.py`: Aplicação principal Flask.
- `db_manager.py`: Gerenciamento de conexões com banco de dados.
- `iago.py`: Lógica de Inteligência Artificial e padrões.
- `email_service.py`: Serviço de envio de notificações.
- `templates/`: Arquivos HTML.
- `static/`: Arquivos CSS, JS e imagens.

## 🤝 Contribuição

1. Faça um Fork do projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
