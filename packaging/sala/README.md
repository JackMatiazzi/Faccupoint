# Ambiente de teste de sala

Entrada por codigo/apelido e compartilhamento de quizzes entre professores sao
intencionais e permanecem habilitados. IP nao comprova identidade do aluno;
navegadores nao fornecem um ID confiavel de aparelho. Nenhum fingerprint foi adicionado.

## Isolamento

Este Compose usa PostgreSQL novo, usuario de aplicacao sem superusuario, segredos
gerados em `.local/sala-secrets`, rede interna sem saida para internet para backend,
aluno e banco, processos Python sem root, filesystem somente leitura, limites de
memoria/processos e sem montagem das pastas pessoais ou do socket Docker.
Os `.env` do projeto nao entram na imagem nem sao lidos pelo Compose.
O proxy recebe as conexoes publicas; banco e backend nao sao publicados na LAN.
O professor desktop acessa a API por `127.0.0.1:18000`.

O banco remoto usado pelo launcher normal nao e migrado nem copiado para este ambiente.
E-mails externos e midias que dependam de conexao de saida do servidor nao fazem
parte deste teste isolado. Clientes podem precisar de internet para recursos do Flet.
Containers reduzem impacto; nao sao garantia de isolamento absoluto do host.

## Iniciar no computador

Com Docker Desktop em execucao, na raiz do repositorio:

```powershell
powershell -NoProfile -File packaging/sala/iniciar-sala.ps1
```

Aluno: `http://localhost:8081`. Conta ficticia: `professor@teste.invalid`.
O PIN inicial aleatorio esta em `.local/sala-secrets/admin_pin`; e solicitada troca
no primeiro login. Depois de trocar, use o PIN escolhido. Nenhuma senha e versionada.

## Desenvolvimento simples

Este ambiente usa HTTP local e nao exige certificados. Abra `http://localhost:8081`.
A API administrativa para testes fica em `http://127.0.0.1:18000`.
O banco separado e as protecoes de autenticacao e limites permanecem ativos.

Para testar com outro aparelho da mesma rede, publique somente na interface local:

```powershell
powershell -NoProfile -File packaging/sala/iniciar-sala.ps1 -Endereco 192.168.1.16
```

HTTP pela rede nao criptografa o trafego; use apenas dados ficticios neste teste.
Para producao, HTTPS deve usar certificado reconhecido pelos navegadores, sem
pedir instalacao de certificados aos alunos.

O firewall nao e modificado automaticamente. Se bloquear a conexao, o script
`proteger-firewall.ps1` mostra um plano de regras; `-Aplicar` exige administrador.
Ele libera TCP 8081 para a sub-rede, bloqueia SMB no perfil publico e desabilita
regras amplas do Python, guardando seus nomes em `.local/firewall`.

## Limites e verificacao

HTTP: 3000 requisicoes/minuto por IP, 10000/minuto globais, 120/minuto em auth por
IP, corpo maximo de 64 KiB, prazo total de leitura 15 segundos.
Conta: 5 tentativas de login/PIN por minuto (inclui sucesso), recuperacao 3/10min.
WebSocket backend: 1000 conexoes globais, 300/IP, 600 aberturas/minuto/IP,
120 mensagens/minuto/conexao, 16 KiB/mensagem e binarios desabilitados.
Flet: 600 mensagens/minuto/conexao, 256 KiB/mensagem e binarios permitidos.
Todos configuraveis pelas variaveis de `backend/infraestrutura/limites.py`.

Quotas sao por processo; mantenha um worker. O proxy e o frontend Flet fazem
conexoes internas: o backend pode ver varios alunos no mesmo IP. Nao confie em
X-Forwarded-For fornecido pelo cliente para criar quotas novas.
Os limites sao iniciais, nao capacidade comprovada para 200 alunos simultaneos.
Sockets de professor sao revalidados antes dos envios e quando ociosos a cada 5s.
O timeout de revalidacao e 3s; falha de banco encerra a conexao.

```powershell
python -m unittest discover -s tests -v
docker compose -f packaging/sala/compose.yaml ps
docker compose -f packaging/sala/compose.yaml down
```

`down` para os servicos e preserva o banco local. Nao use `down -v` se desejar
preservar os quizzes de teste. `.local/sala-secrets` deve ser preservado junto
com os volumes; recriar segredos sem recriar banco causa falha de autenticacao.
