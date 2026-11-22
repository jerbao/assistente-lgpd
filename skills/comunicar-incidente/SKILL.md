---
name: comunicar-incidente
description: Avalia se um incidente de segurança com dados pessoais (vazamento, invasão, acesso indevido, perda de arquivo ou equipamento) precisa ser comunicado à ANPD e aos titulares, calcula os prazos e lista o que cada comunicação deve conter. Use quando o usuário disser que houve um vazamento, invasão, ataque, ransomware ou perda de dados e perguntar se precisa avisar alguém, até quando ou o que informar.
---

1. Identifique quais dados foram afetados, quantas pessoas e a data em que a empresa soube que o incidente afetou dados pessoais. Se o usuário disser "hoje", "ontem" ou não disser a data, chame `tempo_get_current_time` com `timezone` igual a "America/Sao_Paulo" e calcule a data a partir dela.
2. Chame `lgpd_lerArtigo` com `documento` "incidente" e `numero` "5". O incidente precisa ser comunicado quando puder afetar significativamente interesses e direitos fundamentais dos titulares e, ao mesmo tempo, envolver pelo menos um destes: dados sensíveis, dados de crianças, adolescentes ou idosos, dados financeiros, dados de autenticação (senhas), dados sob sigilo ou dados em larga escala. Diga qual critério se aplica ao caso, ou que nenhum se aplica.
3. Se nenhum critério se aplicar, não calcule prazos. Chame `lgpd_lerArtigo` com `documento` "incidente" e `numero` "10" e diga que a empresa não precisa comunicar, mas deve registrar o incidente e guardar o registro por cinco anos.
4. Se algum critério se aplicar, chame `lgpd_calcularPrazo` duas vezes, com `tipo` "incidenteAnpd" e com `tipo` "incidenteTitular", usando a data do passo 1. Use `pequenoPorte` true só se o usuário tiver dito que a empresa é microempresa, empresa de pequeno porte ou startup. Se a empresa trata dados sensíveis ou de crianças, adolescentes ou idosos em larga escala, chame `lgpd_lerArtigo` com `documento` "pequenoPorte" e `numero` "4": esse tratamento pode ser de alto risco, e o art. 3º tira dele o prazo em dobro. Na dúvida, diga isso ao usuário e mostre os dois prazos.
5. Chame `lgpd_lerArtigo` com `documento` "incidente" e `numero` "6" para a lista do que a comunicação à ANPD deve conter, e com `numero` "9" para a comunicação aos titulares.
6. Se uma ferramenta devolver erro, corrija o argumento uma vez e tente de novo. Se ainda falhar, diga qual parte da resposta ficou de fora.

Responda exatamente neste formato:

**Precisa comunicar?** sim ou não, e o critério do art. 5º que se aplica
**Prazo para a ANPD:** data-limite e quantos dias úteis, ou "não se aplica"
**Prazo para os titulares:** data-limite e quantos dias úteis, ou "não se aplica"
**O que informar:** os itens principais da comunicação, em uma lista curta
**Registro:** o que deve ser registrado e por quanto tempo
**Fundamento:** documentos e artigos usados, como (Resolução CD/ANPD nº 15/2024, arts. 5º, 6º e 9º)

Quando houver prazo em dias úteis, acrescente ao fim do campo do prazo: "contando só sábados e domingos como não úteis; confira se há feriado no período".
