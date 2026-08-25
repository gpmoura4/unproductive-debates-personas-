# Fase 0 — Relatório de Inspeção do Schema MatrAIx

## 1. Sumário geral do schema

- Total de dimensões: 1290
- Número médio de valores categóricos por dimensão: 4.92

| Grupo | Contagem |
|---|---|
| Expertise: Domains | 144 |
| Interests: Media | 81 |
| Interests: Topics | 78 |
| Interests: Culture | 74 |
| Skills: Tools | 69 |
| Worldview: Beliefs | 67 |
| Expertise: Skills | 64 |
| Linguistic: Language | 53 |
| Professional: Industry | 51 |
| Personality: Big Five | 50 |
| Interests: Hobbies | 50 |
| Values & Motivation | 46 |
| Skills: Programming | 44 |
| Interests: Sports | 40 |
| Linguistic: Communication | 37 |
| Interests: Food | 35 |
| Personality: Character | 34 |
| Learning: Academic | 34 |
| Behavior: Preferences | 34 |
| Behavior: Habits | 30 |
| Demographic: Core | 25 |
| Health: Physical | 25 |
| Demographic: Life Events | 24 |
| Developer: AI Workflow Tasks | 12 |
| Developer: Agent Adoption | 11 |
| Developer: Code Maintenance | 10 |
| Developer: AI Adoption | 8 |
| Developer: Technology Evaluation | 8 |
| Risk & Decision | 7 |
| Developer: Open Source Behavior | 7 |
| Developer: Professional Context | 6 |
| State: Emotional | 5 |
| Professional: Career | 4 |
| Personality: Relationships | 4 |
| Developer: Community Behavior | 4 |
| Behavior: Time | 3 |
| Demographic: Cultural | 2 |
| Personality: MBTI | 2 |
| Health: Fitness | 2 |
| Health: Lifestyle | 2 |
| Behavior: Work | 2 |
| Learning: Style | 1 |
| Demographic: Family | 1 |

## 2. Dimensões em Psychology/Worldview/Beliefs

