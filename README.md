# Marginalia Books API

API REST para operação de uma biblioteca: cadastro de autores e exemplares, patronos, empréstimos e devoluções, fila de reserva por exemplar, notificações in-app para o patrono, relatórios para equipe e lembretes automáticos de vencimento (e-mail e/ou webhook).

- **Base da API:** `http://localhost:8000` (ambiente local padrão com Docker).
- **Contrato versionado:** `/api/v1`.
- **Documentação interativa:** [Swagger UI](http://localhost:8000/docs) e [OpenAPI JSON](http://localhost:8000/openapi.json) (versão **0.7.0**).

---

## 1. Instalação e execução

### 1.1 Pré-requisitos

- **Docker** e **Docker Compose**: para subir API, banco, Redis e workers.
- **Node.js 20+** e **npm**: apenas se for rodar o cliente web em [`frontend/`](frontend/).

### 1.2 Executar a aplicação (Docker)

Na raiz do repositório:

```bash
docker compose up --build
```

Com isso sobem PostgreSQL, Redis, a API (FastAPI), o worker e o agendador do Celery. Quando estiver pronto:

- **API:** http://localhost:8000  
- **Swagger:** http://localhost:8000/docs  

Na **primeira** subida com banco vazio, a API aplica as migrações e em seguida executa um *seed* de desenvolvimento (variável `SEED_DEV_DATA=true` no `docker-compose.yml`): ficam disponíveis um **administrador** (`admin@demo.marginalia.org` / `AdminSenha1`), um **patrono** de exemplo (`patron@demo.marginalia.org` / `PatronoSenha1`) e um pequeno catálogo (autores e exemplares). Os domínios são só para desenvolvimento (não enviam e-mail) e usam um host aceito pelo validador da API (`.local` é rejeitado). Se o admin já existir, o seed não altera o banco de novo. Para desligar esse preenchimento automático, remova `SEED_DEV_DATA` ou defina como vazio no serviço `api`.

**Interface web (opcional):** com a API no ar, em outro terminal:

```bash
cd frontend && npm install && npm run dev
```

O Vite costuma servir em http://localhost:5173.

### 1.3 Variáveis de ambiente (`backend/.env`)

O arquivo **[`backend/.env.example`](backend/.env.example)** lista variáveis suportadas. Copie para `backend/.env` e ajuste quando precisar.

Em resumo:

- **`DATABASE_URL`**, **`REDIS_URL`**, **`JWT_SECRET_KEY`**, **`ACCESS_TOKEN_EXPIRE_MINUTES`**, **`JWT_ALGORITHM`**: autenticação e conexões.
- **`CELERY_BROKER_URL`**: fila do Celery (no Compose dos workers costuma ser `redis://redis:6379/1`).
- **Worker Celery e Redis:** além do broker (`CELERY_BROKER_URL`), o **worker** usa **`REDIS_URL`** para o mesmo Redis da API (índice **0**, cache e invalidação de catálogo). Sem `REDIS_URL` apontando para a instância correta (em Docker: `redis://redis:6379/0`, não `localhost`), tarefas que alteram dados e invalidam cache podem falhar antes do `commit`, por exemplo expiração de *hold* de reserva e lembretes que tocam o catálogo. O **`docker-compose.yml`** do repositório já define `REDIS_URL` no serviço `celery_worker`; em deploy próprio, replique **Postgres + `REDIS_URL` + broker** no ambiente do worker.
- **`SMTP_*`**: se preenchido, o worker pode enviar e-mail de lembrete; sem `SMTP_HOST`, o envio por e-mail é ignorado (a API continua funcionando).
- **`LOAN_REMINDER_WEBHOOK_URL`**: se definido, o worker também pode disparar um POST JSON por lembrete.
- **`CORS_ORIGINS`**: origens permitidas (lista separada por vírgula); vazio desativa o middleware CORS (ver `backend/app/core/config.py`).

O Compose **não** versiona segredos: use `backend/.env` para Mailtrap, produção, etc.

### 1.4 Testes automatizados (backend)

Suíte **pytest** sobre o contrato HTTP da API, com persistência em **SQLite em memória** (sem depender do Postgres do Compose). Cobre rotas públicas e autenticadas, regras de empréstimo e devolução, permissões de administrador no catálogo e fluxos de reserva.

```bash
cd backend && pip install -r requirements.txt && pytest
```

Cenários e documentação da pasta de testes: **[`backend/tests/README.md`](backend/tests/README.md)**.

---

## 2. Decisões arquiteturais

### 2.1 Objetivo do desenho

O sistema separa **interface HTTP**, **regras de negócio**, **persistência** e **infraestrutura** (configuração, logging, limites de taxa, integração com Redis e filas). Isso facilita evoluir o contrato em `/api/v1`, testar serviços e trocar detalhes de infraestrutura sem espalhar lógica pelas rotas.

### 2.2 Stack

| Camada | Tecnologia |
| ------ | ---------- |
| HTTP / contrato | **FastAPI**, **Pydantic v2** (validação e geração OpenAPI). |
| Banco | **PostgreSQL**, **SQLAlchemy 2** com sessão **assíncrona**. |
| Migrações | **Alembic**. |
| Cache | **Redis** (invalidação quando autores, livros, empréstimos ou reservas mudam). |
| Filas / agendamento | **Celery** + **Redis** como broker; **Celery Beat** em UTC. |
| Autenticação | **JWT** (senhas com **bcrypt**). |
| Limitação de abuso | **slowapi** nas rotas públicas de registro e login (por IP). |
| Logs | **structlog** (JSON ou console), com **correlation id** por requisição (`X-Correlation-ID`). |

### 2.3 Organização do código (`backend/app/`)

- **`api/`**: Rotas: `v1` (auth, usuários, autores, livros, empréstimos, reservas, notificações, relatórios, painel admin) e **health** fora do prefixo versionado.
- **`services/`**: Regras de empréstimo, multa, reserva, cache, relatórios, lembretes, notificações, etc.
- **`models/`**: Tabelas ORM.
- **`schemas/`**: Modelos Pydantic de entrada/saída.
- **`core/`**: Configuração, sessão de banco, segurança, middleware, constantes de negócio.

### 2.4 Modelo de dados e regras de negócio

Os valores abaixo vêm de [`backend/app/core/constants.py`](backend/app/core/constants.py):

- **Exemplar:** cada registro em `books` representa **um** exemplar. Há no máximo **um** empréstimo ativo por exemplar.
- **Prazo padrão do empréstimo:** **14 dias** a partir da data de empréstimo.
- **Multa:** **R$ 2,00** por dia civil de atraso após o vencimento; devolução no vencimento ou antes gera multa zero.
- **Limite de empréstimos ativos por patrono:** **3**.
- **Reservas pendentes por patrono:** até **3** (fila por exemplar; ordem **FIFO**). Reserva só é aceita enquanto o exemplar está emprestado.
- **Renovação:** até **1** vez por empréstimo; acrescenta **4 dias** ao `due_at` atual; só nos **primeiros 7 dias corridos** do empréstimo; não permitida se o empréstimo estiver atrasado ou houver fila de reserva para aquele exemplar.
- **Após devolução com fila:** o primeiro da fila ganha uma janela para emprestar; se o patrono estiver no limite de empréstimos, aplica-se um *hold* com TTL definido em `constants.py` (em desenvolvimento costuma ser curto em minutos; comentários no arquivo indicam ajuste para horas em produção). Tarefa periódica do Celery expira *holds* vencidos.

Lembretes de **“vence nas próximas 48 horas”** rodam **no worker** (varredura horária em UTC), com idempotência em `loan_reminder_logs`, e podem acionar e-mail e/ou webhook conforme configuração.

### 2.5 Autenticação e perfis

- **Público (sem JWT):** `GET /health`, `GET /health/live`, `GET /health/ready`, documentação OpenAPI, `POST /api/v1/auth/register`, `POST /api/v1/auth/login`.
- **Autenticado:** demais rotas em `/api/v1/*` com `Authorization: Bearer <token>`.
- **Administrador (`is_admin`):** criação/edição/exclusão de autores e livros; listagem global de empréstimos (`GET /api/v1/loans`); exclusão de usuários sem empréstimos; relatórios CSV/PDF; painel `GET /api/v1/admin/dashboard`. Não existe endpoint HTTP para conceder admin; em ambientes controlados isso é feito diretamente no banco (ver exemplos na seção 4).

### 2.6 Saúde e disponibilidade

- **`GET /health`** e **`GET /health/live`:** liveness —> o processo está respondendo.
- **`GET /health/ready`:** readiness —> PostgreSQL obrigatório (HTTP 503 se o banco não responder); Redis é opcional para a API (se o Redis configurado falhar, a resposta pode ser HTTP 200 com status `degraded`).

---

## 3. Funcionalidades implementadas

### 3.1 Autenticação

- Registro de patrono com senha (`POST /api/v1/auth/register`).
- Login e emissão de JWT (`POST /api/v1/auth/login`).
- Limite de requisições por IP nas rotas de auth.

### 3.2 Usuários

- Listagem paginada com filtro opcional por nome/e-mail (**admin**).
- Consulta e atualização de perfil (próprio usuário ou **admin**).
- Exclusão de usuário sem empréstimos (**admin**).
- Histórico de empréstimos do patrono com filtro por status (`GET /api/v1/users/{id}/loans` próprio ou **admin**).

### 3.3 Catálogo

- CRUD de autores (leitura autenticada; escrita **admin**).
- CRUD de livros vinculados a autor (escrita **admin**); listagem e detalhe com flag de disponibilidade; busca por título ou nome do autor (`q` ou `search`).
- Endpoint de disponibilidade do exemplar (`GET /api/v1/books/{id}/availability`).

### 3.4 Empréstimos

- Novo empréstimo respeitando limite por patrono, disponibilidade do exemplar e regras da fila de reserva (`POST /api/v1/loans`). Patrono só pode criar para si; **admin** pode informar outro `user_id`.
- Devolução com cálculo de multa (`POST /api/v1/loans/{id}/return`). A multa por atraso é **computada só na devolução** e gravada em `fine_amount`; não há cobrança automática nem notificação dedicada só de “multa”. O patrono vê o valor na **resposta da devolução** e no **histórico de empréstimos** na interface (empréstimos já devolvidos com multa).
- Em empréstimos **ainda ativos**, a API expõe **`projected_fine_brl`** (estimativa se devolver naquele momento, mesma regra de dias corridos); o frontend mostra em **Meus empréstimos** e na página do livro quando há valor positivo.
- Renovação (`POST /api/v1/loans/{id}/renew`) conforme regras da seção 2.4.
- Listagem **global** de empréstimos com filtro `active` / `overdue` / `all` **somente admin** (`GET /api/v1/loans`). Patronos usam `GET /api/v1/users/{id}/loans` para o próprio histórico.

### 3.5 Reservas (fila por exemplar)

- Entrar na fila, listar fila por livro ou listar reservas pendentes do usuário, cancelar reserva (`/api/v1/reservations`).

### 3.6 Notificações (in-app)

- Listar notificações recentes, contagem de não lidas, marcar uma ou todas como lidas (`/api/v1/notifications`).
- Incluem eventos de **reserva** (fila, *hold*, expiração) e **lembretes de empréstimo** (in-app; e-mail e webhook só onde configurados): janela **48 h** antes do vencimento; **no dia do vencimento (UTC)** aviso sobre cobrança por atraso; **cada dia em atraso** (multa acumulada estimada, mesma regra da devolução).

### 3.7 Operação e staff

- **Painel admin (JSON):** resumo agregado para período (`GET /api/v1/admin/dashboard`) apenas **admin**.
- **Relatórios exportáveis (CSV ou PDF):** empréstimos no período, multas, livros mais emprestados, inventário (`GET /api/v1/reports/loans`, `/fines`, `/top-books`, `/inventory`) apenas **admin**. Período padrão: últimos 30 dias UTC quando datas omitidas.

### 3.8 Infraestrutura transversal

- Paginação padrão (`page`, `page_size`) nas listas que suportam.
- Cache de leitura do catálogo com invalidação coerente.
- Logs estruturados e correlation id.
- Tarefas agendadas: lembretes de vencimento; expiração de reservas em *hold*.

---

## 4. Exemplos de uso da API

Os exemplos usam `curl` e `jq`. Ajuste host, e-mail e senha.

### 4.1 Registrar, autenticar e montar o header

```bash
BASE=http://localhost:8000/api/v1

curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria Silva","email":"maria@example.com","password":"senhaSegura12"}'

TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"maria@example.com","password":"senhaSegura12"}' | jq -r .access_token)

AUTH="Authorization: Bearer $TOKEN"
```

### 4.2 Conceder perfil de administrador (operação no banco)

Com **`docker compose up`**, o usuário admin de demonstração já nasce com `is_admin` (veja o parágrafo sobre *seed* em **§1.2**). Não há rota HTTP para promover usuário; para **outros** e-mails criados via registro, use SQL (ajuste o e-mail):

```sql
UPDATE users SET is_admin = true WHERE email = 'maria@example.com';
```

Em geral o token JWT já emitido continua válido; se alguma permissão falhar, faça login novamente.

### 4.3 Criar autor e livro (admin)

```bash
AUTHOR_ID=$(curl -s -X POST "$BASE/authors" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{"name":"Clarice Lispector","bio":"Escritora brasileira."}' | jq -r .id)

curl -s -X POST "$BASE/books" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d "{\"title\":\"A hora da estrela\",\"author_id\":$AUTHOR_ID,\"publication_year\":1977}"
```

### 4.4 Emprestar e devolver

```bash
USER_ID=$(curl -s -H "$AUTH" "$BASE/users?page_size=1" | jq -r '.items[0].id')
BOOK_ID=$(curl -s -H "$AUTH" "$BASE/books?page_size=1" | jq -r '.items[0].id')

LOAN_ID=$(curl -s -X POST "$BASE/loans" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d "{\"user_id\":$USER_ID,\"book_id\":$BOOK_ID}" | jq -r .id)

curl -s -X POST "$BASE/loans/$LOAN_ID/return" -H "$AUTH"
```

### 4.5 Consultas úteis

```bash
# Empréstimos do patrono (substitua USER_ID)
curl -s -H "$AUTH" "$BASE/users/$USER_ID/loans?status=all"

# Lista global de empréstimos requer admin
curl -s -H "$AUTH" "$BASE/loans?filter=active"

# Disponibilidade de um exemplar
curl -s -H "$AUTH" "$BASE/books/$BOOK_ID/availability"
```

### 4.6 Health checks (sem token)

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/ready
```

### 4.7 Ajustes manuais no banco (Docker / testes)

Com os containers no ar, abra o Postgres do projeto:

```bash
docker compose exec db psql -U library -d library
```

Exemplos úteis para testar **multa** (vencimento no passado em empréstimo ainda ativo) ou **lembrete de 48 h** (ajuste `id` do empréstimo):

```sql
-- Empréstimo ativo com vencimento ontem (ao devolver, multa = dias em atraso × R$ 2,00)
UPDATE loans
SET due_at = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - interval '1 day'
WHERE id = 1 AND returned_at IS NULL;

-- Vence nas próximas horas (entra na varredura horária de lembrete + notificação in-app)
UPDATE loans
SET due_at = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') + interval '12 hours'
WHERE id = 1 AND returned_at IS NULL;
```

Encerre com `\q`. Rode **`alembic upgrade head`** após puxar migrações novas. A multa só existe após **`POST .../return`**; até lá o exemplar pode aparecer como atrasado na UI.

### 4.8 Relatório em PDF (admin)

```bash
curl -s -L -H "$AUTH" -o inventario.pdf \
  "http://localhost:8000/api/v1/reports/inventory?format=pdf"
```

Para todos os campos obrigatórios, códigos de erro e parâmetros opcionais, use o **Swagger em `/docs`** como referência principal.

O contrato **OpenAPI 3** em **`/openapi.json`** pode ser consumido por clientes HTTP (Postman, Insomnia, geradores de SDK, etc.) com a API em execução.

---

## 5. Postman

Na pasta [`postman/`](postman/) há:

- **`Marginalia.postman_collection.json`**: requisições geradas a partir do OpenAPI da API.
- **`Marginalia.local.postman_environment.json`**: variáveis para uso em máquina local (sem segredos versionados).

**Recomenda-se o Postman Desktop** ao testar `localhost` (importação por URL ou envio de requisições costuma ser mais estável que só o Postman no navegador).

### Passos para teste

1. Subir a API com Docker (seção 1.2) e conferir http://localhost:8000/docs  
2. No Postman: **Import** → arrastar ou selecionar **`postman/Marginalia.postman_collection.json`** e **`postman/Marginalia.local.postman_environment.json`**.  
3. No canto superior direito, selecionar o ambiente **Marginalia Local**.  
4. Variáveis do ambiente:
   - **`baseUrl`:** `http://localhost:8000` (já vem preenchido; ajuste só se a API rodar em outro host/porta).
   - **`bearerToken`:** deixe vazio até o login. A collection usa **`{{bearerToken}}`** no esquema Bearer das rotas protegidas (não há variável `token` neste pacote).
5. **Autenticação:** envie **`POST /api/v1/auth/register`** (se precisar de usuário) e depois **`POST /api/v1/auth/login`** com e-mail e senha no body JSON. Na resposta, copie o valor de **`access_token`**.  
6. **Environments** → **Marginalia Local** → em **`bearerToken`**, cole só o token (sem o prefixo `Bearer `) → **Save**.  
7. Testar rotas protegidas (ex.: **`GET /api/v1/books`**). Se receber **401**, o token expirou ou não foi salvo; repita o login e atualize **`bearerToken`**.

**Rotas só para administrador** (`GET /api/v1/loans`, relatórios em `/api/v1/reports/*`, escrita no catálogo, etc.): não há endpoint para promover usuário. Com a API e o banco locais, use cliente SQL (ex.: `docker compose exec db psql -U library -d library`) e execute `UPDATE users SET is_admin = true WHERE email = '...';` Depois, se necessário, faça login de novo e atualize **`bearerToken`**.

---

## 6. Estrutura do repositório (referência)

```
marginalia-api/
├── docker-compose.yml
├── README.md
├── postman/                
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
└── frontend/
```

O código-fonte da API e as rotas expostas são a fonte da verdade; este README resume instalação, arquitetura, escopo funcional e exemplos.