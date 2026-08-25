# Fase 2 — Validação da Convenção de Decodificação

Convenção testada: nibble **low-first** (índice par -> `byte & 0x0F`, índice ímpar -> `byte >> 4`), `null_bitmap` com bit=0 significando dimensão populada.

Evidência: comparação entre o valor decodificado e o texto livre do campo `descriptions` gerado para a mesma persona (dimensões com `attribute_overrides` foram excluídas, pois o override substitui o código original por texto livre).

| índice | dimensão | valor decodificado | trecho da descrição (gabarito) |
|---|---|---|---|
| 2 | gender_identity | Man | Horace is referred to using male pronouns and titles such as 'he' and 'poet' throughout the text. |
| 3 | urbanicity | Dense urban | Horace lived and worked in major ancient urban centers like Rome and Athens, and held a civil service position in the capital. |
| 4 | socioeconomic_band | Upper-middle | Horace came from a family that could afford significant education, achieved the status of equestrian (knight), and received a farm with income from tenants from |
| 6 | english_proficiency | None | Horace lived in the 1st century BC, long before the modern English language existed, so he could not have spoken it. |
| 7 | multilingualism | Trilingual+ | Horace was native to Latin, educated in Greek literature and philosophy in Athens, and grew up in a region of Italy where Italic dialects and Oscan were spoken. |
| 8 | register | Formal / standard | Horace was a highly educated poet who wrote in sophisticated Latin forms, including hexameters and odes, using elegant and versatile language. |
| 9 | domain | Arts & Humanities | Horace was a prominent Roman lyric poet and satirist, recognized as a leading literary figure of the Augustan age. |
| 10 | subject_specialty | Comparative literature | He specialized in adapting Greek lyric forms and themes into Latin poetry, blending Hellenistic aesthetics with Roman social contexts. |
| 11 | domain_characteristics | Practitioner | Horace was a leading Roman lyric poet who actively produced and refined multiple poetic genres, including odes, satires, and epistles, during the Augustan era. |
| 12 | highest_education | Master's | Horace pursued advanced formal education at The Academy in Athens, studying under Epicurean and Stoic philosophers after his initial schooling in Venusia and Ro |
| 13 | academic_field | Humanities | Horace was a professional poet and literary critic whose primary field of study and work was classical literature, rhetoric, and philosophy. |
| 14 | institution_tier | Top-tier research | He studied at The Academy in Athens, the historic institution founded by Plato, which was a premier center for philosophical learning in the ancient world. |
| 15 | research_output | Prolific publisher | Horace was a highly productive poet who published multiple collections of works across various genres, including Satires, Epodes, Odes, and Epistles, establishi |
| 16 | seniority | Lead / Principal | As the leading Roman lyric poet of the Augustan age and a close confidant of the Emperor, Horace held a principal position in the literary and political landsca |
| 17 | company_size | Solo / freelance | Horace operated as an independent poet and writer, relying on patronage from Maecenas and the state rather than employment by a formal organization. |

**Resultado: convenção validada** — os valores decodificados são consistentes com as descrições em linguagem natural.
