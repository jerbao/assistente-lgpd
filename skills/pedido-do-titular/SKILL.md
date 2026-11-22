---
name: pedido-do-titular
description: Orienta como responder a um pedido de um titular de dados (acesso, correção, eliminação, portabilidade ou revogação do consentimento), com o prazo calculado e os artigos da LGPD. Use quando o usuário disser que um cliente, funcionário ou usuário pediu os próprios dados, pediu para apagar ou corrigir dados, ou perguntar até quando precisa responder a esse pedido.
---

Não faça perguntas ao usuário antes de responder: siga os passos com o que ele disse e deixe claro na resposta o que você supôs.

1. Identifique o tipo de pedido e a data em que ele foi feito. Se o usuário disser "hoje", "ontem" ou não disser a data, chame `tempo_get_current_time` com `timezone` igual a "America/Sao_Paulo" e use a data de hoje.
2. Considere que a empresa é microempresa, empresa de pequeno porte ou startup só se o usuário tiver dito. Se não disse, use o prazo normal e avise que ele dobra para agentes de pequeno porte.
3. Chame `lgpd_lerArtigo` com `documento` "lgpd" e `numero` "18" para ler a lista dos direitos do titular.
4. Se o pedido for de acesso ou confirmação, chame `lgpd_calcularPrazo` com `tipo` "acessoTitular", a data do passo 1 e `pequenoPorte` conforme o passo 2.
5. Se o pedido for de eliminação, chame `lgpd_lerArtigo` com `documento` "lgpd" e `numero` "16", que diz quando os dados podem ser guardados mesmo assim.
6. Se uma ferramenta devolver erro, corrija o argumento uma vez (por exemplo, o formato AAAA-MM-DD da data) e tente de novo. Se ainda falhar, diga qual parte da resposta ficou de fora.

Responda exatamente neste formato:

**Pedido:** tipo do pedido e data considerada
**O que a empresa deve fazer:** até três frases
**Prazo:** data-limite calculada, ou "a LGPD não fixa prazo para este pedido"
**Exceções:** quando a empresa pode recusar o pedido ou guardar os dados, ou "nenhuma"
**Fundamento:** documentos e artigos usados, como (LGPD, arts. 18 e 19)
