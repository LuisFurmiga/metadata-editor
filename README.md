# Metadados

Aplicação web para **visualizar, pesquisar, editar, remover e exportar metadados de arquivos** sem sobrescrever o arquivo original.

O frontend utiliza **React + TypeScript + Vite + Tailwind**, enquanto o backend utiliza **FastAPI** e delega a leitura e escrita dos metadados ao **ExifTool**.

## Recursos

- Upload por clique ou arrastar e soltar, com limite configurável de **250 MB** por padrão.
- Visualização de metadados agrupados, busca, filtros, favoritos e modo técnico.
- Criação e edição de campos graváveis em formatos compatíveis, incluindo campos comuns de PDF.
- Edição em lote com revisão antes/depois e restauração.
- Preservação do arquivo original: alterações são realizadas apenas em uma cópia de trabalho.
- Remoção de GPS, remoção total e remoção seletiva orientada pela análise de privacidade.
- Exportação em **JSON, CSV e TXT**.
- Temas claro, escuro e sistema.
- Health check da API e diagnóstico do ExifTool.
- Execução simplificada com **Docker Compose**.

## Arquitetura

```text
Navegador
   │
   ▼
Frontend (React + TypeScript)
   │
   └── /api
        │
        ▼
     FastAPI
        │
        ├── MetadataService ──> ExifToolService ──> ExifTool
        ├── FileService ──────> workspaces temporários
        └── PrivacyService
```

Cada upload recebe um UUID imprevisível, refletido na URL local (`/files/{uuid}`). O backend mantém uma cópia `original` imutável e uma cópia `working`, utilizada nas operações de edição.

Sessões inativas são removidas automaticamente após **24 horas por padrão**.

---

## Início rápido com Docker

> **Recomendado para quem deseja apenas executar a aplicação.**
>
> Usando Docker, não é necessário instalar Python, Node.js, npm ou ExifTool manualmente no computador. Essas dependências ficam dentro dos contêineres.

### Requisitos

- **Windows/macOS:** Docker Desktop.
- **Linux:** Docker Engine + Docker Compose Plugin.

No Windows, o Docker Desktop pode ser obtido em:

https://www.docker.com/products/docker-desktop/

Confirme a instalação:

```powershell
docker --version
docker compose version
```

Opcionalmente, teste o Docker Engine:

```powershell
docker run hello-world
```

### Subir a aplicação

Na raiz do projeto, onde está o arquivo `compose.yaml`:

```bash
docker compose up --build
```

Depois, abra:

```text
http://localhost:8080
```

Health check da API:

```text
http://localhost:8080/api/health
```

Na primeira execução, o Docker precisará baixar as imagens base e construir o frontend e o backend.

### Executar em segundo plano

```bash
docker compose up -d --build
```

Verifique os serviços:

```bash
docker compose ps
```

### Ver logs

Todos os serviços:

```bash
docker compose logs -f
```

Somente o backend:

```bash
docker compose logs -f backend
```

Somente o frontend:

```bash
docker compose logs -f frontend
```

### Parar a aplicação

```bash
docker compose down
```

### Reconstruir após alterações

```bash
docker compose up --build
```

Para reconstruir sem cache:

```bash
docker compose build --no-cache
docker compose up
```

### Verificar o ExifTool no contêiner

O backend Docker já inclui o ExifTool:

```bash
docker compose exec backend exiftool -ver
```

---

## Como o Docker está organizado

O `compose.yaml` cria dois serviços:

```text
┌────────────────────────────────┐
│           Navegador            │
│        localhost:8080          │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│           frontend             │
│ React compilado + Nginx        │
│ porta interna: 8080            │
└───────────────┬────────────────┘
                │ /api
                ▼
┌────────────────────────────────┐
│            backend             │
│ FastAPI + Python + ExifTool    │
│ porta interna: 8000            │
└────────────────────────────────┘
```

O backend não é exposto diretamente para o host. O Nginx do frontend encaminha as requisições `/api` pela rede interna do Docker.

### Armazenamento temporário

No Docker, os arquivos de cada sessão ficam em um `tmpfs` privado do contêiner do backend:

```text
/tmp/metadata-editor
```

Esse armazenamento:

- não é persistido no host;
- está limitado a **1 GiB**;
- é removido quando o contêiner é removido;
- também é limpo pelo fluxo normal de conclusão/cancelamento da sessão.

---

## Configuração do Docker

É possível definir configurações em um arquivo `.env` na raiz do projeto, ao lado de `compose.yaml`:

```dotenv
APP_PORT=8080
METADATA_MAX_UPLOAD_SIZE=262144000
METADATA_SESSION_TTL_SECONDS=86400
```

| Variável | Padrão | Descrição |
| --- | ---: | --- |
| `APP_PORT` | `8080` | Porta usada para acessar a aplicação no host. |
| `METADATA_MAX_UPLOAD_SIZE` | `262144000` | Limite máximo de upload em bytes (250 MB). |
| `METADATA_SESSION_TTL_SECONDS` | `86400` | Tempo de vida da sessão em segundos (24 h). |

Após alterar o `.env`:

```bash
docker compose up -d --build
```

---

## Desenvolvimento sem Docker

