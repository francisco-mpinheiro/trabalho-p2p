# Plano de Implementação - Sprint 01: Mecanismo de Heartbeat

## Objetivo
Estabelecer a comunicação base entre o Worker e o Master, garantindo que o Worker consiga verificar se o seu "mestre" está ativo através da troca de mensagens JSON via TCP.

## Escopo
- Criação da infraestrutura base TCP.
- Implementação do envio e recebimento de payloads JSON delimitados por `\n`.
- Suporte a múltiplas conexões concorrentes no Master.
- Implementação de reconexão e loop de envios periódicos no Worker.
- Uso de uma biblioteca para colorir/destacar os logs no terminal (ex: `colorama`).

## Tarefas (Execução Passo a Passo)

### Tarefa 1: Infraestrutura Básica e Configurações (config.py)
- Configurar o ambiente virtual e instalar dependências (`colorama`).
- Criar o arquivo `config.py`.
- Definir constantes globais: HOST, PORT, HEARTBEAT_INTERVAL, UUIDs e um utilitário base para formatação de logs coloridos.

### Tarefa 2: Infraestrutura TCP do Master (master.py)
- Criar `master.py`.
- Implementar o servidor TCP utilizando `asyncio` (para garantir alta concorrência e não bloqueio).
- Implementar escuta de conexões e loop contínuo de leitura de stream até o delimitador `\n`.
- Logar o recebimento de mensagens.

### Tarefa 3: Infraestrutura TCP do Worker e Lógica de Requisição (worker.py)
- Criar `worker.py`.
- Implementar o cliente TCP com `asyncio` para manter a conexão aberta sem travar a thread principal.
- Implementar lógica de reconexão em caso de falha.
- Adicionar o loop que envia periodicamente (a cada 10s) o payload de `HEARTBEAT` validado (JSON + `\n`).

### Tarefa 4: Lógica de Resposta e Parsing no Master
- Atualizar o `master.py` para realizar o parsing (JSON) das mensagens recebidas na conexão.
- Se `TASK == "HEARTBEAT"`, enviar de volta a resposta `{"SERVER_UUID": "...", "TASK": "HEARTBEAT", "RESPONSE": "ALIVE"}` finalizada com `\n`.
- Registrar logs de recebimento e envio coloridos no terminal destacando o lado "MASTER".

### Tarefa 5: Lógica de Recepção no Worker e Conclusão
- Atualizar o `worker.py` para aguardar a resposta do Master após o envio do heartbeat (leitura em background).
- Fazer o parsing da resposta e verificar o status `ALIVE`.
- Registrar confirmação de conexão saudável via logs coloridos no terminal destacando o lado "WORKER".

## Requisitos Técnicos
- Linguagem: Python 3.
- Concorrência: `asyncio` (Padrão moderno para I/O e alta concorrência em Python, superior a Threads puras para este caso).
- Bibliotecas Externas: `colorama` (para cores no terminal) e os pacotes padrão `json` e `logging`.
- Protocolo de Transporte: TCP (Sockets / Streams via asyncio).
- Formato de Mensagem: Payload JSON finalizado com `\n`.

## Critérios de Aceite (DoD)
1. O Worker consegue abrir uma conexão TCP com o Master.
2. O Master recebe a mensagem JSON, realiza o parsing e identifica corretamente o comando `HEARTBEAT`.
3. O Worker recebe a resposta `"ALIVE"` e registra a confirmação em log colorido.
4. A conexão é mantida ou restabelecida automaticamente em caso de falha (Resiliência).
5. Logs no terminal diferenciam visualmente as saídas do Master e do Worker.

## User Review Required
> [!IMPORTANT]
> Vou utilizar o framework nativo `asyncio` do Python para garantir concorrência de forma muito limpa e eficiente no Master e Worker. Isso evitará as dores de cabeça do gerenciamento de múltiplas `Threads`. Além disso, incluirei a biblioteca `colorama` para prover logs formatados e coloridos, como você solicitou para destacar a interação entre eles no terminal.
