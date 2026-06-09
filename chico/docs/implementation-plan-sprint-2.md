# Plano de Implementação - Sprint 02: Fluxo de Tarefas P2P

## Objetivo
Implementar a estrutura completa de envio, recebimento, execução e relatório de tarefas entre Master e Worker, substituindo o Heartbeat simples por uma comunicação orientada a eventos e tarefas de fato.

## Escopo
- Alteração dos payloads JSON para o novo padrão de distribuição de tarefas da Sprint 2.
- Lógica de "Diferencial de Origem", permitindo que o Worker envie seu UUID de Master original quando configurado como "Emprestado".
- Gestão em memória de uma fila (`Queue`) real de tarefas do lado do Master.
- Processamento simulado no Worker seguido por envio de relatório de status (OK/NOK).
- Ciclo de encerramento de tarefa via confirmação ACK enviada do Master ao Worker.

## Tarefas (Execução Passo a Passo)

### Tarefa 1: Refatoração dos Payloads de Apresentação
- Substituir o payload de "HEARTBEAT" pelo payload de "ALIVE" (`WORKER: ALIVE`).
- O Worker deverá sempre enviar seu próprio `WORKER_UUID`.
- Implementar verificação no arquivo de configurações para a variável opcional `ORIGINAL_MASTER_UUID`.
- Se o Worker possuir esta variável (origem de outro master), ele deve enviar o campo adicional `SERVER_UUID` neste handshake, caracterizando sua atuação como Worker "Emprestado".

### Tarefa 2: Gestão de Fila (Queue) no Master
- Criar uma estrutura de fila real no Master (via `asyncio.Queue`).
- Desenvolver uma função assíncrona executada em background que simula a chegada contínua de requisições de clientes externos ao Master, preenchendo essa fila com tarefas do tipo `"QUERY"`.
- Modificar o handler de conexão do Master para que, ao receber o handshake de apresentação "ALIVE", ele interaja com a fila:
  - Se a fila estiver vazia: enviar payload `{"TASK": "NO_TASK"}`.
  - Se a fila contiver tarefas: desempilhar a próxima e enviar o payload `{"TASK": "QUERY", "USER": "..."}`.

### Tarefa 3: Processamento e Reporte de Status no Worker
- O Worker deve agora conseguir interpretar e diferenciar as diferentes respostas do Master.
- Se receber `NO_TASK`, o Worker deve apenas logar que não há demanda e aguardar para tentar de novo.
- Se receber uma tarefa verdadeira (`QUERY`), ele deve invocar a rotina de execução simulada (usando `asyncio.sleep()`).
- Ao finalizar a execução simulada, o Worker precisa construir e enviar o payload de notificação para o Master: `{"STATUS": "OK", "TASK": "QUERY", "WORKER_UUID": "..."}`.

### Tarefa 4: Log de Origens e Confirmação de Tarefa (ACK) no Master
- O Master precisa analisar o primeiro handshake (ALIVE) e salvar localmente em memória (num dicionário) se um determinado Worker é `Local` (payload sem SERVER_UUID) ou `Emprestado` (payload com SERVER_UUID preenchido).
- Ao receber a segunda mensagem de reporte (`"STATUS": "OK"`), o Master deve conseguir identificar o Worker pela memória para registrar um log detalhado, distinguindo se a tarefa foi completada por um "Worker [Emprestado]" ou um "Worker [Local]".
- Imediatamente após este log de status, o Master encerra o fluxo enviando o payload final de confirmação: `{"STATUS": "ACK", "WORKER_UUID": "..."}` para o Worker respectivo.

## Requisitos Técnicos
- Linguagem: Python 3
- Concorrência: A estrutura foi aprofundada no `asyncio`, utilizando a estrutura robusta de `asyncio.Queue` para a fila, permitindo gerenciamento atômico no loop de eventos.
- Prevenção de Erros: O código foi higienizado removendo APIs obsoletas e o tratamento nativo ao CancelledError foi adicionado para encerramentos mais limpos ao pressionar (Ctrl+C).

## Critérios de Aceite (DoD)
1. O Worker realiza o "handshake" de apresentação com sucesso, enviando UUID (seja local ou de outro Master).
2. O Master distribui ativamente uma tarefa da fila via desempilhamento ou avisa corretamente sobre a ausência delas.
3. O Worker processa essa tarefa pontualmente e o Master recebe o status retornado (`OK`).
4. O Worker finaliza sua rotina ao receber adequadamente o `ACK` do Master, concluindo sem falhas de parsing ou erros de rede.
5. O sistema trata eficientemente as diferentes origens, imprimindo corretamente e diferenciando Workers locais de emprestados durante a consolidação das informações.