Para desenvolvimento com hot reload, execute frontend e backend diretamente no sistema operacional.

### Requisitos

- Python **3.12+**
- Node.js **20+**
- npm **10+**
- ExifTool disponível no `PATH`

### ExifTool

#### Windows 10/11

Baixe o executável em:

https://exiftool.org/

Renomeie `exiftool(-k).exe` para `exiftool.exe` e adicione a pasta ao `PATH`.

Quando disponível, também é possível usar:

```powershell
winget install OliverBetz.ExifTool
```

Confirme:

```powershell
exiftool -ver
```

#### macOS

```bash
brew install exiftool
```

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install libimage-exiftool-perl
```

### Backend

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências e inicie a API:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Endpoints:

```text
API:          http://localhost:8000
Documentação: http://localhost:8000/docs
Health check: http://localhost:8000/api/health
```

### Frontend

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Abra:

```text
http://localhost:5173
```

O proxy do Vite encaminha `/api` para `localhost:8000`.

### Execução conjunta

Depois de instalar as dependências:

Windows PowerShell:

```powershell
.\scripts\run-dev.ps1
```

Linux/macOS:

```bash
./scripts/run-dev.sh
```

---

## Configuração do backend

Na execução sem Docker, as variáveis podem ser definidas em `backend/.env`:

```dotenv
METADATA_MAX_UPLOAD_SIZE=262144000
METADATA_SESSION_TTL_SECONDS=86400
METADATA_EXIFTOOL_BINARY=exiftool
METADATA_WORKSPACE_ROOT=C:/Users/seu-usuario/.metadata-editor/sessions
```

As origens CORS permitidas por padrão são:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Para implantar em outro domínio, revise `allowed_origins` antes da publicação.

---

## Testes e qualidade

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run test
npm run lint
npm run typecheck
npm run build
```

Os testes do backend simulam subprocessos, não modificam arquivos pessoais e não exigem ExifTool instalado.

---

## Estrutura do projeto

```text
metadados-info/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── scripts/
│   ├── run-dev.ps1
│   └── run-dev.sh
├── compose.yaml
└── README.md
```

- `backend/app/api/routes`: rotas HTTP.
- `backend/app/models`: modelos Pydantic.
- `backend/app/services`: arquivos, ExifTool, metadados e privacidade.
- `backend/tests`: testes unitários e de integração.
- `frontend/src/components`: componentes reutilizáveis.
- `frontend/src/pages`: páginas da aplicação.
- `frontend/src/services/api.ts`: cliente HTTP.
- `frontend/src/contexts` e `frontend/src/hooks`: preferências e estado local.
- `scripts`: inicializadores para desenvolvimento.

---

## Solução de problemas

### `docker` não é reconhecido no PowerShell

Confirme que o Docker Desktop foi instalado e feche/reabra o terminal:

```powershell
docker --version
docker compose version
```

### Docker instalado, mas os serviços não iniciam

Confirme que o Docker Desktop está aberto e verifique:

```bash
docker compose ps
docker compose logs
```

### Porta 8080 ocupada

Crie ou altere o `.env` da raiz:

```dotenv
APP_PORT=8081
```

Depois:

```bash
docker compose up -d
```

A aplicação ficará disponível em `http://localhost:8081`.

### ExifTool não encontrado na execução local

```powershell
Get-Command exiftool
exiftool -ver
```

Se necessário, configure `backend/.env`:

```dotenv
METADATA_EXIFTOOL_BINARY=C:/caminho/exiftool.exe
```

No Docker, o ExifTool já está incluído no backend.

### Upload recusado

Confira `METADATA_MAX_UPLOAD_SIZE` e confirme que o arquivo não está vazio.

### Tag não editável

Alguns metadados são calculados ou somente leitura. A possibilidade de escrita também depende do suporte do ExifTool para o formato utilizado.

### `npm ci` apresenta erro

Confirme as versões:

```bash
node --version
npm --version
```

O projeto requer Node.js 20+ e npm 10+.

Evite `--force` e `--legacy-peer-deps`, pois essas opções podem apenas ocultar incompatibilidades.

### `vite` não é reconhecido

Reinstale as dependências:

```bash
cd frontend
npm ci
npm run dev
```

### Erro de tipos entre Vite e Vitest no build Docker

```bash
docker compose build --no-cache frontend
docker compose up
```

### Sessão perdida

As sessões são temporárias e expiram. Faça o download da cópia final antes de encerrar a sessão.

---

## Segurança

A aplicação evita modificar diretamente o arquivo original:

- comandos externos são executados como listas de argumentos;
- `shell=False` é utilizado no backend;
- tags são validadas;
- nomes de arquivos não viram IDs ou caminhos arbitrários;
- original e cópia de trabalho permanecem separados;
- tracebacks não são retornados ao cliente;
- no Docker, os arquivos temporários ficam em `tmpfs`;
- os contêineres utilizam `no-new-privileges`;
- o backend Docker executa com usuário não privilegiado.

Antes de disponibilizar a aplicação publicamente, recomenda-se adicionar autenticação, rate limiting, inspeção de conteúdo, política de retenção adequada e armazenamento isolado.
