
# python-worker-boilerplate

Um boilerplate mínimo para workers em Python — projeto organizado para facilitar a criação de consumidores (SQS, filas, workers) e serviços de borda (health check, adapters, logging). O objetivo é fornecer uma base limpa e modular para construir workers testáveis e configuráveis.

## Conteúdo

- Código-fonte em `src/`
- Entrypoints em `src/entry_point/` (HTTP health, SQS consumer)
- Casos de uso em `src/core/use_cases/`
- Adaptadores de infra em `src/infra/adapters/`
- Configuração em `src/config/`

## Requisitos

- Python 3.8+ (recomendado 3.10/3.11)
- Pip

Observação: este projeto usa `pyproject.toml` para metadados; adapte o gerenciador de dependências conforme sua preferência (pip, poetry, pipx, etc.).

## Instalação

1. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instale dependências:

Opção A (pip):

```bash
python -m pip install -e .
```

Opção B (poetry):

```bash
poetry install
```

Se o projeto não fornecer instalação editável, instale manualmente as dependências listadas no `pyproject.toml`.

## Como executar

O projeto contém um módulo principal em `src/main.py`. Para executar localmente:

```bash
source .venv/bin/activate
python -m src.main
```

Dependendo da configuração do entry point que você desejar executar (por exemplo, consumidor SQS), pode ser necessário ajustar variáveis de ambiente apontando para o broker/filas ou provider locais.

### Health check

Há um serviço de health em `src/entry_point/http/health/health_service.py` — use-o para verificar rapidamente se os componentes principais iniciaram corretamente.

## Estrutura do projeto

Visão geral dos arquivos/dirs principais:

- `src/main.py` — ponto de entrada principal para execução local.
- `src/core/` — entidades e casos de uso (business logic).
- `src/entry_point/` — adaptadores de entrada: HTTP health, SQS consumer.
- `src/infra/adapters/logging/` — adaptador de logging (ex.: structlog).
- `src/config/` — configurações e leitura de variáveis de ambiente.

Essa organização segue princípios de Clean Architecture / Hexagonal Architecture: separação entre núcleo (core), portas/contratos (ports) e adaptadores (infra/entry points).

## Testes

Este repositório não contém testes explícitos por padrão. Recomenda-se adicionar testes unitários para casos de uso em `src/core/use_cases/` e testes de integração para os entry points.

Exemplo rápido (pytest):

```bash
python -m pip install pytest
pytest
```

## Desenvolvimento

- Use um ambiente virtual.
- Mantenha as dependências no `pyproject.toml`.
- Prefira adicionar pequenos commits e documentar mudanças no README quando alterar a estrutura ou contratos entre módulos.

## Contribuição

Contribuições são bem-vindas. Abra issues para discutir mudanças e envie pull requests com descrições claras do que foi alterado.

## Licença

Nenhuma licença foi definida neste repositório por padrão. Adicione um arquivo `LICENSE` com a licença desejada (por exemplo, MIT) se pretender tornar o projeto open-source.

---

Se quiser, eu posso:

- ajustar o README com comandos específicos de execução (por exemplo, como rodar o consumer SQS),
- adicionar exemplos de variáveis de ambiente em um `.env.example`,
- ou criar um arquivo `requirements.txt` / `pyproject.toml` mais explícito.

Diga qual desses extras você quer que eu adicione primeiro.


