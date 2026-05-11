-- criar tabela de docentes
-- papel: 'adm' cadastra outros docentes; 'prof' não.
create table if not exists docentes(
    id_docente integer primary key autoincrement,
    nome text not null,
    email text not null unique,
    pin_hash text not null,
    papel text not null default 'prof'
        check (papel in ('adm', 'prof'))
);

--  criar tabela de quizzes
create table if not exists quizzes (
    id_quiz integer primary key autoincrement,

    titulo text not null,
    titulo_normalizado text not null,
    descricao text,

    id_docente_proprietario integer not null,

    constraint fk_quiz_docente
        foreign key (id_docente_proprietario)
        references docentes(id_docente),

    constraint uq_quiz_docente_titulo
        unique (id_docente_proprietario, titulo_normalizado)
);

--  criar tabela de perguntas

create table if not exists perguntas (
    id_pergunta integer primary key autoincrement,

    id_quiz integer not null,
    enunciado text not null,
    ordem integer not null,

    constraint fk_pergunta_quiz
        foreign key (id_quiz)
        references quizzes(id_quiz),

    constraint uq_pergunta_ordem_quiz
        unique (id_quiz, ordem)
);

-- criar as alternativas

create table if not exists alternativas (
    id_alternativa integer primary key autoincrement,

    id_pergunta integer not null,
    texto text not null,
    correta integer not null,

    constraint fk_alternativa_pergunta
        foreign key (id_pergunta)
        references perguntas(id_pergunta),

    constraint ck_alternativa_correta
        check (correta in (0, 1))
);

-- sessão ao vivo (DER / Apêndice C — Ciclo 2+ consome estes vínculos)
create table if not exists sessoes (
    id_sessao integer primary key autoincrement,
    id_quiz integer not null,
    id_docente_anfitriao integer not null,
    codigo_curto text,
    criada_em text not null default (datetime('now')),

    constraint fk_sessao_quiz
        foreign key (id_quiz)
        references quizzes(id_quiz),

    constraint fk_sessao_docente
        foreign key (id_docente_anfitriao)
        references docentes(id_docente)
);

create table if not exists participantes (
    id_participante integer primary key autoincrement,
    id_sessao integer not null,
    apelido text not null,

    constraint fk_participante_sessao
        foreign key (id_sessao)
        references sessoes(id_sessao)
);

create table if not exists tentativas (
    id_tentativa integer primary key autoincrement,
    id_participante integer not null,
    id_pergunta integer not null,
    id_alternativa_escolhida integer,
    acertou integer not null,
    registrada_em text not null default (datetime('now')),

    constraint fk_tentativa_participante
        foreign key (id_participante)
        references participantes(id_participante),

    constraint fk_tentativa_pergunta
        foreign key (id_pergunta)
        references perguntas(id_pergunta),

    constraint fk_tentativa_alternativa
        foreign key (id_alternativa_escolhida)
        references alternativas(id_alternativa),

    constraint ck_tentativa_acertou
        check (acertou in (0, 1)),

    constraint uq_tentativa_participante_pergunta
        unique (id_participante, id_pergunta)
);