# Projeto Farm P2P Distribuído

Este projeto é uma implementação em Python de um sistema distribuído mestre-trabalhador (Master-Worker) com comunicação P2P entre Masters (Master-to-Master) para compartilhamento dinâmico de recursos sob saturação, além de telemetria TLS para painéis de monitoramento.

---

## 🛠️ Requisitos e Dependências

Para rodar este projeto, você precisa ter o **Python 3.8+** instalado na sua máquina. 

O projeto utiliza apenas duas bibliotecas externas. Para instalá-las, abra o terminal na pasta raiz do projeto e execute o comando:

```bash
pip install -r requirements.txt
```

*(Se você preferir instalar manualmente, as dependências são: `colorama` e `psutil`)*

---

## 🚀 Como Executar o Projeto

A inicialização do cluster local é dividida em dois passos simples:

### 1. Iniciando o Servidor Master
O Master é o cérebro da operação. Ele gerencia as tarefas, escuta os Workers, monitora a carga e se comunica com os Masters vizinhos.
No terminal, execute:

```bash
python master.py
```
*(No Windows, você pode usar `py master.py`)*

Se aparecer um aviso do **Firewall do Windows**, certifique-se de clicar em **Permitir Acesso**, para que o P2P funcione na rede local.

### 2. Iniciando os Workers (Trabalhadores)
Os workers são os executores. Você pode iniciar quantos workers quiser. Cada worker se conecta automaticamente ao Master configurado e começa a pedir tarefas (Heartbeat).

Abra um **novo terminal** e execute:

```bash
python worker.py
```

Você pode abrir vários terminais rodando `python worker.py` simultaneamente para simular uma Farm com múltiplos núcleos de processamento.

---

## ⚙️ Configurações Principais (config.py)

Toda a customização da rede é feita no arquivo `config.py`. Não é necessário mexer nos arquivos `master.py` ou `worker.py` para testes de rede.

- `MASTER_HOST`: Define o IP onde seu Master vai rodar (ex: `"127.0.0.1"` para testes locais, ou o IP da rede `"192.168.0.x"` para comunicar com outros computadores).
- `MASTER_PORT`: Define a porta do Master (Padrão: `5000` ou `8000`).
- `NEIGHBOR_MASTERS`: Uma string contendo a lista de Masters vizinhos separados por vírgula (ex: `"192.168.0.10:8000, 192.168.0.11:8000"`).
- `MASTER_CAPACITY`: Limite de tarefas que a fila do Master suporta antes de declarar saturação e pedir ajuda aos vizinhos.
- `MASTER_ID`: O nome identificador único do seu servidor (Usado para o Painel de Telemetria).

---

## 📂 Estrutura de Arquivos

- `master.py`: Lógica do servidor central, distribuição de tarefas, balanceamento P2P e envio de métricas.
- `worker.py`: Lógica do cliente trabalhador que executa tarefas e gerencia empréstimos M2M.
- `protocol.py`: Funções utilitárias para construir e decodificar as mensagens JSON trafegadas via socket.
- `supervisor_client.py`: Módulo responsável pela coleta de hardwares (CPU, RAM) e envio de TLS Fire-And-Forget para o dashboard central.
- `config.py`: Variáveis de ambiente, portas, IPs e thresholds de saturação.
