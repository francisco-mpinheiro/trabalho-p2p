# Projeto P2P

Este projeto implementa uma arquitetura distribuída baseada em nós (Workers) que se comunicam com um nó central (Master) utilizando sockets TCP.

## Estrutura do Projeto

- `master.py`: Servidor que escuta conexões dos workers, processa mensagens e responde.
- `worker.py`: Cliente que se conecta ao master e mantém a comunicação ativa (envia heartbeats e implementa reconexão).
- `config.py`: Arquivo de configuração contendo constantes globais como host, porta, intervalo de heartbeat, UUIDs das instâncias e utilitários de log.

## Como Executar

O projeto foi construído utilizando apenas a biblioteca padrão do Python (`asyncio`, `json`, etc.), portanto, **não é necessário criar um ambiente virtual (venv)** ou instalar bibliotecas externas.

Para iniciar o servidor central:
```bash
python master.py
```

Para iniciar um nó trabalhador:
```bash
python worker.py
```
*(Você pode abrir múltiplos terminais e rodar vários `worker.py` simultaneamente)*

---

## Histórico de Desenvolvimento

### Sprint 1: Mecanismo de Heartbeat

**Objetivo:** Estabelecer a comunicação base entre o Worker e o Master, garantindo que o Worker consiga verificar se o seu "mestre" está ativo através da troca de mensagens JSON via TCP.

**O que foi feito:**
* **Infraestrutura TCP Assíncrona:** Utilização da biblioteca `asyncio` para garantir alta concorrência sem bloqueios. O master agora consegue lidar com múltiplas conexões de workers simultaneamente de forma limpa.
* **Comunicação por JSON:** Definição de um protocolo baseado no envio e recebimento de payloads no formato JSON, usando a quebra de linha (`\n`) como delimitador entre as mensagens.
* **Mecanismo de Heartbeat:** O worker envia periodicamente (baseado no `HEARTBEAT_INTERVAL` em `config.py`) uma requisição informando sua UUID com a `TASK: "HEARTBEAT"`.
* **Processamento no Master:** O master realiza o parse das requisições. Ao identificar a tarefa de heartbeat, ele valida e responde imediatamente com `RESPONSE: "ALIVE"`.
* **Resiliência e Tolerância a Falhas:** O worker foi projetado com suporte a reconexão. Se a conexão com o master for perdida (timeout) ou recusada, ele entra em um loop tentando se reconectar a cada 5 segundos até que o master volte a ficar online.
* **Logging e Monitoramento:** Adição de utilitários nativos de log no `config.py` para visualizar o status do sistema, diferenciando avisos, erros e mensagens normais entre Worker e Master.
