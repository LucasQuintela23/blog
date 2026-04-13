# Tech Blog - High Performance & Quality Engineering

Um blog técnico desenvolvido com foco em **Engenharia de Software Rigorosa**, **Clean Architecture** e princípios **12-Factor App**. Este projeto serve como uma referência para aplicações Django modernas, escaláveis e testáveis.

## 🚀 Tech Stack

* **Backend**: Python 3.14+, Django 5.x
* **Database**: PostgreSQL 15+ (com SearchVector para Full-Text Search)
* **Frontend**: Django Templates, Bootstrap 5, Highlight.js (Syntax Highlighting)
* **Infra**: Docker, Docker Compose, Gunicorn, WhiteNoise
* **QA/SDET**: Pytest, Factory Boy, Ruff, Mypy, Coverage (Meta > 95%)
* **Segurança**: Sanitização estrita de HTML com `nh3` (Rust-based)

## 🏗 Arquitetura

O projeto segue uma estrutura de **Modular Monolith**:

* `core/`: Configurações do projeto (Settings, WSGI/ASGI).
* `blog/`: Domínio principal (Posts, Views).
* `users/`: Gestão de usuários customizada.
* `tests/`: Suíte de testes segregada e escalável.

## 🛠️ Como Rodar Localmente

### Pré-requisitos

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Quickstart

1. **Clone o repositório:**

    ```bash
    git clone <seu-repo-url>
    cd blog
    ```

2. **Suba o ambiente com Docker:**

    ```bash
    docker compose up -d --build
    ```

    Isso irá construir a imagem, instalar as dependências e iniciar os serviços `web` (Django) e `db` (Postgres).

3. **Acesse a aplicação:**
    * Frontend: [http://localhost:8000](http://localhost:8000)
    * Admin: [http://localhost:8000/admin](http://localhost:8000/admin)

### Configuração Inicial

Como o banco de dados é inicializado do zero, você precisará criar um superusuário para acessar o admin:

```bash
docker compose exec web python manage.py createsuperuser
```

## 🧪 Testes e Qualidade (QA)

Este projeto possui uma barreira de qualidade estrita. O CI/CD falhará se a cobertura de testes for menor que 95%.

### Rodar Testes

Para executar a suíte de testes completa dentro do container:

```bash
docker compose exec web python -m pytest
```

### Verificar Cobertura

O relatório de cobertura é gerado automaticamente. Para ver o detalhe no terminal:

```bash
docker compose exec web python -m pytest --cov=. --cov-report=term-missing
```

### Linting e Type Checking

```bash
# Lint (Ruff)
docker compose exec web ruff check .

# Type Check (Mypy)
docker compose exec web mypy .
```

## 🔒 Segurança

* **XSS Protection**: Todo input de Markdown é convertido para HTML e sanitizado via `nh3` antes de ser salvo no banco.
* **CSRF/SQL Injection**: Proteções nativas do Django habilitadas.
* **Container**: A aplicação roda como usuário não-root (`appuser`).

## 🌐 Tradução Automática (LibreTranslate)

O projeto suporta tradução automática de posts (PT -> EN/ES) ao salvar no admin.

Configure no ambiente:

```bash
LIBRETRANSLATE_ENABLED=True
LIBRETRANSLATE_URL=http://seu-libretranslate:5000/translate
LIBRETRANSLATE_API_KEY=
LIBRETRANSLATE_SOURCE_LANGUAGE=pt
LIBRETRANSLATE_TIMEOUT=15
```

Comportamento:

* A tradução é aplicada no `save` do post.
* Só preenche campos EN/ES vazios (não sobrescreve traduções manuais).
* Se a API falhar, o post continua sendo salvo normalmente.

## 📦 CI/CD

O pipeline do GitHub Actions (`.github/workflows/ci-cd.yml`) executa:

1. **Quality Gate**: Lint, Types, Tests (com validação de coverage).
2. **Build**: Constrói e publica a imagem Docker no GHCR (apenas se o Quality Gate passar).
