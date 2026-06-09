# Guia de Execução no Laboratório da Faculdade

Este documento é o guia definitivo de como configurar, rodar e adaptar o nosso projeto P2P nos computadores da faculdade. Siga este passo a passo na hora de testar com os colegas.

---

## 1. Descobrindo o IP da Máquina

Para que as máquinas conversem, cada aluno precisa saber o seu endereço na rede local do laboratório:
1. Abra o Terminal (`CMD` ou `PowerShell`).
2. Digite o comando: `ipconfig`
3. Procure a linha que diz **Endereço IPv4**. Vai ser algo parecido com `192.168.x.x` ou `10.x.x.x`.
4. **Anote o seu IP e pegue o IP dos colegas com quem você vai testar.**

---

## 2. Configurando o seu arquivo `config.py`

Abra o arquivo `config.py` no VS Code. É aqui que toda a mágica da rede acontece.

### A. O seu próprio endereço (Master Host)
Você precisa avisar o seu Master qual é o IP dele para ele escutar a rede da faculdade:
- **Onde mudar:** Na variável `MASTER_HOST`.
- **Como deixar:** Coloque o SEU Endereço IPv4.
```python
# Exemplo se o seu IP for 192.168.1.50
MASTER_HOST = os.getenv('MASTER_HOST', '192.168.1.50') 

# A porta que vamos usar será a 8000
MASTER_PORT = int(os.getenv('MASTER_PORT', '8000'))
```

### B. Os endereços dos seus colegas (Neighbors)
Você precisa dizer ao seu Master para quem ele deve pedir socorro quando a fila dele encher.
- **Onde mudar:** Na variável `NEIGHBOR_MASTERS`.
- **Como deixar:** Coloque uma lista com os IPs dos colegas acompanhados da porta `:8000`.
```python
# Exemplo: Colega 1 (IP final .51) e Colega 2 (IP final .52)
NEIGHBOR_MASTERS = os.getenv('NEIGHBOR_MASTERS', '192.168.1.51:8000,192.168.1.52:8000').split(',')
```
*(Importante: sempre inclua a porta `:8000` junto ao IP dos vizinhos)*

---

## 3. O Professor pediu para NÃO saturar o seu Master?

Se o professor chegar na sua mesa e disser: *"Quero ver o seu Master apenas emprestando workers para os outros, o seu não precisa estourar a fila nem pedir socorro"*.

**A Solução é muito simples:**
Você só precisa aumentar o limite de capacidade do seu Master para um número inalcançável.
- Vá no arquivo `config.py`.
- Procure a variável `MASTER_CAPACITY`.
- Altere para um número gigantesco:
```python
MASTER_CAPACITY = int(os.getenv('MASTER_CAPACITY', '9999999'))
```
Pronto! Seu código continua rodando, vai ajudar os outros se pedirem, mas ele mesmo nunca vai pedir socorro porque a fila dele nunca vai chegar a um milhão.

---

## 4. O Firewall do Windows (Muito Importante 🚨)

Ao rodar o `master.py` pela primeira vez, o Windows pode exibir uma janela do **Firewall do Windows Defender**.
- Você **PRECISA** clicar no botão **Permitir Acesso** (Allow Access).
- Se você cancelar, o Firewall vai bloquear os seus colegas e dar erro de *Timeout* ou *Connection Refused* na tela deles quando tentarem pedir sua ajuda.

---

## 5. Como rodar o projeto

Com o `config.py` salvo, abra dois terminais diferentes na mesma pasta do projeto:

**Terminal 1 (Roda o Master):**
```bash
py master.py
```
*Ele vai mostrar que está escutando no seu IP e Porta 8000.*

**Terminal 2 (Roda os seus Workers):**
```bash
py worker.py
```
*Se você quiser mais poder de processamento local, pode abrir um Terminal 3 e rodar `py worker.py` de novo para ter 2 workers rodando ao mesmo tempo sob o comando do seu Master.*

> **Dica de Teste:** Para ver a saturação e o empréstimo acontecendo de verdade, reduza o `MASTER_CAPACITY` de um dos colegas para `1` ou `2`. Assim que a fila dele passar de 2, ele vai pedir socorro para o seu IP e você verá um worker novo conectando no seu terminal!
