# Testes automatizados do backend (pytest)

Este documento descreve os cenários de teste.

## Como rodar

Na pasta `backend/` (com o ambiente virtual ativado, se você usar um):

```bash
pip install -r requirements.txt
pytest
```

Opções úteis:

- `pytest -v` — lista cada teste
- `pytest tests/test_auth.py` — só um arquivo
- `pytest -k "loan"` — testes cujo nome contém `loan`

## Ambiente dos testes

Os testes usam **SQLite em memória**, não o PostgreSQL do Docker. Assim qualquer máquina roda a suíte sem subir banco. A API real continua pensada para Postgres; aqui validamos **regras de negócio e HTTP**.

Redis **não** é obrigatório: nas requisições o cache aparece como indisponível, o que é aceitável para estes cenários.

---

## 1. Saúde da API

| Cenário | O que é verificado |
| -------- | ------------------ |
| **Liveness** | `GET /health` responde que o processo está no ar. |
| **Readiness** | `GET /health/ready` consegue falar com o banco de testes e responde com sucesso. |

---

## 2. Autenticação (registro e login)

| Cenário | O que é verificado |
| -------- | ------------------ |
| **Novo patrono** | Registro com nome, e-mail e senha válidos cria usuário e retorna **201**. |
| **Login correto** | Mesmo e-mail e senha retornam um **JWT** (`access_token`). |
| **E-mail duplicado** | Segundo registro com o mesmo e-mail retorna **409** (conflito). |
| **Senha errada** | Login com senha incorreta retorna **401**, sem vazar se o e-mail existe ou não. |
| **Rota protegida** | Acessar o catálogo sem `Authorization: Bearer` retorna **401**. |
| **Token válido** | Com JWT correto, `GET /api/v1/books` retorna **200**. |

---

## 3. Permissões de administrador (catálogo)

| Cenário | O que é verificado |
| -------- | ------------------ |
| **Patrono não admin** | Criar autor com JWT de usuário comum retorna **403**. |
| **Administrador** | O mesmo comando com JWT de admin retorna **201** e persiste o autor. |

*(Promover usuário a admin no sistema real é feito no banco; nos testes foi criado um admin diretamente na base de testes.)*

---

## 4. Empréstimos e devoluções

| Cenário | O que é verificado |
| -------- | ------------------ |
| **Empréstimo feliz** | Exemplar disponível, patrono abaixo do limite → **201** e prazo coerente com a regra (14 dias). |
| **Exemplar já emprestado** | Segundo empréstimo do mesmo livro enquanto o primeiro está ativo → **409**. |
| **Limite de 3 ativos** | Com 3 empréstimos ativos, o 4º para o mesmo usuário → **409**. |
| **Devolução no prazo** | Multa **zero** quando a devolução não ultrapassa o vencimento. |
| **Devolução atrasada** | Com vencimento no passado e “hoje” simulado depois do vencimento, a multa segue **R$ 2,00 por dia civil** de atraso. |
| **Renovação permitida** | Dentro da janela (primeiros dias do empréstimo), sem fila, uma renovação estende o prazo (**+4 dias**) e só pode ocorrer uma vez → segunda renovação **409**. |
| **Renovação com atraso** | Se o vencimento já passou, renovar retorna **400**. |
| **Renovação fora da janela** | Empréstimo “antigo” na base (mais de 7 dias corridos desde a retirada) → renovação **400**. |

---

## 5. Reservas (fila do exemplar)

| Cenário | O que é verificado |
| -------- | ------------------ |
| **Livro na estante** | Não dá para entrar na fila se o exemplar **não** está emprestado → **409** com mensagem clara. |
| **Livro emprestado** | Com exemplar emprestado para outra pessoa, o patrono entra na fila → **201**. |
| **Quem pode emprestar (fila após devolução)** | Quando o exemplar é devolvido e o líder da fila está no **limite de empréstimos**, ele entra em *hold* e o livro fica sem empréstimo ativo. Outro patrono que tenta emprestar “por cima” recebe **409** citando **fila** / espera (não basta estar disponível na prateleira). |

---

## 6. Arquivos de teste

| Arquivo | Conteúdo principal |
| -------- | ------------------- |
| `conftest.py` | Banco SQLite, override do `get_db`, cliente HTTP async, helpers (`register_patron`, `login`, sementes de catálogo). |
| `test_health.py` | Liveness e readiness. |
| `test_auth.py` | Registro, login, conflitos, 401/403 em rotas. |
| `test_admin_catalog.py` | Autor: 403 patrono / 201 admin. |
| `test_loans.py` | Empréstimo, limites, multa, renovação. |
| `test_reservations.py` | Reserva só com exemplar emprestado; fila com *hold* após devolução. |

---
