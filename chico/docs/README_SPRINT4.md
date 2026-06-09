# Guia de Apresentação - Sprint 04 (Dashboard)

Este guia foi feito para você não precisar tocar em código durante a apresentação. Tudo o que precisa ser ajustado para a Sprint 04 (Telemetria do Supervisor) se resolve apenas alterando valores no arquivo **`config.py`**.

---

## 1. O Identificador do seu Servidor no Dashboard
A especificação exige que o servidor seja identificado por um `server_uuid` específico dado pelo professor (ex: `michel_1`, `michel_2`).
- **Onde mudar:** No arquivo `config.py`, na variável `MASTER_ID`.
- **Exemplo:**
  ```python
  MASTER_ID = os.getenv('MASTER_ID', 'michel_1')
  ```
> **Nota:** É esse valor que vai aparecer lá no painel central da faculdade, então pergunte ao professor qual nome ele quer que você coloque antes de rodar.

## 2. Parâmetros de Alerta (Stress Tests do Painel)
O Dashboard possui alertas visuais se a CPU, Memória ou Tarefas ultrapassarem limites. Nós deixamos esses limites facilmente configuráveis.
Se o professor pedir para ver os alertas no painel, altere no `config.py`:
- `MAX_TASK`: Número máximo de tarefas para considerar fila cheia (Default: 100).
- `WARN_CPU_PERCENT`: Porcentagem da CPU para ficar vermelho no painel (Default: 85).
- `WARN_MEMORY_PERCENT`: Porcentagem da Memória (Default: 85).
- `RELEASE_TASK`: Quando a fila cair abaixo disso, ele devolve workers (Default: 60).

## 3. Conexão de Rede Local (Revisão da Sprint 3)
A telemetria (Sprint 4) envia dados para a nuvem usando a internet (`nuted-ia.dev:443`), então **sua máquina precisa ter internet**.
Mas para a sua simulação do P2P funcionar entre você e seus colegas, revise os IPs da rede da faculdade:
- `MASTER_HOST`: Coloque o SEU IP local (ex: `192.168.x.x`).
- `NEIGHBOR_MASTERS`: Coloque os IPs dos colegas com a porta `:8000` (ex: `192.168.x.y:8000`).

## 4. O que o código faz nos bastidores? (Caso ele pergunte)
Se o professor perguntar como você implementou:
1. **Não usamos HTTP:** Diga que usamos a biblioteca `asyncio` e `ssl` pura do Python para abrir um `socket TCP TLS` direto na porta 443 do `nuted-ia.dev`.
2. **Fire and Forget:** Diga que o seu Master envia o JSON a cada 10 segundos e fecha a conexão no mesmo milissegundo, sem dar `recv()` ou aguardar resposta.
3. **Leitura de Hardware:** Diga que você usou a biblioteca `psutil` para ler a CPU e a RAM real do Windows/Linux, e cruzou isso com os dados do próprio Master (tamanho da fila de tarefas, número de workers nativos e emprestados). Tudo de forma totalmente assíncrona.

Boa Apresentação! 🚀
