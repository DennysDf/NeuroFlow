# NeuroFlow

Sistema de gestão de alunos multi-escola, com login por CPF, perfis de acesso (Super Admin de Organização, Administrador da Escola, Administrativo, Profissional), construtor de formulários estilo Google Forms para diferentes categorias de profissionais e atendimentos compartilhados pela equipe do aluno.

Stack: **Flask 3 + SQLAlchemy 2 + PostgreSQL 16 + Jinja + HTMX + Alpine.js + SortableJS + Tailwind CSS**.

## Pré-requisitos

- Python 3.12 (com `venv`)
- PostgreSQL 16 rodando localmente
- Node.js 20 (somente para gerar o CSS via Tailwind CLI)

## Setup

```bash
# 1. Clonar e entrar
git clone <repo> && cd neuroflow

# 2. venv + dependências Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. dependências do Tailwind
npm install
npm run build           # gera app/static/css/app.css

# 4. variáveis de ambiente
cp .env.example .env
# editar .env: DATABASE_URL, SECRET_KEY, SEED_*

# 5. banco
createdb neuroflow      # usuário/permissões via psql conforme seu setup
flask db upgrade        # aplica migrations
python scripts/seed.py  # cria organização inicial + super admin + categorias

# 6. rodar
flask run --debug
```

Em outra aba, opcionalmente:

```bash
npm run dev   # Tailwind em watch
```

## Comandos úteis

```bash
make install     # pip + npm
make migrate     # flask db upgrade
make revision m="mensagem"
make seed        # roda scripts/seed.py
make run         # flask run
make test        # pytest
make lint        # ruff
make format      # black + ruff --fix
make tw-build    # Tailwind build
make tw-watch    # Tailwind em watch
```

## Perfis de acesso

| Perfil | Escopo | Pode |
|---|---|---|
| Super Admin (Organização) | Organização | Criar e editar escolas, gerenciar tudo dentro da org |
| Administrador da Escola | Escola | Tudo dentro da escola (usuários, profissionais, alunos, formulários, agenda, atendimentos) |
| Administrativo | Escola | Criar usuários, profissionais, formulários, agenda; **NÃO** vê conteúdo de atendimentos |
| Profissional | Escola | Realiza atendimentos para alunos da sua equipe; vê todos os atendimentos dos seus alunos |

Compartilhamento de atendimentos: configurado pela **equipe do aluno**. Todo profissional adicionado à equipe vê todos os atendimentos daquele aluno.

## Builder de formulários

Acesse `/schools/<id>/forms/<id>/builder`. Os tipos de campo disponíveis são: texto curto, parágrafo, número, data, escolha única, múltipla escolha, lista suspensa, escala 1-5, caixa de seleção, cabeçalho de seção. Reordenação por drag-and-drop (SortableJS) e propriedades editáveis no painel à direita. **Versões publicadas são imutáveis**, garantindo que atendimentos antigos preservem o formulário com que foram preenchidos.

## Smoke test manual

1. Login como super admin → criar Escola.
2. Criar Admin Escolar → logar e criar categoria "Psicólogo" → criar formulário "Anamnese Psi" no builder e publicar v1.
3. Criar usuário Administrativo → confirmar 403 ao tentar `/students/<id>/attendances`.
4. Criar 2 profissionais Psi (Maria, João), 1 aluno (Lucas), adicionar ambos à equipe.
5. Logar como Maria → criar atendimento de Lucas → preencher → submeter.
6. Logar como João → ver atendimento na lista do Lucas.
7. Profissional fora da equipe → 403.
8. Publicar v2 do formulário → atendimento antigo continua mostrando v1.

## Estrutura

```
app/
  __init__.py        # create_app + blueprints
  config.py          # Dev/Prod/Test configs
  context.py         # contexto de membership na sessão
  extensions.py      # db, login, csrf, limiter
  permissions.py     # decoradores RBAC + helpers de visibilidade
  auth/              # login, switch-context, hash de senha, validador de CPF
  models/            # SQLAlchemy 2 (User, Membership, Org, School, Student, ...)
  blueprints/
    org/             # super admin: organização e escolas
    schools/
    users/           # CRUD usuários + memberships
    professionals/   # categorias + profissionais
    students/        # alunos + equipe (compartilhamento)
    forms_builder/   # builder drag-and-drop + versionamento
    attendances/     # criar, preencher, submeter, listar atendimentos
    schedule/        # agenda
    dashboard/
  templates/
  static/
migrations/
scripts/seed.py
tests/
```
