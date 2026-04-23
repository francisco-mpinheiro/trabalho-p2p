# P2P com Balanceamento de Carga Dinâmico

Este projeto implementa um sistema distribuído onde um nó **Master** gerencia uma farm de nós **Worker**. O sistema utiliza comunicação TCP com mensagens JSON delimitadas por `\n`.

## Como Configurar e Rodar

Para que o sistema funcione corretamente em máquinas diferentes, siga os passos abaixo:

### 1. Descobrir o IP da Máquina Master
Na máquina que vai rodar o `master.py`, você precisa identificar o endereço IP na rede local:
* **Windows:** Abra o terminal e digite `ipconfig /all`. Procure pelo campo "Endereço IPv4" da sua placa de rede.
* **Linux (Ubuntu/Outros):** Abra o terminal e use o comando `ip a` ou `ifconfig`.

### 2. Ajustar o Código
Com o IP do Master em mãos, abra os arquivos `.py` e atualize a variável `HOST`:

* **No `master.py`:** Altere a variável `HOST` para o IP exato da sua máquina Master (ex: `HOST = '192.168.1.15'`). Isso garante que o servidor faça o bind e escute especificamente nesta interface de rede.
* **No `worker.py`:** Altere a variável `HOST` para o mesmo IP configurado no Master (ex: `HOST = '192.168.1.15'`).

### 3. Execução
Sempre inicie o Master primeiro para que a porta esteja aberta quando o Worker tentar conectar.

**Na Máquina Master:**
```bash
python3 master.py