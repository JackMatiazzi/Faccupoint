# Faccupoint

FaccuPoint é uma plataforma educacional gamificada desenvolvida como TCC, focada em quizzes, pontuação e progressão. Utiliza backend em PostgreSQL com WebSockets em uma arquitetura distribuída, onde o frontend executável se conecta a um servidor local e sincroniza dados com um servidor central.

## Ciclo 1.1:  Ambiente de desenvolvimento

**Requisitos:** Python 3.10 ou superior , Git, vscode o  SQLite está incluído na biblioteca padrão do Python (`sqlite3`).

### Configuração (Windows / PowerShell)

1. Clonar o repositório e entrar na pasta do projeto.
2. Criar e ativar o ambiente virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instalar dependências:

   ```powershell
   pip install -r requirements.txt
   ```

4. Executar a linha de teste de verificação:

   ```powershell
   python -c "import kivy; print(kivy.__version__)"
   ```

Para desativar o venv: `deactivate`.

### Resultado esperado (1.1)

- Ambiente virtual `.venv` com Kivy instalado.
- Repositório versionado; dependências listadas em [`requirements.txt`](requirements.txt).

