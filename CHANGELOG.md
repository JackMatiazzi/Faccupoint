# Changelog

## [1.4.0](https://github.com/JackMatiazzi/Faccupoint/compare/v1.3.1...v1.4.0) (2026-09-29)


### Features

* **video:** aumenta o video no telao do professor e tira da tela do aluno ([9d58ac2](https://github.com/JackMatiazzi/Faccupoint/commit/9d58ac28ad0337b4a392891b56698b727051e6b0))
* **video:** video maior no telao do professor, some da tela do aluno ([6c5ea21](https://github.com/JackMatiazzi/Faccupoint/commit/6c5ea2188e63e9c3c84c6ad5a191f6672f666e27))


### Bug Fixes

* **painel:** peso da pergunta aceita separador decimal no campo ([c6da8a0](https://github.com/JackMatiazzi/Faccupoint/commit/c6da8a02a0e7723e1886ca994e7277d2675c3a70))
* **painel:** peso da pergunta aceita separador decimal no campo ([c43b671](https://github.com/JackMatiazzi/Faccupoint/commit/c43b67194449c9bddae46885175efdca1ff9143c))

## [1.3.1](https://github.com/JackMatiazzi/Faccupoint/compare/v1.3.0...v1.3.1) (2026-09-29)


### Bug Fixes

* **build:** inclui flet.fastapi como hidden import no executavel Windows ([a98f784](https://github.com/JackMatiazzi/Faccupoint/commit/a98f784cc6ec4a9c7c9f1a401d9e53079a02dcc0))
* **build:** inclui flet.fastapi como hidden import no executavel Windows ([c86ac66](https://github.com/JackMatiazzi/Faccupoint/commit/c86ac666fc76d4510dc3da711baf781b31344a83))
* **lobby:** traz o QR/lobby do [#27](https://github.com/JackMatiazzi/Faccupoint/issues/27) que nunca chegou em main ([4e72d5c](https://github.com/JackMatiazzi/Faccupoint/commit/4e72d5ccc4e9eb321d16745de6b6b94937cd062e))

## [1.3.0](https://github.com/JackMatiazzi/Faccupoint/compare/v1.2.1...v1.3.0) (2026-09-29)


### Features

* **pontuacao:** peso decimal (0,01 a 100) com snapshot dos pontos por tentativa ([4fc5e44](https://github.com/JackMatiazzi/Faccupoint/commit/4fc5e44beb454f64cdc8707f35a04c56f68955ee))
* **pontuacao:** peso decimal por pergunta, snapshot de pontos e CSV ([90d2ca0](https://github.com/JackMatiazzi/Faccupoint/commit/90d2ca08c1580aab18f95dd271321a13dbba8c48))
* **professor:** janela dedicada via WebView2 no Windows ([a438138](https://github.com/JackMatiazzi/Faccupoint/commit/a4381381bce2e8d9f52cba87abe5753db6747f08))
* **professor:** janela do Windows passa a usar WebView2 pra videos incorporados ([da7dfa1](https://github.com/JackMatiazzi/Faccupoint/commit/da7dfa102d1671867a529747d362a5a3c7e8f96f))


### Bug Fixes

* **aluno:** backend confiavel definido so pelo operador, nao por query da URL ([67bd82d](https://github.com/JackMatiazzi/Faccupoint/commit/67bd82dd03105c5ff9119ef29426e183b111d1e5))
* **aluno:** backend confiavel definido so pelo operador, nao por query da URL ([c81c758](https://github.com/JackMatiazzi/Faccupoint/commit/c81c75826000d2565ddd836709f11faccb15ee18))
* **aluno:** preserva o player de video entre perguntas consecutivas ([8148301](https://github.com/JackMatiazzi/Faccupoint/commit/8148301413afab62d6299f907404efeb471b6449))
* **cadastro:** valida campos de docente e tempo de quiz antes do banco ([8ef6013](https://github.com/JackMatiazzi/Faccupoint/commit/8ef6013a61f63225a3285b25ed19b6cdd911edfe))
* **cadastro:** valida campos de docente e tempo de quiz antes do banco ([212fa7d](https://github.com/JackMatiazzi/Faccupoint/commit/212fa7dd302be0dc1271496973680d27f4373ab6))
* **conexao:** propaga API_URL pro ambiente antes de abrir os subprocessos ([3949ad1](https://github.com/JackMatiazzi/Faccupoint/commit/3949ad1af0349abbf2d2a2a04ce634a3c5f73f37))
* **pontuacao:** Participante.pontos vira float ([3b21529](https://github.com/JackMatiazzi/Faccupoint/commit/3b2152923b73cbe31c0f05c0887965cf6128b815))
* **protocolo:** aceita numero opcional na resposta para compatibilidade com 1.2.1 ([a4badc8](https://github.com/JackMatiazzi/Faccupoint/commit/a4badc80aa3ed9cec8a298e21d97e43e371c898e))
* **sala:** encadeia sobre fix/seguranca-sessoes; packaging/sala/aluno_web.py importava LimitesMiddleware, que so existe la ([9238044](https://github.com/JackMatiazzi/Faccupoint/commit/92380444182e816f3523f8e91b2e1c0ee6a5752a))
* **sala:** encadeia tambem sobre fix/conexao-alunos; compose configurava API_URL que o cliente antigo ignorava ([d7aef43](https://github.com/JackMatiazzi/Faccupoint/commit/d7aef432ea3884b9d2bc492dda57b5acb6a6bd8c))
* **seguranca:** revalida sessao do professor, protege reconexao e adiciona limites ([89145d3](https://github.com/JackMatiazzi/Faccupoint/commit/89145d3a008f6718b7693c3d957567ac491faa87))
* **tempo-real:** aceita numero opcional na resposta para compatibilidade com 1.2.1 ([897535a](https://github.com/JackMatiazzi/Faccupoint/commit/897535ae2920ee6e43f1d1e7f2385fe97fb7b3da))
* **video-aluno:** preserva o player de video entre perguntas ([0762275](https://github.com/JackMatiazzi/Faccupoint/commit/07622757972241df08aae543cbd8e0652f943c6d))

## [1.2.1](https://github.com/JackMatiazzi/Faccupoint/compare/v1.2.0...v1.2.1) (2026-09-25)


### Bug Fixes

* **email:** adiciona envio Gmail API por HTTPS ([027735b](https://github.com/JackMatiazzi/Faccupoint/commit/027735b5dec8f3826eac4a52785b2ff2cee81657))
* **email:** envia relatorios pela Gmail API via HTTPS ([99801b5](https://github.com/JackMatiazzi/Faccupoint/commit/99801b55f502d4b593ed28be8cf2f61cdc3bb059))

## [1.2.0](https://github.com/JackMatiazzi/Faccupoint/compare/v1.1.1...v1.2.0) (2026-09-02)


### Features

* **aluno:** reconexao na sessao e exibicao do peso da questao ([09011c7](https://github.com/JackMatiazzi/Faccupoint/commit/09011c700387595726b1f32cd86c4fd06f2e2e33))
* **auth:** PIN provisorio com troca obrigatoria, reset via admin e invalidacao de token ao trocar PIN ([60686fe](https://github.com/JackMatiazzi/Faccupoint/commit/60686fe5c40d36a7da453665ca08272961510275))


### Bug Fixes

* **test:** define SECRET_KEY no setUp do teste de troca de PIN ([a242bb5](https://github.com/JackMatiazzi/Faccupoint/commit/a242bb54ce20d7ad28c519b2398c002c2301ef43))

## [1.1.1](https://github.com/JackMatiazzi/Faccupoint/compare/v1.1.0...v1.1.1) (2026-07-12)


### Bug Fixes

* teste release ([ab24700](https://github.com/JackMatiazzi/Faccupoint/commit/ab247007e8f575eb6316306051f7471590ef2463))
* torna teste de versao dinamico ([5d7d072](https://github.com/JackMatiazzi/Faccupoint/commit/5d7d0721a8e0c0212d1aba1eebc8af7bce11065c))

## [1.1.0](https://github.com/JackMatiazzi/Faccupoint/compare/v1.0.1...v1.1.0) (2026-07-12)


### Features

* adiciona atualizacao por versao ([d928754](https://github.com/JackMatiazzi/Faccupoint/commit/d928754ed52dc38691b4e9e7f8760f2385b3264c))
* adiciona atualizacao por versao ([c17b318](https://github.com/JackMatiazzi/Faccupoint/commit/c17b3187b3183f3fe6739365fa51585db4d366e8))
