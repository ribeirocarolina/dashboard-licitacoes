# Radar de licitações de tecnologia

Dashboard local que consulta o [PNCP (Portal Nacional de Contratações Públicas)](https://pncp.gov.br) e mostra licitações abertas na área de tecnologia, para empresas e consultores.

Um pequeno servidor em Python busca os dados no PNCP e entrega a página no navegador. Não há banco de dados, instalação de pacotes nem importação de arquivos.

## O que ele faz

- Busca licitações com prazo de propostas em aberto.
- Filtra por palavras-chave de tecnologia (software, TI, nuvem, segurança da informação, etc.).
- Separa os editais voltados a consultores (objeto com consultoria, assessoria, mentoria ou treinamento) dos voltados a empresas.
- Mostra contadores, ordena pelo prazo mais próximo e destaca o que encerra em até 15 dias.
- Cada resultado tem link direto para o edital no PNCP.

Por enquanto cobre apenas licitações e contratações públicas. Editais de fomento (Finep, CNPq, BNDES, FAPs, Sebrae) não estão incluídos.

## Requisitos

- Python 3.8 ou mais novo (nenhuma biblioteca extra).
- Um navegador atual (Chrome, Edge, Firefox ou Safari).
- Acesso à internet.

## Como rodar

1. Deixe `servidor.py` e `index.html` na mesma pasta.
2. Abra um terminal nessa pasta e rode:

   ```
   python servidor.py
   ```

   No Mac ou Linux, se `python` não funcionar, use `python3 servidor.py`.
3. O navegador abre sozinho em `http://127.0.0.1:8765`. Se não abrir, digite esse endereço na barra.
4. Para encerrar, volte ao terminal e tecle `Ctrl+C`.

Não abra o `index.html` com duplo clique: a página precisa do servidor rodando para buscar os dados.

## Como usar

Escolha os parâmetros e clique em **Buscar no PNCP**:

| Parâmetro | O que faz | Padrão |
|---|---|---|
| Estado (UF) | Restringe a busca a um estado | Todos |
| Modalidade | Pregão eletrônico, concorrência, dispensa, credenciamento, etc. Há uma opção que reúne as quatro principais | Principais |
| Propostas abertas até | Limite, em dias a partir de hoje, para o prazo de propostas | 60 |
| Páginas por modalidade | Quantas páginas de 50 registros ler em cada modalidade | 5 |
| Palavras-chave | Termos separados por vírgula; `\b` nas pontas marca palavra inteira (ex.: `\bti\b`) | Lista de tecnologia |

Os resultados aparecem à medida que as páginas chegam. Depois da busca, use o campo de texto e o seletor de público para filtrar a lista sem consultar o PNCP de novo.

Ler mais páginas encontra mais editais, mas deixa a busca mais lenta.

## Como funciona

```
navegador (index.html)  ->  servidor.py (127.0.0.1:8765)  ->  API de consultas do PNCP
```

- `index.html` monta a tela e pede os dados ao servidor, página por página.
- `servidor.py` consulta o PNCP, aplica o filtro de palavras-chave e devolve só o que interessa. Como é o servidor que fala com o PNCP, o navegador não sofre bloqueio de CORS.
- A API usada é a de consultas, no serviço de contratações com período de propostas em aberto (`/api/consulta/v1/contratacoes/proposta`).
- O servidor escuta apenas em `127.0.0.1`, ou seja, só é acessível no seu computador.

## Personalização

No topo do `servidor.py`:

- `PORTA`: porta do servidor (padrão `8765`).
- `EXCLUIR`: termos que descartam um edital mesmo quando casa com as palavras-chave (padrão: medicamentos, merenda, obra de engenharia, veículo).
- `CONSULTORIA`: termos que marcam o edital como voltado a consultores.

As palavras-chave de tecnologia e as modalidades podem ser mudadas direto na tela. Para alterar os valores iniciais, edite o `index.html`.

## Limitações

- O filtro olha só o texto do objeto da licitação. Pode deixar passar editais relevantes com descrição genérica e trazer alguns irrelevantes. Ajuste as palavras-chave conforme o seu caso.
- Há relatos de qualidade irregular nos dados do PNCP (campos vazios ou status inconsistente). Confira sempre prazos e regras no documento oficial do edital.
- Os resultados não ficam salvos: cada busca começa do zero.
- Os nomes de parâmetros e campos seguem a API pública do PNCP. Se o PNCP alterar a API, o código pode precisar de ajustes. A documentação oficial está em `https://pncp.gov.br/api/consulta/swagger-ui`.

## Problemas comuns

- **`python` não é reconhecido:** instale o Python em python.org/downloads e, no Windows, marque "Add Python to PATH" na instalação.
- **A porta já está em uso:** feche o servidor anterior ou mude `PORTA` no `servidor.py`.
- **Mensagem de erro do PNCP na tela:** o texto vem da própria API. Costuma ser parâmetro inválido ou instabilidade; tente de novo ou reduza o número de páginas.
- **Nenhum resultado:** aumente os dias à frente, leia mais páginas ou revise as palavras-chave.

## Estrutura

```
radar-licitacoes/
├── servidor.py   # servidor local e consulta ao PNCP
├── index.html    # dashboard
└── README.md
```
