[English](README.md) | **Português (BR)**

# FS22 Beacon

Controle a luz USB rotativa do Farming Simulator 22 pelo Windows, e faça ela piscar e girar quando o Zabbix reportar um problema de severidade **Disaster**.

## Conteúdo

- `beacon.py`: controla a luz (girar, piscar, desligar). Usa só a biblioteca padrão do Python, sem instalar nada.
- `zabbix_monitor.py`: consulta a API do Zabbix a cada 60 segundos. Enquanto houver um problema Disaster ativo, a luz alterna entre piscar e girar. Quando o problema é resolvido, a luz desliga.

## Requisitos

- Windows 10 ou 11
- Python 3.x (testado com 3.12)
- A luz USB do Farming Simulator 22 conectada ao PC (VID `340D`, PID `1710`)
- Para o monitor: um servidor Zabbix (testado com 8.0) e um token de API com permissão **somente leitura**

## Controlando a luz

```
python beacon.py spin 10    # gira por 10 segundos
python beacon.py flash 10   # pisca por 10 segundos
python beacon.py stop       # desliga
```

## Usando com o Zabbix

1. Copie `zabbix_url.example.txt` para `zabbix_url.txt` e coloque a URL da API, por exemplo `https://seu-servidor/zabbix/api_jsonrpc.php`.
2. Copie `zabbix_token.example.txt` para `zabbix_token.txt` e coloque o token da API. Crie o token em *Administração → Tokens de API*, usando um usuário com acesso de leitura.
3. Teste a conexão sem acender a luz:

   ```
   python zabbix_monitor.py --once
   ```

4. Rode o monitor:

   ```
   python zabbix_monitor.py
   ```

Os arquivos `zabbix_url.txt` e `zabbix_token.txt` estão no `.gitignore`, então a URL e o token nunca são publicados.

## Como funciona

- O monitor faz apenas conexões HTTPS de saída para a API do Zabbix. Não abre portas no PC.
- A luz é controlada por USB HID, com os mesmos bytes de comando que o jogo usa. As sequências de bytes vêm do projeto [blinkybeacon](https://github.com/duckfullstop/blinkybeacon).
- A luz espera relatórios de saída de 65 bytes; o script completa cada comando com zeros até esse tamanho.

## Limitações

- Só reage a problemas de severidade **Disaster**.
- Pode haver até 60 segundos de atraso entre o problema aparecer e a luz reagir.
- O monitor só funciona enquanto estiver rodando e o PC estiver ligado com a luz conectada.
- Não testado com outros modelos de luz.

## Segurança

Nunca publique o seu `zabbix_token.txt`. Se um token vazar, revogue-o no Zabbix e crie outro.
