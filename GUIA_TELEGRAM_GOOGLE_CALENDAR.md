# Antenna Hair no Telegram com agendamento no Google Calendar

Este guia substitui o Twilio. O canal será o Telegram e, depois da confirmação da cliente, o bot verificará conflitos e criará o evento na agenda Google.

## O que foi implementado

O fluxo agora é:

```text
/start ou oi
  → serviço
  → nome
  → data
  → horário
  → resumo
  → sim
  → verifica conflito no Google Calendar
  → cria evento
```

O bot não cria o evento apenas porque a cliente informou um horário. Ele só acessa a agenda depois de receber `sim` na confirmação.

## 1. Substitua os arquivos do projeto

Na pasta do seu projeto do Windows, substitua ou adicione estes arquivos:

- `salon_logic.py`
- `bot_telegram.py`
- `google_calendar.py`
- `setup_google_calendar.py`
- `test_bot.py`
- `requirements.txt`

Não apague `gemini_client.py` ou `prompt_gemini.txt`.

Os novos nomes oficiais são:

- Antenna Hair
- Alongamento — R$ 100,00
- Manutenção — R$ 90,00
- Esmaltação em gel — R$ 70,00
- Blindagem — R$ 70,00
- Banho de gel — R$ 70,00
- Remoção — R$ 50,00
- Unhas tradicionais — R$ 30,00
- Cutilagem — R$ 20,00

## 2. Instale as dependências

Abra o Prompt de Comando dentro da pasta do projeto. O caminho deve ser parecido com:

```text
C:\Users\LENOVO\Downloads\antena-hair-bot\antena-hair-bot>
```

Ative o ambiente virtual:

```cmd
.venv\Scripts\activate
```

Instale as dependências:

```cmd
python -m pip install -r requirements.txt
```

## 3. Crie o projeto no Google Cloud

Faça esta parte no navegador:

1. Acesse https://console.cloud.google.com/
2. Entre com a mesma conta Google cuja agenda será usada.
3. No topo, clique no seletor de projeto.
4. Clique em **Novo projeto**.
5. Use um nome como `antena-hair-calendar`.
6. Clique em **Criar**.
7. Selecione o projeto recém-criado.

## 4. Ative a Google Calendar API

1. No menu do Google Cloud, abra **APIs e serviços**.
2. Clique em **Biblioteca**.
3. Pesquise por `Google Calendar API`.
4. Abra o resultado oficial.
5. Clique em **Ativar**.

## 5. Configure a tela de consentimento

1. Abra **APIs e serviços → Tela de consentimento OAuth**.
2. Se aparecer uma escolha, selecione **Externo**.
3. Informe o nome do aplicativo: `Antenna Hair Chatbot`.
4. Informe seu e-mail como e-mail de suporte e contato do desenvolvedor.
5. Salve e avance pelas etapas.
6. Em **Usuários de teste**, adicione o mesmo e-mail que possui a agenda.
7. Salve.

O aplicativo será usado apenas pela sua conta. Não publique as credenciais.

## 6. Crie as credenciais OAuth

1. Abra **APIs e serviços → Credenciais**.
2. Clique em **Criar credenciais**.
3. Escolha **ID do cliente OAuth**.
4. Se for solicitado o tipo de aplicativo, escolha **Aplicativo para computador**.
5. Dê um nome como `Antenna Hair Desktop`.
6. Clique em **Criar**.
7. Clique no botão para baixar o JSON.

Renomeie o arquivo baixado para:

```text
credentials.json
```

Coloque esse arquivo na mesma pasta de `google_calendar.py`, por exemplo:

```text
C:\Users\LENOVO\Downloads\antena-hair-bot\antena-hair-bot\credentials.json
```

Não envie esse arquivo para outras pessoas nem publique em repositório.

## 7. Autorize o acesso à agenda

Com o ambiente virtual ativo, execute:

```cmd
python setup_google_calendar.py
```

Uma janela do navegador será aberta. Escolha a conta Google que possui sua agenda e autorize o acesso solicitado.

Se aparecer uma tela dizendo que o aplicativo não foi verificado:

1. Clique em **Avançado**.
2. Clique em **Ir para Antenna Hair Chatbot (não seguro)**, se essa opção aparecer.
3. Continue e permita o acesso ao Google Calendar.

Isso acontece porque o aplicativo é seu e ainda não foi enviado para verificação pública.

Quando terminar, o terminal deverá mostrar:

```text
Autorização concluída.
O arquivo token.json foi criado.
```

O arquivo `token.json` é privado. Não publique e não envie para ninguém.

## 8. Configure o token do Telegram

No mesmo Prompt de Comando:

```cmd
set TELEGRAM_BOT_TOKEN=COLE_AQUI_O_TOKEN_DO_BOTFATHER
```

Se você usar o Gemini:

```cmd
set GEMINI_API_KEY=COLE_AQUI_A_CHAVE_DO_GEMINI
```

Não coloque aspas e não compartilhe os valores.

## 9. Execute os testes locais

Antes de iniciar o Telegram:

```cmd
python test_bot.py
python -m py_compile salon_logic.py google_calendar.py bot_telegram.py setup_google_calendar.py
```

O resultado esperado é:

```text
Todos os testes passaram.
```

## 10. Inicie o bot

Execute:

```cmd
python bot_telegram.py
```

Não feche essa janela. Ela precisa permanecer aberta para o bot responder.

No Telegram, abra seu bot e envie:

```text
/start
```

Depois teste exatamente nesta sequência:

```text
quero um alongameto
Ana
30/11/2026
14h
sim
```

O bot deverá:

1. reconhecer `alongameto` como Alongamento;
2. mostrar o preço de R$ 100,00;
3. pedir o nome;
4. pedir a data;
5. pedir o horário;
6. mostrar o resumo;
7. verificar a agenda;
8. criar um evento de 2 horas no Google Calendar;
9. enviar a confirmação no Telegram.

## 11. Teste de horário ocupado

Faça um primeiro agendamento para um horário de teste. Depois tente agendar outro serviço no mesmo horário.

O bot deverá informar que o horário está ocupado e não deverá criar um segundo evento naquele intervalo.

A duração utilizada é:

- Alongamento: 120 minutos;
- Manutenção: 90 minutos;
- Esmaltação em gel: 60 minutos;
- Blindagem: 90 minutos;
- Banho de gel: 90 minutos;
- Remoção: 45 minutos;
- Unhas tradicionais: 60 minutos;
- Cutilagem: 30 minutos.

Se algum tempo estiver diferente na prática do salão, altere a duração em `salon_logic.py`.

## 12. Comandos disponíveis

```text
/start       reinicia e mostra o menu
/cancelar    cancela o pedido atual
menu         reinicia e mostra os serviços
```

## 13. Se ocorrer um erro

### `credentials.json não encontrado`

O arquivo não está na mesma pasta de `google_calendar.py`. Copie-o para a pasta correta e execute novamente:

```cmd
python setup_google_calendar.py
```

### `Access blocked`

Verifique se o e-mail foi adicionado como usuário de teste na tela de consentimento OAuth e se você está entrando com a conta correta.

### O bot responde, mas não cria evento

Confirme se:

- `python setup_google_calendar.py` terminou com sucesso;
- o arquivo `token.json` existe;
- você autorizou a mesma conta que possui a agenda;
- o terminal não mostrou uma mensagem de erro.

### O bot não inicia

Verifique se o ambiente virtual está ativo e execute:

```cmd
python -m pip install -r requirements.txt
```

Depois:

```cmd
python bot_telegram.py
```

## 14. Segurança

Nunca publique estes arquivos ou valores:

```text
credentials.json
token.json
TELEGRAM_BOT_TOKEN
GEMINI_API_KEY
```

O arquivo `token.json` concede acesso à agenda para o programa. Se ele for exposto, apague o acesso do aplicativo na sua conta Google e refaça a autorização.

## 15. Limitação atual

O bot cria eventos diretamente na agenda Google somente enquanto o programa estiver executando no computador. Para funcionar 24 horas, será necessário hospedar o bot em um servidor persistente e transferir as credenciais de forma segura. Para a apresentação, executar o terminal durante a demonstração é suficiente.