| id | label | valores |
|---|---|---|
| values_priority | Core value | Achievement, Security, Autonomy, Community, Novelty, Tradition |
| political_lean | Political lean | Left, Center-left, Center, Center-right, Right, Apolitical |
| religiosity | Religiosity | Secular, Spiritual, Observant, Devout, Prefer not to say |
| trust_level | Trust level | Trusting, Verifying, Skeptical, Hostile |
| safety_sensitivity | Safety sensitivity | Benign, Sensitive personal, High-stakes (medical/legal/financial), Potentially harmful, Dual-use |
| economic_motivation | Economic motivation | Cost-sensitive, Value-driven, Premium-seeking, Indifferent |
| fam_political_science | Familiarity: Political science | Expert, Proficient, Familiar, Aware, None |
| fam_religious_studies | Familiarity: Religious studies | Expert, Proficient, Familiar, Aware, None |
| topic_spirituality | Interest: Spirituality | Passionate, Interested, Neutral, Indifferent, Averse |
| att_ai | Attitude: AI | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_automation | Attitude: Automation | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_data_privacy | Attitude: Data privacy | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_social_media | Attitude: Social media | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_remote_work | Attitude: Remote work | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_globalization | Attitude: Globalization | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_free_markets | Attitude: Free markets | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_government_regulation | Attitude: Government regulation | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_climate_action | Attitude: Climate action | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_nuclear_energy | Attitude: Nuclear energy | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_renewable_energy | Attitude: Renewable energy | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_genetic_engineering | Attitude: Genetic engineering | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_vaccines | Attitude: Vaccines | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_alternative_medicine | Attitude: Alternative medicine | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_organized_religion | Attitude: Organized religion | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_cryptocurrency | Attitude: Cryptocurrency | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_the_gig_economy | Attitude: The gig economy | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_labor_unions | Attitude: Labor unions | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_higher_education | Attitude: Higher education | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_homeownership | Attitude: Homeownership | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_taking_on_debt | Attitude: Taking on debt | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_risk_taking | Attitude: Risk-taking | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_authority | Attitude: Authority | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_rapid_change | Attitude: Rapid change | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_new_technology | Attitude: New technology | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_brand_loyalty | Attitude: Brand loyalty | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_advertising | Attitude: Advertising | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_influencers | Attitude: Influencers | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_online_reviews | Attitude: Online reviews | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_subscription_services | Attitude: Subscription services | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_open_source | Attitude: Open source | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_surveillance | Attitude: Surveillance | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_self_driving_cars | Attitude: Self-driving cars | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_space_exploration | Attitude: Space exploration | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_universal_basic_income | Attitude: Universal basic income | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_minimalism | Attitude: Minimalism | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_consumerism | Attitude: Consumerism | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_veganism | Attitude: Veganism | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_fast_fashion | Attitude: Fast fashion | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_gun_ownership | Attitude: Gun ownership | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_capital_punishment | Attitude: Capital punishment | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_free_speech | Attitude: Free speech | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_privacy_vs_security | Attitude: Privacy vs security | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_globalized_supply_chains | Attitude: Globalized supply chains | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_working_from_office | Attitude: Working from office | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_four_day_work_week | Attitude: Four-day work week | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_performance_reviews | Attitude: Performance reviews | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_standardized_testing | Attitude: Standardized testing | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_tipping_culture | Attitude: Tipping culture | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_electric_vehicles | Attitude: Electric vehicles | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_public_transit | Attitude: Public transit | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_urban_density | Attitude: Urban density | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| att_gentrification | Attitude: Gentrification | Enthusiast, Positive, Neutral, Skeptical, Opposed |
| acad_political_theory | Subject: Political theory | Passionate, Interested, Neutral, Indifferent, Averse |
| val_family | Value: Family | Core value, Important, Moderate, Minor, Irrelevant |
| val_career_success | Value: Career success | Core value, Important, Moderate, Minor, Irrelevant |
| val_wealth | Value: Wealth | Core value, Important, Moderate, Minor, Irrelevant |
| val_health | Value: Health | Core value, Important, Moderate, Minor, Irrelevant |
| val_personal_freedom | Value: Personal freedom | Core value, Important, Moderate, Minor, Irrelevant |
| val_security_stability | Value: Security & stability | Core value, Important, Moderate, Minor, Irrelevant |
| val_adventure | Value: Adventure | Core value, Important, Moderate, Minor, Irrelevant |
| val_tradition | Value: Tradition | Core value, Important, Moderate, Minor, Irrelevant |
| val_power_influence | Value: Power & influence | Core value, Important, Moderate, Minor, Irrelevant |
| val_achievement | Value: Achievement | Core value, Important, Moderate, Minor, Irrelevant |
| val_creativity_self_expression | Value: Creativity & self-expression | Core value, Important, Moderate, Minor, Irrelevant |
| val_community | Value: Community | Core value, Important, Moderate, Minor, Irrelevant |
| val_spirituality_faith | Value: Spirituality / faith | Core value, Important, Moderate, Minor, Irrelevant |
| val_knowledge_truth | Value: Knowledge & truth | Core value, Important, Moderate, Minor, Irrelevant |
| val_social_status | Value: Social status | Core value, Important, Moderate, Minor, Irrelevant |
| val_independence | Value: Independence | Core value, Important, Moderate, Minor, Irrelevant |
| val_justice_fairness | Value: Justice & fairness | Core value, Important, Moderate, Minor, Irrelevant |
| val_loyalty | Value: Loyalty | Core value, Important, Moderate, Minor, Irrelevant |
| val_sustainability | Value: Sustainability | Core value, Important, Moderate, Minor, Irrelevant |
| val_recognition | Value: Recognition | Core value, Important, Moderate, Minor, Irrelevant |
| val_helping_others | Value: Helping others | Core value, Important, Moderate, Minor, Irrelevant |
| val_personal_growth | Value: Personal growth | Core value, Important, Moderate, Minor, Irrelevant |
| val_fun_enjoyment | Value: Fun & enjoyment | Core value, Important, Moderate, Minor, Irrelevant |
| val_integrity_honesty | Value: Integrity & honesty | Core value, Important, Moderate, Minor, Irrelevant |
| val_beauty_aesthetics | Value: Beauty & aesthetics | Core value, Important, Moderate, Minor, Irrelevant |
| val_order_structure | Value: Order & structure | Core value, Important, Moderate, Minor, Irrelevant |
| val_patriotism | Value: Patriotism | Core value, Important, Moderate, Minor, Irrelevant |
| val_equality | Value: Equality | Core value, Important, Moderate, Minor, Irrelevant |
| val_privacy | Value: Privacy | Core value, Important, Moderate, Minor, Irrelevant |
| schwartz_value_self_direction | Schwartz Self-Direction | Very high, High, Average, Low, Very low |
| schwartz_value_stimulation | Schwartz Stimulation | Very high, High, Average, Low, Very low |
| schwartz_value_hedonism | Schwartz Hedonism | Very high, High, Average, Low, Very low |
| schwartz_value_achievement | Schwartz Achievement | Very high, High, Average, Low, Very low |
| schwartz_value_power | Schwartz Power | Very high, High, Average, Low, Very low |
| schwartz_value_security | Schwartz Security | Very high, High, Average, Low, Very low |
| schwartz_value_conformity | Schwartz Conformity | Very high, High, Average, Low, Very low |
| schwartz_value_tradition | Schwartz Tradition | Very high, High, Average, Low, Very low |
| schwartz_value_benevolence | Schwartz Benevolence | Very high, High, Average, Low, Very low |
| schwartz_value_universalism | Schwartz Universalism | Very high, High, Average, Low, Very low |
| sdt_need_autonomy | SDT Autonomy Need | Very high, High, Average, Low, Very low |
| sdt_need_competence | SDT Competence Need | Very high, High, Average, Low, Very low |
| sdt_need_relatedness | SDT Relatedness Need | Very high, High, Average, Low, Very low |
| mft_care_harm | Moral Foundation Care/Harm | Very high, High, Average, Low, Very low |
| mft_fairness_cheating | Moral Foundation Fairness/Cheating | Very high, High, Average, Low, Very low |
| mft_loyalty_betrayal | Moral Foundation Loyalty/Betrayal | Very high, High, Average, Low, Very low |
| mft_authority_subversion | Moral Foundation Authority/Subversion | Very high, High, Average, Low, Very low |
| mft_sanctity_degradation | Moral Foundation Sanctity/Degradation | Very high, High, Average, Low, Very low |
| mft_liberty_oppression | Moral Foundation Liberty/Oppression | Very high, High, Average, Low, Very low |
| need_for_cognition | Need for Cognition | Very high, High, Average, Low, Very low |
| dospert_health_safety_risk_tolerance | DOSPERT Health/Safety Risk Tolerance | Very high, High, Average, Low, Very low |

