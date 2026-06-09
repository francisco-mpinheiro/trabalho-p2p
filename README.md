# Projeto: Arquitetura P2P com Balanceamento de Carga Dinâmico

Este repositório contém a implementação do projeto prático desenvolvido para a disciplina de Arquitetura de Sistemas Distribuídos do UniCEUB. 

O objetivo principal do sistema é demonstrar o conceito de balanceamento de carga horizontal por meio de uma arquitetura P2P (Peer-to-Peer). A aplicação é composta por nós "Master", que gerenciam seus próprios conjuntos de nós "Worker" (Farms). Quando um Master atinge um limiar de saturação de carga, ele negocia dinamicamente o empréstimo de Workers com Masters vizinhos através de um protocolo de consenso.

## Estrutura do Repositório

O desenvolvimento foi dividido em quatro etapas principais, cada uma contida em seu respectivo diretório:

* **`/trabalho-p2p-sprint-1`**: Implementação do mecanismo base de comunicação e Heartbeat (TCP) entre Worker e Master.
* **`/trabalho-p2p-sprint-2`**: Gestão do ciclo de vida das tarefas, incluindo a fila de processamento, apresentação dos Workers e reporte de status (OK/NOK/ACK).
* **`/trabalho-p2p-sprint-3`**: Protocolo de negociação entre Masters (Master-to-Master) e o redirecionamento dinâmico de Workers emprestados.
* **`/trabalho-p2p-sprint-4`**: Integração final com o Supervisor de Métricas do cluster, enviando relatórios de desempenho em tempo real para o dashboard da disciplina.

> **Nota:** As instruções detalhadas sobre a arquitetura específica e os passos para executar cada parte do sistema (incluindo dependências e inicialização dos nós) estão documentadas dentro do README de cada um dos diretórios das sprints.