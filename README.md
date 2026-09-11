# Hora Livre

Busca de academias brasileiras, com comparação de tendências por dia e hora. Site estático responsivo, API Python, banco SQL SQLite materializado e processamento PySpark/Spark SQL fora da Vercel.

Filtros separados por nome, estado, cidade, bairro e convênio (Wellhub/Gympass, TotalPass ou ambos). Bairro só é preenchido quando consta na fonte OSM; ausência de bairro ou convênio não significa ausência da academia ou recusa do benefício.

Convênios usam `data/benefits.json`, com identificação exata da unidade, fonte oficial e data. O cadastro inicial contém uma confirmação TotalPass da Smart Fit Luxemburgo (Rua Guaicuí, 600). Não há confirmação Wellhub no snapshot inicial. A rotina `pipeline/refresh_benefits.py` revalida páginas já mapeadas; não descobre automaticamente todas as parcerias do Brasil. Páginas alteradas retornam a “não informado”; falhas de rede preservam a última verificação, que expira em 30 dias. Inclusões e negativas precisam de verificação específica da unidade. Os planos não são inferidos.

## O que os dados significam

- Cadastro real do OpenStreetMap, com cobertura parcial. Pode incluir estabelecimentos mal classificados ou desatualizados pela comunidade.
- Cidade e UF preenchidas pela posição em malhas municipais simplificadas do IBGE. Pontos próximos à fronteira podem ter imprecisão; não há endereço inventado.
- O perfil de movimento vem de **uma academia universitária** no Kaggle. Os registros disponíveis são de 2015–2017. É aplicado igualmente a todas as academias brasileiras como referência exploratória de baixa confiança. Não é um modelo validado para o Brasil, uma medição local, percentual de capacidade nem previsão ao vivo.
- Média de pessoas por dia e hora local da fonte, dividida pelo maior valor médio da semana, gerando índice relativo 0–100. O fuso original é preservado ao agrupar.
- O intervalo selecionado pelo usuário é apenas a janela de comparação; não se afirma que a academia esteja aberta. Horários OSM aparecem em sua notação original quando disponíveis.
- Google Maps é um link externo. A API oficial Places não oferece o campo de horários de pico; este projeto não coleta ou atribui dados ao Google.

## Executar localmente

Python 3.12, sem dependências para o servidor e importação convencional:

```sh
python pipeline/serve.py
```

Abra http://127.0.0.1:4173. O snapshot já acompanha o projeto. A API SQL fica em `/api/gyms?q=belo%20horizonte`. A interface usa o snapshot JSON para busca instantânea e também funciona como site estático.

## Atualizar os dados

```sh
python pipeline/fetch_sources.py
python pipeline/geography.py
pip install -r pipeline/requirements.txt
python pipeline/spark_job.py
python pipeline/refresh_benefits.py
python pipeline/build.py
python -m unittest discover -s tests -v
```

PySpark requer Java 17 no ambiente de processamento. Para executar apenas Python, omita o passo Spark e remova um eventual `data/spark_profiles.json` antigo antes de gerar o banco. A execução automática sempre recalcula com Spark.

## Publicar na Vercel

1. Envie este projeto para um repositório GitHub seu, incluindo `dist/data.json`, `data/gyms.db` e `data/kaggle_meta.json`.
2. Importe o repositório na Vercel. Preset **Other**, diretório de saída **dist**, sem comando de build. `vercel.json` configura a função Python e inclui o banco de leitura.
3. Na Vercel, crie um **Deploy Hook** para a branch principal. Salve a URL como secret `VERCEL_DEPLOY_HOOK` no GitHub. Não a coloque em código ou mensagens.
4. Habilite GitHub Actions e permissão de escrita de conteúdo para o workflow. Execute “Atualizar academias e estimativas” manualmente e confira a publicação no painel da Vercel.

O workflow agenda atualização diária às **05:23 de Brasília** (08:23 UTC), com possíveis atrasos do GitHub. Ele consulta fontes, processa com PySpark, valida, grava um novo snapshot e solicita publicação. Falha na coleta ou validação impede substituir os dados publicados. Falha na Vercel fica visível no painel; a aceitação do hook não comprova publicação concluída. Mantenha notificações de falha do GitHub habilitadas e acompanhe os deploys da Vercel. Em repositórios públicos, GitHub pode desativar agendas após inatividade.

**A agenda só fica ativa após configurar repositório, Actions e Vercel.** O código local não agenda tarefas no computador. O site mostra data da consulta e alerta após 48h; consultar novamente o Kaggle não torna recentes observações antigas. Para resultados locais atualizados de movimento, será necessária uma fonte por academia (por exemplo, registros autorizados de entrada ou um provedor com cobertura verificada).

## Fontes e licenças

- [OpenStreetMap / ODbL](https://www.openstreetmap.org/copyright). Os dados derivados do cadastro devem manter atribuição e as obrigações ODbL aplicáveis; o snapshot pode ser baixado em `/data.json`.
- [Kaggle: Crowdedness at the Campus Gym](https://www.kaggle.com/datasets/nsrose7224/crowdedness-at-the-campus-gym).
- [IBGE: malhas geográficas](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3).
- [Google: horários de pico](https://support.google.com/business/answer/6263531?hl=pt-BR).
- [Vercel: Python](https://vercel.com/docs/functions/runtimes/python) e [Deploy Hooks](https://vercel.com/docs/deploy-hooks).

Credenciais não são exigidas para os downloads públicos usados nesta primeira coleta. Mudanças de acesso, esquema ou indisponibilidade das fontes exigem manutenção do pipeline.