## 3. Dimensões candidatas por term-match

| id | label | grupo | termos matched |
|---|---|---|---|
| institution_tier | Institution tier | Learning: Academic | institution |
| major_life_events | Major life events | Demographic: Life Events | immigration |
| values_priority | Core value | Values & Motivation | value, motivation, autonomy |
| political_lean | Political lean | Worldview: Beliefs | political, left, right, worldview, belief |
| religiosity | Religiosity | Values & Motivation | value, religion, spiritual, secular, motivation |
| trust_level | Trust level | Worldview: Beliefs | worldview, belief, trust |
| safety_sensitivity | Safety sensitivity | Worldview: Beliefs | worldview, belief |
| economic_motivation | Economic motivation | Values & Motivation | value, motivation |
| fam_political_science | Familiarity: Political science | Worldview: Beliefs | political, worldview, belief |
| fam_ethics | Familiarity: Ethics | Expertise: Domains | ethics |
| fam_religious_studies | Familiarity: Religious studies | Worldview: Beliefs | worldview, belief, religious |
| topic_religion | Interest: Religion | Interests: Topics | religion |
| topic_spirituality | Interest: Spirituality | Worldview: Beliefs | worldview, belief, spiritual |
| att_ai | Attitude: AI | Worldview: Beliefs | worldview, belief |
| att_automation | Attitude: Automation | Worldview: Beliefs | worldview, belief |
| att_data_privacy | Attitude: Data privacy | Worldview: Beliefs | worldview, belief |
| att_social_media | Attitude: Social media | Worldview: Beliefs | worldview, belief |
| att_remote_work | Attitude: Remote work | Worldview: Beliefs | worldview, belief |
| att_globalization | Attitude: Globalization | Worldview: Beliefs | worldview, belief |
| att_immigration | Attitude: Immigration | Demographic: Cultural | immigration |
| att_free_markets | Attitude: Free markets | Worldview: Beliefs | worldview, belief |
| att_government_regulation | Attitude: Government regulation | Worldview: Beliefs | worldview, belief, government |
| att_climate_action | Attitude: Climate action | Worldview: Beliefs | worldview, belief |
| att_nuclear_energy | Attitude: Nuclear energy | Worldview: Beliefs | worldview, belief |
| att_renewable_energy | Attitude: Renewable energy | Worldview: Beliefs | worldview, belief |
| att_genetic_engineering | Attitude: Genetic engineering | Worldview: Beliefs | worldview, belief |
| att_vaccines | Attitude: Vaccines | Worldview: Beliefs | worldview, belief |
| att_alternative_medicine | Attitude: Alternative medicine | Worldview: Beliefs | worldview, belief |
| att_organized_religion | Attitude: Organized religion | Worldview: Beliefs | worldview, belief, religion |
| att_traditional_gender_roles | Attitude: Traditional gender roles | Demographic: Core | traditional |
| att_cryptocurrency | Attitude: Cryptocurrency | Worldview: Beliefs | worldview, belief |
| att_the_gig_economy | Attitude: The gig economy | Worldview: Beliefs | worldview, belief |
| att_labor_unions | Attitude: Labor unions | Worldview: Beliefs | worldview, belief |
| att_higher_education | Attitude: Higher education | Worldview: Beliefs | worldview, belief |
| att_homeownership | Attitude: Homeownership | Worldview: Beliefs | worldview, belief |
| att_taking_on_debt | Attitude: Taking on debt | Worldview: Beliefs | worldview, belief |
| att_risk_taking | Attitude: Risk-taking | Worldview: Beliefs | worldview, belief |
| att_authority | Attitude: Authority | Worldview: Beliefs | worldview, belief, authority |
| att_rapid_change | Attitude: Rapid change | Worldview: Beliefs | worldview, belief |
| att_new_technology | Attitude: New technology | Worldview: Beliefs | worldview, belief |
| att_brand_loyalty | Attitude: Brand loyalty | Worldview: Beliefs | worldview, belief |
| att_advertising | Attitude: Advertising | Worldview: Beliefs | worldview, belief |
| att_influencers | Attitude: Influencers | Worldview: Beliefs | worldview, belief |
| att_online_reviews | Attitude: Online reviews | Worldview: Beliefs | worldview, belief |
| att_subscription_services | Attitude: Subscription services | Worldview: Beliefs | worldview, belief |
| att_open_source | Attitude: Open source | Worldview: Beliefs | worldview, belief |
| att_surveillance | Attitude: Surveillance | Worldview: Beliefs | worldview, belief |
| att_self_driving_cars | Attitude: Self-driving cars | Worldview: Beliefs | worldview, belief |
| att_space_exploration | Attitude: Space exploration | Worldview: Beliefs | worldview, belief |
| att_universal_basic_income | Attitude: Universal basic income | Worldview: Beliefs | worldview, belief |
| att_minimalism | Attitude: Minimalism | Worldview: Beliefs | worldview, belief |
| att_consumerism | Attitude: Consumerism | Worldview: Beliefs | worldview, belief |
| att_veganism | Attitude: Veganism | Worldview: Beliefs | worldview, belief |
| att_fast_fashion | Attitude: Fast fashion | Worldview: Beliefs | worldview, belief |
| att_gun_ownership | Attitude: Gun ownership | Worldview: Beliefs | worldview, belief |
| att_capital_punishment | Attitude: Capital punishment | Worldview: Beliefs | worldview, belief |
| att_free_speech | Attitude: Free speech | Worldview: Beliefs | worldview, belief |
| att_privacy_vs_security | Attitude: Privacy vs security | Worldview: Beliefs | worldview, belief |
| att_globalized_supply_chains | Attitude: Globalized supply chains | Worldview: Beliefs | worldview, belief |
| att_working_from_office | Attitude: Working from office | Worldview: Beliefs | worldview, belief |
| att_four_day_work_week | Attitude: Four-day work week | Worldview: Beliefs | worldview, belief |
| att_performance_reviews | Attitude: Performance reviews | Worldview: Beliefs | worldview, belief |
| att_standardized_testing | Attitude: Standardized testing | Worldview: Beliefs | worldview, belief |
| att_tipping_culture | Attitude: Tipping culture | Worldview: Beliefs | worldview, belief |
| att_electric_vehicles | Attitude: Electric vehicles | Worldview: Beliefs | worldview, belief |
| att_public_transit | Attitude: Public transit | Worldview: Beliefs | worldview, belief |
| att_urban_density | Attitude: Urban density | Worldview: Beliefs | worldview, belief |
| att_gentrification | Attitude: Gentrification | Worldview: Beliefs | worldview, belief |
| ind_government | Industry: Government | Professional: Industry | government |
| big5_liberalism | Liberalism | Personality: Big Five | liberal |
| big5_trust | Trust | Personality: Big Five | trust |
| big5_morality | Morality | Personality: Big Five | moral |
| lstyle_banking_style | Banking style | Interests: Culture | traditional |
| health_dietary_restriction | Dietary restriction | Health: Physical | religious |
| acad_political_theory | Subject: Political theory | Worldview: Beliefs | political, worldview, belief |
| trait_spirituality | Character: Spirituality | Personality: Character | spiritual |
| val_family | Value: Family | Values & Motivation | value, motivation |
| val_career_success | Value: Career success | Values & Motivation | value, motivation |
| val_wealth | Value: Wealth | Values & Motivation | value, motivation |
| val_health | Value: Health | Values & Motivation | value, motivation |
| val_personal_freedom | Value: Personal freedom | Values & Motivation | value, motivation |
| val_security_stability | Value: Security & stability | Values & Motivation | value, motivation |
| val_adventure | Value: Adventure | Values & Motivation | value, motivation |
| val_tradition | Value: Tradition | Values & Motivation | value, motivation |
| val_power_influence | Value: Power & influence | Values & Motivation | value, motivation |
| val_achievement | Value: Achievement | Values & Motivation | value, motivation |
| val_creativity_self_expression | Value: Creativity & self-expression | Values & Motivation | value, motivation |
| val_community | Value: Community | Values & Motivation | value, motivation |
| val_spirituality_faith | Value: Spirituality / faith | Values & Motivation | value, faith, spiritual, motivation |
| val_knowledge_truth | Value: Knowledge & truth | Values & Motivation | value, motivation |
| val_social_status | Value: Social status | Values & Motivation | value, motivation |
| val_independence | Value: Independence | Values & Motivation | value, motivation |
| val_justice_fairness | Value: Justice & fairness | Values & Motivation | value, motivation |
| val_loyalty | Value: Loyalty | Values & Motivation | value, motivation |
| val_sustainability | Value: Sustainability | Values & Motivation | value, motivation |
| val_recognition | Value: Recognition | Values & Motivation | value, motivation |
| val_helping_others | Value: Helping others | Values & Motivation | value, motivation |
| val_personal_growth | Value: Personal growth | Values & Motivation | value, motivation |
| val_fun_enjoyment | Value: Fun & enjoyment | Values & Motivation | value, motivation |
| val_integrity_honesty | Value: Integrity & honesty | Values & Motivation | value, motivation |
| val_beauty_aesthetics | Value: Beauty & aesthetics | Values & Motivation | value, motivation |
| val_order_structure | Value: Order & structure | Values & Motivation | value, motivation |
| val_patriotism | Value: Patriotism | Values & Motivation | value, motivation |
| val_equality | Value: Equality | Values & Motivation | value, motivation |
| val_privacy | Value: Privacy | Values & Motivation | value, motivation |
| habit_procrasti_cleaning | Habit: Procrasti-cleaning | Behavior: Habits | leaning |
| pref_work_location | Office vs remote | Behavior: Work | leaning |
| pref_team_vs_solo | Team vs solo work | Behavior: Preferences | leaning |
| pref_routine_vs_variety | Routine vs variety | Behavior: Preferences | leaning |
| pref_speed_vs_accuracy | Speed vs accuracy | Behavior: Preferences | leaning |
| pref_quality_vs_quantity | Quality vs quantity | Behavior: Preferences | leaning |
| pref_logic_vs_intuition | Logic vs intuition | Behavior: Preferences | leaning |
| pref_save_vs_spend | Save vs spend | Behavior: Preferences | leaning |
| pref_indoor_vs_outdoor | Indoor vs outdoor | Behavior: Preferences | leaning |
| pref_big_group_vs_one_on_one | Big group vs one-on-one | Behavior: Preferences | leaning |
| pref_novelty_vs_familiarity | Novelty vs familiarity | Behavior: Preferences | leaning |
| pref_detail_brief_vs_full | Brief vs full detail | Behavior: Preferences | leaning |
| pref_stability_vs_change | Stability vs change | Behavior: Preferences | leaning |
| demo_housing_status | Housing status | Demographic: Core | right |
| demo_religion_affiliation | Religious affiliation | Demographic: Core | religion, religious, spiritual, traditional |
| demo_political_engagement | Political engagement | Demographic: Core | political |
| lifex_geographic_mobility | Geographic mobility | Demographic: Life Events | left |
| lifex_travel_breadth | Travel breadth | Demographic: Life Events | left |
| lifex_education_journey | Education journey | Demographic: Life Events | traditional |
| lifex_immigration_generation | Immigration generation | Demographic: Life Events | immigration |
| lifex_faith_journey | Faith journey | Demographic: Life Events | left, faith, secular |
| lifex_turning_point | Defining turning point | Demographic: Life Events | spiritual |
| bfi2_facet_trust | BFI-2 Trust | Personality: Big Five | trust |
| schwartz_value_self_direction | Schwartz Self-Direction | Values & Motivation | value, motivation |
| schwartz_value_stimulation | Schwartz Stimulation | Values & Motivation | value, motivation |
| schwartz_value_hedonism | Schwartz Hedonism | Values & Motivation | value, motivation |
| schwartz_value_achievement | Schwartz Achievement | Values & Motivation | value, motivation |
| schwartz_value_power | Schwartz Power | Values & Motivation | value, motivation |
| schwartz_value_security | Schwartz Security | Values & Motivation | value, motivation |
| schwartz_value_conformity | Schwartz Conformity | Values & Motivation | value, motivation |
| schwartz_value_tradition | Schwartz Tradition | Values & Motivation | value, religious, motivation |
| schwartz_value_benevolence | Schwartz Benevolence | Values & Motivation | value, motivation |
| schwartz_value_universalism | Schwartz Universalism | Values & Motivation | value, motivation |
| sdt_need_autonomy | SDT Autonomy Need | Values & Motivation | value, motivation, autonomy |
| sdt_need_competence | SDT Competence Need | Values & Motivation | value, motivation |
| sdt_need_relatedness | SDT Relatedness Need | Values & Motivation | value, motivation |
| mft_care_harm | Moral Foundation Care/Harm | Worldview: Beliefs | worldview, belief, moral |
| mft_fairness_cheating | Moral Foundation Fairness/Cheating | Worldview: Beliefs | worldview, belief, moral |
| mft_loyalty_betrayal | Moral Foundation Loyalty/Betrayal | Worldview: Beliefs | worldview, belief, moral |
| mft_authority_subversion | Moral Foundation Authority/Subversion | Worldview: Beliefs | worldview, belief, moral, authority |
| mft_sanctity_degradation | Moral Foundation Sanctity/Degradation | Worldview: Beliefs | worldview, belief, moral |
| mft_liberty_oppression | Moral Foundation Liberty/Oppression | Worldview: Beliefs | worldview, belief, moral |
| need_for_cognition | Need for Cognition | Values & Motivation | value, motivation |
| dospert_health_safety_risk_tolerance | DOSPERT Health/Safety Risk Tolerance | Worldview: Beliefs | worldview, belief |
| interpersonal_agency_dominance | Interpersonal Agency/Dominance | Personality: Relationships | agency |
| coding_ai_output_trust | Coding AI output trust | Developer: AI Adoption | trust |
| coding_agent_autonomy_preference | Coding agent autonomy preference | Developer: Agent Adoption | autonomy |
| coding_tool_ethics_blocker | Coding tool ethics blocker | Developer: Technology Evaluation | ethics |
| human_help_boundary_for_ai_coding | Human help boundary for AI coding | Developer: AI Adoption | ethics, trust |
| future_developer_skill_belief | Future developer skill belief | Developer: AI Adoption | belief |

