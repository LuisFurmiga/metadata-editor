# Metadados

Aplicação local para visualizar, pesquisar, editar, remover e exportar metadados sem sobrescrever o arquivo enviado. O React conversa exclusivamente com a API FastAPI, que mantém uma cópia original e uma cópia de trabalho e delega toda leitura/escrita ao ExifTool.

> **Screenshot:** execute o projeto e abra `http://localhost:5173`. Uma captura da interface pode ser adicionada aqui na publicação.

## Recursos

- Upload por clique ou arrastar e soltar, com cancelamento e limite configurável (250 MB por padrão).
- Metadados agrupados, nomes amigáveis, busca local, filtros, favoritos e modo técnico. Para PDFs, campos graváveis comuns que ainda não existem (título, autor, assunto, palavras-chave, descrição e idioma) aparecem vazios com o selo **disponível**, permitindo criá-los.
- Edição em lote com revisão antes/depois, restauração e download da cópia modificada. A URL identifica a sessão temporária; ao voltar/cancelar ou concluir o download, original e cópia temporários são excluídos imediatamente do backend.
- Remoção de GPS, remoção total e remoção seletiva orientada pela análise de privacidade.
- Exportação JSON, CSV e TXT; temas claro, escuro e sistema persistidos localmente.
- Erros estruturados, health check e diagnóstico claro quando o ExifTool está ausente.

## Arquitetura

```text
frontend (React + TypeScript + Vite + Tailwind)
  └── REST /api
      └── FastAPI → MetadataService → ExifToolService → exiftool
                  → FileService (workspaces temporários)
                  → PrivacyService
```

Cada upload recebe um UUID imprevisível, refletido na URL local (`/files/{uuid}`). Por segurança do navegador, o caminho original no computador não é disponibilizado pela página; somente o nome do arquivo e a URL da sessão são mostrados. O backend sanitiza apenas o nome de exibição, grava o conteúdo em um diretório controlado (`~/.metadata-editor/sessions`) e nunca aceita caminhos do cliente. O `original` é imutável pela aplicação; todas as operações usam `working`. Sessões inativas são removidas na inicialização (24 horas por padrão).

## Requisitos

- Python 3.12 ou superior
- Node.js 20 ou superior e npm
- [ExifTool](https://exiftool.org/) disponível no `PATH`

### Instalar ExifTool

- **Windows 10/11:** baixe o executável oficial, renomeie `exiftool(-k).exe` para `exiftool.exe` e adicione a pasta ao `PATH`; ou use
```bash
winget install OliverBetz.ExifTool
```
quando disponível.
- **macOS:**
```bash
brew install exiftool
```
- **Ubuntu/Debian:**
```bash
sudo apt install libimage-exiftool-perl
```

Confirme com `exiftool -ver`.

## Instalação e execução

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

A documentação interativa fica em `http://localhost:8000/docs` e o diagnóstico em `http://localhost:8000/api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`. O proxy do Vite encaminha `/api` para a porta 8000.

### Execução conjunta

Após instalar as dependências, use `scripts/run-dev.ps1` no PowerShell (Windows) ou `./scripts/run-dev.sh` no Linux/macOS. O Vite abre o navegador automaticamente.

## Configuração

Variáveis usam o prefixo `METADATA_` e podem ser colocadas em `backend/.env`:

```dotenv
METADATA_MAX_UPLOAD_SIZE=262144000
METADATA_SESSION_TTL_SECONDS=86400
METADATA_EXIFTOOL_BINARY=exiftool
METADATA_WORKSPACE_ROOT=C:/Users/seu-usuario/.metadata-editor/sessions
```

As origens CORS são restritas a `localhost:5173` e `127.0.0.1:5173`. Ajuste `allowed_origins` antes de uma implantação diferente.

## Testes e qualidade

```bash
cd backend && pytest
cd frontend && npm run test
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

Os testes do backend simulam subprocessos: não modificam arquivos pessoais e não exigem ExifTool. Os testes cobrem execução segura, JSON inválido, escrita em lote, privacidade, sanitização e fluxo principal da API.

## Estrutura

- `backend/app/api/routes`: contratos HTTP finos.
- `backend/app/models`: modelos Pydantic.
- `backend/app/services`: arquivos, ExifTool, metadados e privacidade.
- `backend/tests`: testes unitários e de integração.
- `frontend/src/components`: elementos reutilizáveis.
- `frontend/src/pages`: experiência após upload.
- `frontend/src/services/api.ts`: único cliente HTTP.
- `frontend/src/contexts` e `hooks`: preferências locais.
- `scripts`: inicializadores multiplataforma.

## Solução de problemas

- **“ExifTool não encontrado”:** confirme `Get-Command exiftool` e `exiftool -ver` no PowerShell. Reinicie o backend se o `PATH` foi alterado depois que o terminal foi aberto. O backend também relê automaticamente o `PATH` de usuário e de máquina do Registro do Windows. Como alternativa, defina `METADATA_EXIFTOOL_BINARY=C:/caminho/exiftool.exe` em `backend/.env` e consulte `/api/health`; o campo `exiftool.executable` informa qual executável foi localizado.
- **Upload recusado:** verifique o limite `METADATA_MAX_UPLOAD_SIZE` e se o arquivo não está vazio.
- **Tag não editável:** informações calculadas ou do sistema são somente leitura; a possibilidade real também depende do formato suportado pelo ExifTool.
- **`npm install` retorna `ERESOLVE`:** confirme que o repositório está atualizado e que `@vitejs/plugin-react` está na versão `4.3.4`. Essa versão é compatível com o Vite 6 usado pelo projeto. Não use `--force` ou `--legacy-peer-deps`, pois essas opções apenas ocultam incompatibilidades. Se uma instalação anterior falhou, remova `node_modules` e execute `npm install` novamente.
- **`vite` não é reconhecido:** isso significa que `npm install` não terminou com sucesso. Corrija primeiro o erro de instalação; o executável local será chamado automaticamente por `npm run dev`.
- **Porta ocupada:** encerre o processo na porta 8000/5173 ou ajuste os comandos e o proxy.
- **Sessão perdida:** workspaces são temporários e expiram; faça download da cópia final.

## Segurança e evolução

Comandos são listas de argumentos, usam `shell=False` e validam tags; nomes jamais viram IDs ou caminhos arbitrários. Tracebacks não são retornados ao cliente. Antes de hospedagem pública, adicione autenticação, rate limiting, inspeção de conteúdo, política de retenção adequada e armazenamento isolado. A separação atual permite empacotamento futuro com Tauri ou consumo da API por outros clientes sem mover lógica de metadados para a interface.
