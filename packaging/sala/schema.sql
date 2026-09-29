SET ROLE faccupoint;
CREATE TABLE docentes (
    id_docente SERIAL PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    pin_hash TEXT NOT NULL, papel TEXT NOT NULL DEFAULT 'prof',
    precisa_trocar_pin BOOLEAN NOT NULL DEFAULT TRUE,
    solicitou_troca_pin BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE quizzes (
    id_quiz SERIAL PRIMARY KEY, titulo TEXT NOT NULL, descricao TEXT,
    id_docente_proprietario INTEGER NOT NULL REFERENCES docentes,
    tempo_segundos INTEGER, link_midia TEXT
);
CREATE TABLE perguntas (
    id_pergunta SERIAL PRIMARY KEY, id_quiz INTEGER NOT NULL REFERENCES quizzes,
    enunciado TEXT NOT NULL, ordem INTEGER NOT NULL, link_midia TEXT,
    peso INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE alternativas (
    id_alternativa SERIAL PRIMARY KEY, id_pergunta INTEGER NOT NULL REFERENCES perguntas,
    texto TEXT NOT NULL, correta BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE sessoes (
    id_sessao SERIAL PRIMARY KEY, codigo_curto TEXT NOT NULL,
    id_quiz INTEGER NOT NULL REFERENCES quizzes,
    id_docente_anfitriao INTEGER NOT NULL REFERENCES docentes,
    criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pergunta_atual INTEGER NOT NULL DEFAULT -1
);
CREATE TABLE participantes (
    id_participante SERIAL PRIMARY KEY, id_sessao INTEGER NOT NULL REFERENCES sessoes,
    apelido TEXT NOT NULL, UNIQUE(id_sessao, apelido)
);
CREATE TABLE tentativas (
    id_tentativa SERIAL PRIMARY KEY, id_participante INTEGER NOT NULL REFERENCES participantes,
    id_pergunta INTEGER NOT NULL REFERENCES perguntas,
    id_alternativa_escolhida INTEGER REFERENCES alternativas,
    acertou BOOLEAN NOT NULL, registrada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