## 4. Dimensões prioritárias para Fase 1

- **political_lean** — Political lean (grupo: Worldview: Beliefs, termos: political, left, right, worldview, belief)
- **religiosity** — Religiosity (grupo: Values & Motivation, termos: value, religion, spiritual, secular, motivation)
- **trust_level** — Trust level (grupo: Worldview: Beliefs, termos: worldview, belief, trust)
- **safety_sensitivity** — Safety sensitivity (grupo: Worldview: Beliefs, termos: worldview, belief)
- **fam_political_science** — Familiarity: Political science (grupo: Worldview: Beliefs, termos: political, worldview, belief)
- **fam_religious_studies** — Familiarity: Religious studies (grupo: Worldview: Beliefs, termos: worldview, belief, religious)
- **topic_religion** — Interest: Religion (grupo: Interests: Topics, termos: religion)
- **topic_spirituality** — Interest: Spirituality (grupo: Worldview: Beliefs, termos: worldview, belief, spiritual)
- **att_ai** — Attitude: AI (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_automation** — Attitude: Automation (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_data_privacy** — Attitude: Data privacy (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_social_media** — Attitude: Social media (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_remote_work** — Attitude: Remote work (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_globalization** — Attitude: Globalization (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_free_markets** — Attitude: Free markets (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_government_regulation** — Attitude: Government regulation (grupo: Worldview: Beliefs, termos: worldview, belief, government)
- **att_climate_action** — Attitude: Climate action (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_nuclear_energy** — Attitude: Nuclear energy (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_renewable_energy** — Attitude: Renewable energy (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_genetic_engineering** — Attitude: Genetic engineering (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_vaccines** — Attitude: Vaccines (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_alternative_medicine** — Attitude: Alternative medicine (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_organized_religion** — Attitude: Organized religion (grupo: Worldview: Beliefs, termos: worldview, belief, religion)
- **att_cryptocurrency** — Attitude: Cryptocurrency (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_the_gig_economy** — Attitude: The gig economy (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_labor_unions** — Attitude: Labor unions (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_higher_education** — Attitude: Higher education (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_homeownership** — Attitude: Homeownership (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_taking_on_debt** — Attitude: Taking on debt (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_risk_taking** — Attitude: Risk-taking (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_authority** — Attitude: Authority (grupo: Worldview: Beliefs, termos: worldview, belief, authority)
- **att_rapid_change** — Attitude: Rapid change (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_new_technology** — Attitude: New technology (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_brand_loyalty** — Attitude: Brand loyalty (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_advertising** — Attitude: Advertising (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_influencers** — Attitude: Influencers (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_online_reviews** — Attitude: Online reviews (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_subscription_services** — Attitude: Subscription services (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_open_source** — Attitude: Open source (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_surveillance** — Attitude: Surveillance (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_self_driving_cars** — Attitude: Self-driving cars (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_space_exploration** — Attitude: Space exploration (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_universal_basic_income** — Attitude: Universal basic income (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_minimalism** — Attitude: Minimalism (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_consumerism** — Attitude: Consumerism (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_veganism** — Attitude: Veganism (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_fast_fashion** — Attitude: Fast fashion (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_gun_ownership** — Attitude: Gun ownership (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_capital_punishment** — Attitude: Capital punishment (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_free_speech** — Attitude: Free speech (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_privacy_vs_security** — Attitude: Privacy vs security (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_globalized_supply_chains** — Attitude: Globalized supply chains (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_working_from_office** — Attitude: Working from office (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_four_day_work_week** — Attitude: Four-day work week (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_performance_reviews** — Attitude: Performance reviews (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_standardized_testing** — Attitude: Standardized testing (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_tipping_culture** — Attitude: Tipping culture (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_electric_vehicles** — Attitude: Electric vehicles (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_public_transit** — Attitude: Public transit (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_urban_density** — Attitude: Urban density (grupo: Worldview: Beliefs, termos: worldview, belief)
- **att_gentrification** — Attitude: Gentrification (grupo: Worldview: Beliefs, termos: worldview, belief)
- **big5_trust** — Trust (grupo: Personality: Big Five, termos: trust)
- **health_dietary_restriction** — Dietary restriction (grupo: Health: Physical, termos: religious)
- **acad_political_theory** — Subject: Political theory (grupo: Worldview: Beliefs, termos: political, worldview, belief)
- **habit_procrasti_cleaning** — Habit: Procrasti-cleaning (grupo: Behavior: Habits, termos: leaning)
- **pref_work_location** — Office vs remote (grupo: Behavior: Work, termos: leaning)
- **pref_team_vs_solo** — Team vs solo work (grupo: Behavior: Preferences, termos: leaning)
- **pref_routine_vs_variety** — Routine vs variety (grupo: Behavior: Preferences, termos: leaning)
- **pref_speed_vs_accuracy** — Speed vs accuracy (grupo: Behavior: Preferences, termos: leaning)
- **pref_quality_vs_quantity** — Quality vs quantity (grupo: Behavior: Preferences, termos: leaning)
- **pref_logic_vs_intuition** — Logic vs intuition (grupo: Behavior: Preferences, termos: leaning)
- **pref_save_vs_spend** — Save vs spend (grupo: Behavior: Preferences, termos: leaning)
- **pref_indoor_vs_outdoor** — Indoor vs outdoor (grupo: Behavior: Preferences, termos: leaning)
- **pref_big_group_vs_one_on_one** — Big group vs one-on-one (grupo: Behavior: Preferences, termos: leaning)
- **pref_novelty_vs_familiarity** — Novelty vs familiarity (grupo: Behavior: Preferences, termos: leaning)
- **pref_detail_brief_vs_full** — Brief vs full detail (grupo: Behavior: Preferences, termos: leaning)
- **pref_stability_vs_change** — Stability vs change (grupo: Behavior: Preferences, termos: leaning)
- **demo_religion_affiliation** — Religious affiliation (grupo: Demographic: Core, termos: religion, religious, spiritual, traditional)
- **demo_political_engagement** — Political engagement (grupo: Demographic: Core, termos: political)
- **bfi2_facet_trust** — BFI-2 Trust (grupo: Personality: Big Five, termos: trust)
- **schwartz_value_tradition** — Schwartz Tradition (grupo: Values & Motivation, termos: value, religious, motivation)
- **mft_care_harm** — Moral Foundation Care/Harm (grupo: Worldview: Beliefs, termos: worldview, belief, moral)
- **mft_fairness_cheating** — Moral Foundation Fairness/Cheating (grupo: Worldview: Beliefs, termos: worldview, belief, moral)
- **mft_loyalty_betrayal** — Moral Foundation Loyalty/Betrayal (grupo: Worldview: Beliefs, termos: worldview, belief, moral)
- **mft_authority_subversion** — Moral Foundation Authority/Subversion (grupo: Worldview: Beliefs, termos: worldview, belief, moral, authority)
- **mft_sanctity_degradation** — Moral Foundation Sanctity/Degradation (grupo: Worldview: Beliefs, termos: worldview, belief, moral)
- **mft_liberty_oppression** — Moral Foundation Liberty/Oppression (grupo: Worldview: Beliefs, termos: worldview, belief, moral)
- **dospert_health_safety_risk_tolerance** — DOSPERT Health/Safety Risk Tolerance (grupo: Worldview: Beliefs, termos: worldview, belief)
- **coding_ai_output_trust** — Coding AI output trust (grupo: Developer: AI Adoption, termos: trust)
- **human_help_boundary_for_ai_coding** — Human help boundary for AI coding (grupo: Developer: AI Adoption, termos: ethics, trust)
- **future_developer_skill_belief** — Future developer skill belief (grupo: Developer: AI Adoption, termos: belief)
