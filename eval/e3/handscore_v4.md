# E3 v4 hand-score pack (10 notes)

Note 1 is the frozen reference case (A6c2d42955a, data before the whole-cent / ID-order fix). Notes 2–10 are the first nine v4 notes with kept lines (synth-v2 data). For each line mark Supported (Y/N) and Useful (Y/N/Partly) in handscore_v4.csv. SIMULATED money, synthetic data.

## Note 1: AML_TEAM_STRUCTURING (severity 8) · reference (frozen, pre-fix data)

```
[E1] Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.39.
[E2] 10 payments totalling $3,844.39, from 3 agents to 2 merchants.
[E3] agent_03 (team ops): 2 payments, $183.21, each 89.6%–93.6% of its $100.00 approval threshold.
[E4] agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold.
[E5] agent_13 (team ops): 2 payments, $908.57, each 84.9%–96.8% of its $500.00 approval threshold.
[E6] First payment 11-09 11:55, last 11-10 16:10: all 10 within 28 h 15 m. Timing label: "over about 28 hours".
[E7] Nimbus Resell (compute, untrusted): 6 payments, $1,968.96, from 3 agents.
[E8] Orbit Tools (software, untrusted): 4 payments, $1,875.43, from 1 agent.
[E9] agent_08 switched from Orbit Tools to Nimbus Resell between 11-09 20:41 and 11-10 08:38 (11 h 57 m apart).
[E10] Largest payments: T0002000 $492.57 (agent_08 to Orbit Tools, 11-09 16:57); T0002006 $484.12 (agent_13 to Nimbus Resell, 11-10 09:14); T0002001 $481.19 (agent_08 to Orbit Tools, 11-09 20:41); T0001998 $452.45 (agent_08 to Orbit Tools, 11-09 14:22); T0001999 $449.21 (agent_08 to Orbit Tools, 11-09 11:55).
[E11] Also flagged: A079df76ca6 (new merchant burst, severity 6, not in your queue, raised 11-09 10:49) shares merchant Orbit Tools.
[E12] Also flagged: A951f199d4f (new merchant burst, severity 6, in your queue, raised 11-09 17:07) shares merchant Orbit Tools.
[E13] Also flagged: A1feea23478 (fan in, severity 7, in your queue, raised 11-10 11:27) shares merchant Orbit Tools; agent agent_08.
[E14] Also flagged: Abf045d9327 (new merchant burst, severity 6, in your queue, raised 11-10 13:51) shares merchant Nimbus Resell.
[E15] Also flagged: A83303da58c (structuring, severity 8, not in your queue, raised 11-10 15:17) shares merchant Nimbus Resell, Orbit Tools; agent agent_08.
[E16] Also flagged: Af212a19138 (fan in, severity 7, in your queue, raised 11-10 16:10) shares merchant Nimbus Resell; agent agent_03, agent_08, agent_13.
```

1. **summary** — Multiple agents under the same owner made several payments just under approval thresholds, indicating possible structuring  
   _cites E1: Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.39._
2. **evidence** — Agent 03 payments were close to its low threshold  
   _cites E3: agent_03 (team ops): 2 payments, $183.21, each 89.6%–93.6% of its $100.00 approval threshold._
3. **evidence** — Agent 08 payments repeatedly approached its high threshold  
   _cites E4: agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold._
4. **evidence** — Agent 13 payments also hovered near its threshold  
   _cites E5: agent_13 (team ops): 2 payments, $908.57, each 84.9%–96.8% of its $500.00 approval threshold._
5. **evidence** — The remaining payments went to an untrusted software merchant  
   _cites E8: Orbit Tools (software, untrusted): 4 payments, $1,875.43, from 1 agent._
6. **open_questions** — Do any of the agents have prior structuring alerts or known risk factors?  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $183.21, each 89.6%–93.6% of its $100.00 approval threshold. | agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold. | agent_13 (team ops): 2 payments, $908.57, each 84.9%–96.8% of its $500.00 approval threshold._
7. **open_questions** — Could the timing pattern be explained by operational batch processing?  
   _cites E6: First payment 11-09 11:55, last 11-10 16:10: all 10 within 28 h 15 m. Timing label: "over about 28 hours"._
8. **actions** — Review the business justification for payments to both merchants  
   _cites E7, E8: Nimbus Resell (compute, untrusted): 6 payments, $1,968.96, from 3 agents. | Orbit Tools (software, untrusted): 4 payments, $1,875.43, from 1 agent._
9. **actions** — Check historical activity of the agents for similar patterns  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $183.21, each 89.6%–93.6% of its $100.00 approval threshold. | agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold. | agent_13 (team ops): 2 payments, $908.57, each 84.9%–96.8% of its $500.00 approval threshold._

Recommendation: **escalate** · checklist: limit_proximity ✓, time_window ✗, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {"describes timing itself instead of using the pack's label": 3, 'contains a spelled-out number': 2}

## Note 2: AML_TEAM_STRUCTURING (severity 8) · reported (synth-v2)

```
[E1] Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.34.
[E2] 10 payments totalling $3,844.34, from 3 agents to 2 merchants.
[E3] agent_03 (team ops): 2 payments, $183.20, each 89.6%–93.6% of its $100.00 approval threshold.
[E4] agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold.
[E5] agent_13 (team ops): 2 payments, $908.56, each 84.9%–96.8% of its $500.00 approval threshold.
[E6] First payment 11-09 11:55, last 11-10 16:10: all 10 within 28 h 15 m. Timing label: "over about 28 hours".
[E7] Nimbus Resell (compute, untrusted): 6 payments, $1,968.93, from 3 agents.
[E8] Orbit Tools (software, untrusted): 4 payments, $1,875.41, from 1 agent.
[E9] agent_08 switched from Orbit Tools to Nimbus Resell between 11-09 20:41 and 11-10 08:38 (11 h 57 m apart).
[E10] Largest payments: T0001245 $492.57 (agent_08 to Orbit Tools, 11-09 16:57); T0001281 $484.12 (agent_13 to Nimbus Resell, 11-10 09:14); T0001271 $481.19 (agent_08 to Orbit Tools, 11-09 20:41); T0001228 $452.44 (agent_08 to Orbit Tools, 11-09 14:22); T0001196 $449.21 (agent_08 to Orbit Tools, 11-09 11:55).
[E11] Also flagged: A3396b35a05 (new merchant burst, severity 6, not in your queue, raised 11-09 10:49) shares merchant Orbit Tools.
[E12] Also flagged: A12b50479ef (new merchant burst, severity 6, in your queue, raised 11-09 17:07) shares merchant Orbit Tools.
[E13] Also flagged: A7179089a09 (fan in, severity 7, in your queue, raised 11-10 11:27) shares merchant Orbit Tools; agent agent_08.
[E14] Also flagged: Ac77696ddd2 (new merchant burst, severity 6, in your queue, raised 11-10 13:51) shares merchant Nimbus Resell.
[E15] Also flagged: Af51c9a493b (structuring, severity 8, not in your queue, raised 11-10 15:17) shares merchant Nimbus Resell, Orbit Tools; agent agent_08.
[E16] Also flagged: Ab8a48ca6a8 (fan in, severity 7, in your queue, raised 11-10 16:10) shares merchant Nimbus Resell; agent agent_03, agent_08, agent_13.
```

1. **summary** — Several payments from multiple agents were made just under their approval thresholds to untrusted merchants, indicating possible structuring  
   _cites E1: Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.34._
2. **evidence** — Agent08 made many payments each just under its higher threshold  
   _cites E4: agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold._
3. **evidence** — Nimbus Resell is an untrusted merchant receiving multiple payments  
   _cites E7: Nimbus Resell (compute, untrusted): 6 payments, $1,968.93, from 3 agents._
4. **evidence** — Orbit Tools is an untrusted merchant receiving multiple payments  
   _cites E8: Orbit Tools (software, untrusted): 4 payments, $1,875.41, from 1 agent._
5. **evidence** — Agent08 switched merchants between payments  
   _cites E9: agent_08 switched from Orbit Tools to Nimbus Resell between 11-09 20:41 and 11-10 08:38 (11 h 57 m apart)._
6. **open_questions** — What legitimate business purpose links these agents to the untrusted merchants?  
   _cites E7, E8: Nimbus Resell (compute, untrusted): 6 payments, $1,968.93, from 3 agents. | Orbit Tools (software, untrusted): 4 payments, $1,875.41, from 1 agent._
7. **open_questions** — Are the untrusted merchants owned or controlled by a common entity?  
   _cites E7, E8: Nimbus Resell (compute, untrusted): 6 payments, $1,968.93, from 3 agents. | Orbit Tools (software, untrusted): 4 payments, $1,875.41, from 1 agent._
8. **open_questions** — Is there any internal policy that permits near-threshold payments for these agents?  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $183.20, each 89.6%–93.6% of its $100.00 approval threshold. | agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold. | agent_13 (team ops): 2 payments, $908.56, each 84.9%–96.8% of its $500.00 approval threshold._
9. **open_questions** — Do any of the agents have approved exceptions for these transaction patterns?  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $183.20, each 89.6%–93.6% of its $100.00 approval threshold. | agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold. | agent_13 (team ops): 2 payments, $908.56, each 84.9%–96.8% of its $500.00 approval threshold._
10. **actions** — Request business justification and supporting documentation for each payment  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $183.20, each 89.6%–93.6% of its $100.00 approval threshold. | agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold. | agent_13 (team ops): 2 payments, $908.56, each 84.9%–96.8% of its $500.00 approval threshold._
11. **actions** — Monitor future transactions from these agents for repeat patterns  
   _cites E6: First payment 11-09 11:55, last 11-10 16:10: all 10 within 28 h 15 m. Timing label: "over about 28 hours"._
12. **reason** — The pack shows a coordinated series of near-threshold payments to untrusted merchants across several agents, a classic structuring indicator  
   _cites E1: Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.34._

Recommendation: **more_info** · checklist: limit_proximity ✓, time_window ✓, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {'contains a spelled-out number': 3, "describes timing itself instead of using the pack's label": 1}

## Note 3: AML_FAN_IN (severity 7) · seed 301

```
[E1] Rule explanation (computed by code, true): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h.
[E2] 4 payments totalling $402.06, from 3 agents to 1 merchant.
[E3] agent_02 (team finance): 1 payment, $286.00, at 57.2% of its $500.00 approval threshold.
[E4] agent_12 (team finance): 2 payments, $86.09, each 20.0%–66.1% of its $100.00 approval threshold.
[E5] agent_34 (team platform): 1 payment, $29.97, at 59.9% of its $50.00 approval threshold.
[E6] First payment 11-09 10:55, last 11-09 18:01: all 4 within 7 h 6 m. Timing label: "within one day".
[E7] Orbit Tools (software, untrusted): 4 payments, $402.06, from 3 agents.
[E8] Largest payments: T0001394 $286.00 (agent_02 to Orbit Tools, 11-09 18:01); T0001344 $66.11 (agent_12 to Orbit Tools, 11-09 12:27); T0001323 $29.97 (agent_34 to Orbit Tools, 11-09 10:55); T0001392 $19.98 (agent_12 to Orbit Tools, 11-09 17:38).
[E9] Also flagged: A0445b0b381 (new merchant burst, severity 6, in your queue, raised 11-09 12:38) shares merchant Orbit Tools; agent agent_12.
[E10] Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_12.
[E11] Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools.
[E12] Also flagged: Abd9a471328 (fan in, severity 7, in your queue, raised 11-12 12:53) shares agent agent_02.
[E13] Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Orbit Tools.
[E14] Also flagged: A2b2f89b8e9 (velocity spike, severity 6, in your queue, raised 11-14 01:48) shares merchant Orbit Tools.
```

1. **evidence** — Shows several payments totalling a notable amount from multiple agents to the same merchant  
   _cites E2: 4 payments totalling $402.06, from 3 agents to 1 merchant._
2. **evidence** — All payments occurred within one day  
   _cites E6: First payment 11-09 10:55, last 11-09 18:01: all 4 within 7 h 6 m. Timing label: "within one day"._
3. **open_questions** — Are any of the agents authorized to transact with this merchant under existing business policies?  
   _cites E3, E4, E5: agent_02 (team finance): 1 payment, $286.00, at 57.2% of its $500.00 approval threshold. | agent_12 (team finance): 2 payments, $86.09, each 20.0%–66.1% of its $100.00 approval threshold. | agent_34 (team platform): 1 payment, $29.97, at 59.9% of its $50.00 approval threshold._
4. **open_questions** — Is there a legitimate business purpose linking the finance and platform teams to Orbit Tools?  
   _cites E1, E7: Rule explanation (computed by code, true): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h. | Orbit Tools (software, untrusted): 4 payments, $402.06, from 3 agents._
5. **open_questions** — Do any of the related alerts indicate a broader pattern of coordinated activity?  
   _cites E9, E10, E11, E12, E13, E14: Also flagged: A0445b0b381 (new merchant burst, severity 6, in your queue, raised 11-09 12:38) shares merchant Orbit Tools; agent agent_12. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_12. | Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools. | Also flagged: Abd9a471328 (fan in, severity 7, in your queue, raised 11-12 12:53) shares agent agent_02. | Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Orbit Tools. | Also flagged: A2b2f89b8e9 (velocity spike, severity 6, in your queue, raised 11-14 01:48) shares merchant Orbit Tools._
6. **actions** — Review the business justification and approval records for each agent's payment to Orbit Tools  
   _cites E3, E4, E5: agent_02 (team finance): 1 payment, $286.00, at 57.2% of its $500.00 approval threshold. | agent_12 (team finance): 2 payments, $86.09, each 20.0%–66.1% of its $100.00 approval threshold. | agent_34 (team platform): 1 payment, $29.97, at 59.9% of its $50.00 approval threshold._
7. **actions** — Check the merchant's risk profile and any prior exceptions granted for this vendor  
   _cites E7: Orbit Tools (software, untrusted): 4 payments, $402.06, from 3 agents._
8. **actions** — Correlate the related alerts to assess whether a coordinated scheme is emerging  
   _cites E9, E10, E11, E12, E13, E14: Also flagged: A0445b0b381 (new merchant burst, severity 6, in your queue, raised 11-09 12:38) shares merchant Orbit Tools; agent agent_12. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_12. | Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools. | Also flagged: Abd9a471328 (fan in, severity 7, in your queue, raised 11-12 12:53) shares agent agent_02. | Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Orbit Tools. | Also flagged: A2b2f89b8e9 (velocity spike, severity 6, in your queue, raised 11-14 01:48) shares merchant Orbit Tools._
9. **reason** — The pattern involves multiple agents, significant amounts relative to thresholds, and an untrusted merchant, indicating heightened risk  
   _cites E1, E2, E7: Rule explanation (computed by code, true): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h. | 4 payments totalling $402.06, from 3 agents to 1 merchant. | Orbit Tools (software, untrusted): 4 payments, $402.06, from 3 agents._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {"describes timing itself instead of using the pack's label": 1, "claims 'just under the threshold' without support": 2, 'contains a spelled-out number': 1}

## Note 4: AML_HIGH_RISK_CATEGORY (severity 6) · seed 301

```
[E1] Rule explanation (computed by code, true): 1 payments, $14.97, to a merchant in high-risk category 'gift_cards'.
[E2] 1 payment totalling $14.97, from 1 agent to 1 merchant.
[E3] agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold.
[E4] First payment 11-12 16:08, last 11-12 16:08: all 1 within 0 s. Timing label: "within a minute".
[E5] Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent.
[E6] Largest payments: T0001807 $14.97 (agent_36 to Apex Vouchers, 11-12 16:08).
[E7] Also flagged: A75fb5922eb (fan in, severity 7, in your queue, raised 11-13 12:51) shares agent agent_36.
[E8] Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Apex Vouchers; agent agent_36.
[E9] Also flagged: Aa6e06a7a90 (rapid fire, severity 5, in your queue, raised 11-13 16:51) shares agent agent_36.
[E10] Also flagged: Ae5db42c7b2 (velocity spike, severity 6, in your queue, raised 11-13 16:51) shares agent agent_36.
```

1. **summary** — A single low-value payment to a high-risk gift-card merchant was made by an agent that appears in multiple other alerts  
   _cites E1, E3: Rule explanation (computed by code, true): 1 payments, $14.97, to a merchant in high-risk category 'gift_cards'. | agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold._
2. **evidence** — the payment used a small fraction of the agent's approval threshold  
   _cites E3: agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold._
3. **evidence** — the merchant is classified as untrusted in a high-risk category  
   _cites E5: Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent._
4. **evidence** — the same agent is linked to another alert with higher severity  
   _cites E7: Also flagged: A75fb5922eb (fan in, severity 7, in your queue, raised 11-13 12:51) shares agent agent_36._
5. **evidence** — the same agent appears in a rapid-fire alert  
   _cites E9: Also flagged: Aa6e06a7a90 (rapid fire, severity 5, in your queue, raised 11-13 16:51) shares agent agent_36._
6. **evidence** — the same agent appears in a velocity-spike alert  
   _cites E10: Also flagged: Ae5db42c7b2 (velocity spike, severity 6, in your queue, raised 11-13 16:51) shares agent agent_36._
7. **open_questions** — Is the agent's activity part of a coordinated scheme across multiple merchants?  
   _cites E7, E8, E9, E10: Also flagged: A75fb5922eb (fan in, severity 7, in your queue, raised 11-13 12:51) shares agent agent_36. | Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Apex Vouchers; agent agent_36. | Also flagged: Aa6e06a7a90 (rapid fire, severity 5, in your queue, raised 11-13 16:51) shares agent agent_36. | Also flagged: Ae5db42c7b2 (velocity spike, severity 6, in your queue, raised 11-13 16:51) shares agent agent_36._
8. **open_questions** — Does the merchant have a legitimate business purpose for the gift-card transactions?  
   _cites E5: Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent._
9. **actions** — Review the other alerts linked to the agent for patterns of abuse  
   _cites E7: Also flagged: A75fb5922eb (fan in, severity 7, in your queue, raised 11-13 12:51) shares agent agent_36._
10. **actions** — Obtain background information on the merchant's ownership and licensing  
   _cites E5: Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent._
11. **actions** — Check for any known sanctions or watch-list matches involving the agent or merchant  
   _cites E1: Rule explanation (computed by code, true): 1 payments, $14.97, to a merchant in high-risk category 'gift_cards'._
12. **reason** — the agent is connected to several high-severity alerts and the merchant is untrusted in a high-risk category  
   _cites E5, E7: Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent. | Also flagged: A75fb5922eb (fan in, severity 7, in your queue, raised 11-13 12:51) shares agent agent_36._

Recommendation: **escalate** · checklist: time_window ✗, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {"describes timing itself instead of using the pack's label": 1}

## Note 5: AML_LOOKALIKE_MERCHANT (severity 9) · seed 301

```
[E1] Rule explanation (computed by code, true): Paid 'C0reCloud', which resembles trusted merchant 'CoreCloud': 3 payments, $85.64.
[E2] 3 payments totalling $85.64, from 1 agent to 1 merchant.
[E3] agent_38 (team ops): 3 payments, $85.64, each 49.0%–69.7% of its $50.00 approval threshold.
[E4] First payment 11-10 12:43, last 11-10 17:46: all 3 within 5 h 3 m. Timing label: "within one day".
[E5] C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent.
[E6] Largest payments: T0001514 $34.86 (agent_38 to C0reCloud, 11-10 17:46); T0001457 $26.28 (agent_38 to C0reCloud, 11-10 12:43); T0001459 $24.50 (agent_38 to C0reCloud, 11-10 12:54).
[E7] Also flagged: Ab5257dbeab (new merchant burst, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38.
[E8] Also flagged: A20de01d7ab (rapid fire, severity 5, in your queue, raised 11-14 08:26) shares agent agent_38.
[E9] Also flagged: A8f89ab1e35 (velocity spike, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38.
[E10] Also flagged: A82197268b4 (fan in, severity 7, not in your queue, raised 11-15 18:54) shares agent agent_38.
```

1. **evidence** — Merchant is flagged as untrusted despite name similarity  
   _cites E5: C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent._
2. **evidence** — All payments occurred within one day  
   _cites E4: First payment 11-10 12:43, last 11-10 17:46: all 3 within 5 h 3 m. Timing label: "within one day"._
3. **open_questions** — Is the merchant C0reCloud a legitimate variant or a spoof of the trusted CoreCloud?  
   _cites E5: C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent._
4. **open_questions** — Do the other alerts sharing the same agent indicate a broader pattern of misuse?  
   _cites E7, E8, E9, E10: Also flagged: Ab5257dbeab (new merchant burst, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A20de01d7ab (rapid fire, severity 5, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A8f89ab1e35 (velocity spike, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A82197268b4 (fan in, severity 7, not in your queue, raised 11-15 18:54) shares agent agent_38._
5. **actions** — Review the merchant registration and naming conventions for C0reCloud to confirm authenticity  
   _cites E5: C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent._
6. **actions** — Examine the agent's recent activity log for additional high-value or similar look-alike transactions  
   _cites E3: agent_38 (team ops): 3 payments, $85.64, each 49.0%–69.7% of its $50.00 approval threshold._
7. **actions** — Cross-reference the flagged alerts that share the same agent to assess coordinated behavior  
   _cites E7: Also flagged: Ab5257dbeab (new merchant burst, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {"claims 'just under the threshold' without support": 2, 'contains a spelled-out number': 1, "describes timing itself instead of using the pack's label": 1}

## Note 6: AML_NEW_MERCHANT_BURST (severity 6) · seed 301

```
[E1] Rule explanation (computed by code, true): 3 first-time merchants inside 24h.
[E2] 3 payments totalling $117.59, from 1 agent to 3 merchants.
[E3] agent_12 (team finance): 3 payments, $117.59, each 21.6%–66.1% of its $100.00 approval threshold.
[E4] First payment 11-09 12:27, last 11-09 12:38: all 3 within 10 m. Timing label: "within an hour".
[E5] Orbit Tools (software, untrusted): 1 payment, $66.11, from 1 agent.
[E6] Pixel Forge Studio (software, untrusted): 1 payment, $29.89, from 1 agent.
[E7] Swiftpay Transfer (money_transfer, untrusted): 1 payment, $21.59, from 1 agent.
[E8] agent_12 switched from Orbit Tools to Pixel Forge Studio between 11-09 12:27 and 11-09 12:27 (6 s apart).
[E9] agent_12 switched from Pixel Forge Studio to Swiftpay Transfer between 11-09 12:27 and 11-09 12:38 (10 m apart).
[E10] Largest payments: T0001344 $66.11 (agent_12 to Orbit Tools, 11-09 12:27); T0001345 $29.89 (agent_12 to Pixel Forge Studio, 11-09 12:27); T0001348 $21.59 (agent_12 to Swiftpay Transfer, 11-09 12:38).
[E11] Also flagged: A19310559d0 (fan in, severity 7, in your queue, raised 11-09 18:01) shares merchant Orbit Tools; agent agent_12.
[E12] Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant Swiftpay Transfer.
[E13] Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares merchant Swiftpay Transfer; agent agent_12.
[E14] Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools, Swiftpay Transfer.
[E15] Also flagged: A6accdc0dcf (round amounts, severity 4, in your queue, raised 11-12 14:18) shares merchant Pixel Forge Studio.
[E16] Also flagged: A7e1b8dcd5f (velocity spike, severity 6, in your queue, raised 11-13 04:41) shares merchant Swiftpay Transfer.
[E17] Before this alert, agent_12 made 33 payments over 12 d 22 h (about 2.6 a day), mostly to Mapwise, Fernway Foods, Deskline Supplies, Northwind Air.
```

1. **evidence** — Payments each represent a high proportion of the agent's approval threshold  
   _cites E3: agent_12 (team finance): 3 payments, $117.59, each 21.6%–66.1% of its $100.00 approval threshold._
2. **evidence** — All payments occurred within an hour  
   _cites E4: First payment 11-09 12:27, last 11-09 12:38: all 3 within 10 m. Timing label: "within an hour"._
3. **evidence** — First merchant is untrusted software  
   _cites E5: Orbit Tools (software, untrusted): 1 payment, $66.11, from 1 agent._
4. **evidence** — Second merchant is untrusted software  
   _cites E6: Pixel Forge Studio (software, untrusted): 1 payment, $29.89, from 1 agent._
5. **evidence** — Third merchant is untrusted money transfer  
   _cites E7: Swiftpay Transfer (money_transfer, untrusted): 1 payment, $21.59, from 1 agent._
6. **open_questions** — Do any of the other flagged alerts share a common justification for using these merchants?  
   _cites E11, E12, E13, E14, E15, E16: Also flagged: A19310559d0 (fan in, severity 7, in your queue, raised 11-09 18:01) shares merchant Orbit Tools; agent agent_12. | Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant Swiftpay Transfer. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares merchant Swiftpay Transfer; agent agent_12. | Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools, Swiftpay Transfer. | Also flagged: A6accdc0dcf (round amounts, severity 4, in your queue, raised 11-12 14:18) shares merchant Pixel Forge Studio. | Also flagged: A7e1b8dcd5f (velocity spike, severity 6, in your queue, raised 11-13 04:41) shares merchant Swiftpay Transfer._
7. **actions** — Query the business unit for any approved projects involving Orbit Tools, Pixel Forge Studio, or Swiftpay Transfer  
   _cites E5, E6, E7: Orbit Tools (software, untrusted): 1 payment, $66.11, from 1 agent. | Pixel Forge Studio (software, untrusted): 1 payment, $29.89, from 1 agent. | Swiftpay Transfer (money_transfer, untrusted): 1 payment, $21.59, from 1 agent._
8. **actions** — Check whether the other flagged alerts involve the same merchant usage patterns and any documented approvals  
   _cites E11, E12, E13, E14, E15, E16: Also flagged: A19310559d0 (fan in, severity 7, in your queue, raised 11-09 18:01) shares merchant Orbit Tools; agent agent_12. | Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant Swiftpay Transfer. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares merchant Swiftpay Transfer; agent agent_12. | Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools, Swiftpay Transfer. | Also flagged: A6accdc0dcf (round amounts, severity 4, in your queue, raised 11-12 14:18) shares merchant Pixel Forge Studio. | Also flagged: A7e1b8dcd5f (velocity spike, severity 6, in your queue, raised 11-13 04:41) shares merchant Swiftpay Transfer._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {'contains a spelled-out number': 3, "describes timing itself instead of using the pack's label": 2}

## Note 7: AML_RAPID_FIRE (severity 5) · seed 301

```
[E1] Rule explanation (computed by code, true): 16 payments with at least 15 inside 60s.
[E2] 16 payments totalling $80.00, from 1 agent to 10 merchants.
[E3] agent_27 (team finance): 16 payments, $80.00, each 2.0%–2.0% of its $250.00 approval threshold.
[E4] First payment 11-10 18:25, last 11-10 18:26: all 16 within 30 s. Timing label: "within a minute".
[E5] Busiest stretch: 16 payments within 30 s (11-10 18:25–18:26). Timing label: "within a minute".
[E6] Brightline Print Co. (print, trusted): 2 payments, $10.00, from 1 agent.
[E7] CityCab (rides, trusted): 1 payment, $5.00, from 1 agent.
[E8] CoreCloud (compute, trusted): 2 payments, $10.00, from 1 agent.
[E9] Fernway Foods (food, trusted): 2 payments, $10.00, from 1 agent.
[E10] Ledgerly (software, trusted): 1 payment, $5.00, from 1 agent.
[E11] Lexa AI (ai_api, trusted): 1 payment, $5.00, from 1 agent.
[E12] Mapwise (data, trusted): 2 payments, $10.00, from 1 agent.
[E13] Northwind Air (flights, trusted): 1 payment, $5.00, from 1 agent.
[E14] Quillbase (software, trusted): 1 payment, $5.00, from 1 agent.
[E15] Tallyhouse Software (software, trusted): 3 payments, $15.00, from 1 agent.
[E16] agent_27 switched from Tallyhouse Software to Brightline Print Co. between 11-10 18:25 and 11-10 18:25 (2 s apart).
[E17] agent_27 switched from Brightline Print Co. to Quillbase between 11-10 18:25 and 11-10 18:25 (2 s apart).
[E18] agent_27 switched from Quillbase to CoreCloud between 11-10 18:25 and 11-10 18:25 (2 s apart).
[E19] agent_27 switched from CoreCloud to Fernway Foods between 11-10 18:25 and 11-10 18:25 (2 s apart).
[E20] agent_27 switched from Fernway Foods to Ledgerly between 11-10 18:25 and 11-10 18:25 (2 s apart).
[E21] Largest payments: T0001525 $5.00 (agent_27 to Tallyhouse Software, 11-10 18:25); T0001526 $5.00 (agent_27 to Brightline Print Co., 11-10 18:25); T0001527 $5.00 (agent_27 to Quillbase, 11-10 18:25); T0001528 $5.00 (agent_27 to CoreCloud, 11-10 18:25); T0001529 $5.00 (agent_27 to Fernway Foods, 11-10 18:25).
[E22] Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27.
[E23] Also flagged: Aea86239f87 (velocity spike, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27.
[E24] Also flagged: A8a3ef664e1 (fan in, severity 7, in your queue, raised 11-15 18:45) shares agent agent_27.
[E25] Before this alert, agent_27 made 60 payments over 13 d 3 h (about 4.6 a day), mostly to CityCab, Pageturn Books.
```

1. **evidence** — Agent appears in another high-severity alert  
   _cites E22: Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27._
2. **evidence** — Agent appears in a velocity-spike alert  
   _cites E23: Also flagged: Aea86239f87 (velocity spike, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27._
3. **open_questions** — Is there a legitimate business process requiring such frequent merchant changes?  
   _cites E16: agent_27 switched from Tallyhouse Software to Brightline Print Co. between 11-10 18:25 and 11-10 18:25 (2 s apart)._
4. **open_questions** — Do any of the merchants share ownership or a common backend?  
   _cites E6, E7, E8, E9, E10, E11, E12, E13, E14, E15: Brightline Print Co. (print, trusted): 2 payments, $10.00, from 1 agent. | CityCab (rides, trusted): 1 payment, $5.00, from 1 agent. | CoreCloud (compute, trusted): 2 payments, $10.00, from 1 agent. | Fernway Foods (food, trusted): 2 payments, $10.00, from 1 agent. | Ledgerly (software, trusted): 1 payment, $5.00, from 1 agent. | Lexa AI (ai_api, trusted): 1 payment, $5.00, from 1 agent. | Mapwise (data, trusted): 2 payments, $10.00, from 1 agent. | Northwind Air (flights, trusted): 1 payment, $5.00, from 1 agent. | Quillbase (software, trusted): 1 payment, $5.00, from 1 agent. | Tallyhouse Software (software, trusted): 3 payments, $15.00, from 1 agent._
5. **open_questions** — Could the agent be a test account for system integration?  
   _cites E25: Before this alert, agent_27 made 60 payments over 13 d 3 h (about 4.6 a day), mostly to CityCab, Pageturn Books._
6. **actions** — Review the business justification for the merchant-switching pattern  
   _cites E16: agent_27 switched from Tallyhouse Software to Brightline Print Co. between 11-10 18:25 and 11-10 18:25 (2 s apart)._
7. **actions** — Check for any known shared relationships among the listed merchants  
   _cites E6, E7, E8, E9, E10, E11, E12, E13, E14, E15: Brightline Print Co. (print, trusted): 2 payments, $10.00, from 1 agent. | CityCab (rides, trusted): 1 payment, $5.00, from 1 agent. | CoreCloud (compute, trusted): 2 payments, $10.00, from 1 agent. | Fernway Foods (food, trusted): 2 payments, $10.00, from 1 agent. | Ledgerly (software, trusted): 1 payment, $5.00, from 1 agent. | Lexa AI (ai_api, trusted): 1 payment, $5.00, from 1 agent. | Mapwise (data, trusted): 2 payments, $10.00, from 1 agent. | Northwind Air (flights, trusted): 1 payment, $5.00, from 1 agent. | Quillbase (software, trusted): 1 payment, $5.00, from 1 agent. | Tallyhouse Software (software, trusted): 3 payments, $15.00, from 1 agent._
8. **actions** — Correlate this activity with the other flagged alerts involving the same agent  
   _cites E22, E23, E24: Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27. | Also flagged: Aea86239f87 (velocity spike, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27. | Also flagged: A8a3ef664e1 (fan in, severity 7, in your queue, raised 11-15 18:45) shares agent agent_27._
9. **reason** — The pattern meets the rapid-fire rule and coincides with multiple high-severity alerts for the same agent  
   _cites E1, E22, E23: Rule explanation (computed by code, true): 16 payments with at least 15 inside 60s. | Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27. | Also flagged: Aea86239f87 (velocity spike, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27._

Recommendation: **escalate** · checklist: time_window ✗, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {"describes timing itself instead of using the pack's label": 3, "claims 'just under the threshold' without support": 1}

## Note 8: AML_ROUND_AMOUNTS (severity 4) · seed 301

```
[E1] Rule explanation (computed by code, true): 3 payments in exact multiples of $10.00.
[E2] 3 payments totalling $70.00, from 1 agent to 1 merchant.
[E3] agent_30 (team growth): 3 payments, $70.00, each 8.0%–12.0% of its $250.00 approval threshold.
[E4] First payment 11-09 16:12, last 11-09 17:10: all 3 within 57 m. Timing label: "within an hour".
[E5] Ledgerly (software, trusted): 3 payments, $70.00, from 1 agent.
[E6] Largest payments: T0001387 $30.00 (agent_30 to Ledgerly, 11-09 17:10); T0001378 $20.00 (agent_30 to Ledgerly, 11-09 16:12); T0001385 $20.00 (agent_30 to Ledgerly, 11-09 17:00).
[E7] Also flagged: A35f7572ae2 (fan in, severity 7, in your queue, raised 11-13 09:40) shares agent agent_30.
[E8] Also flagged: Afa1aeff6e1 (structuring, severity 8, in your queue, raised 11-13 17:23) shares agent agent_30.
[E9] Also flagged: Ae645828e69 (high risk category, severity 6, in your queue, raised 11-15 14:16) shares agent agent_30.
[E10] Before this alert, agent_30 made 24 payments over 13 d 2 h (about 1.8 a day), mostly to Promptworks, DataLoom, Quillbase.
```

1. **evidence** — each payment falls within the high-percentage band of the approval threshold  
   _cites E3: agent_30 (team growth): 3 payments, $70.00, each 8.0%–12.0% of its $250.00 approval threshold._
2. **evidence** — the payments occurred within an hour  
   _cites E4: First payment 11-09 16:12, last 11-09 17:10: all 3 within 57 m. Timing label: "within an hour"._
3. **open_questions** — Is the clustering of other high-severity alerts sharing agent 30 indicative of coordinated activity?  
   _cites E7, E8, E9: Also flagged: A35f7572ae2 (fan in, severity 7, in your queue, raised 11-13 09:40) shares agent agent_30. | Also flagged: Afa1aeff6e1 (structuring, severity 8, in your queue, raised 11-13 17:23) shares agent agent_30. | Also flagged: Ae645828e69 (high risk category, severity 6, in your queue, raised 11-15 14:16) shares agent agent_30._
4. **open_questions** — Does the prior pattern of frequent small payments to other vendors relate to this round-amount behavior?  
   _cites E10: Before this alert, agent_30 made 24 payments over 13 d 2 h (about 1.8 a day), mostly to Promptworks, DataLoom, Quillbase._
5. **actions** — Review the business justification for payments to the trusted software vendor  
   _cites E5: Ledgerly (software, trusted): 3 payments, $70.00, from 1 agent._
6. **actions** — Cross-reference the other flagged alerts for shared entities or motives  
   _cites E7, E8, E9: Also flagged: A35f7572ae2 (fan in, severity 7, in your queue, raised 11-13 09:40) shares agent agent_30. | Also flagged: Afa1aeff6e1 (structuring, severity 8, in your queue, raised 11-13 17:23) shares agent agent_30. | Also flagged: Ae645828e69 (high risk category, severity 6, in your queue, raised 11-15 14:16) shares agent agent_30._
7. **actions** — Assess whether the payment pattern aligns with any known internal policy exceptions  
   _cites E2: 3 payments totalling $70.00, from 1 agent to 1 merchant._
8. **reason** — the combination of round amounts, high threshold percentages, and linkage to multiple severe alerts suggests potential illicit structuring  
   _cites E1, E3, E8: Rule explanation (computed by code, true): 3 payments in exact multiples of $10.00. | agent_30 (team growth): 3 payments, $70.00, each 8.0%–12.0% of its $250.00 approval threshold. | Also flagged: Afa1aeff6e1 (structuring, severity 8, in your queue, raised 11-13 17:23) shares agent agent_30._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {"claims 'just under the threshold' without support": 1, 'contains a spelled-out number': 1, "describes timing itself instead of using the pack's label": 1}

## Note 9: AML_STRUCTURING (severity 8) · seed 301

```
[E1] Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76.
[E2] 4 payments totalling $1,829.76, from 1 agent to 1 merchant.
[E3] agent_01 (team research): 4 payments, $1,829.76, each 88.8%–95.0% of its $500.00 approval threshold.
[E4] First payment 11-11 09:11, last 11-11 19:03: all 4 within 9 h 51 m. Timing label: "within one day".
[E5] QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent.
[E6] Largest payments: T0001701 $475.22 (agent_01 to QuickData Hub, 11-11 19:03); T0001569 $462.69 (agent_01 to QuickData Hub, 11-11 09:11); T0001693 $448.05 (agent_01 to QuickData Hub, 11-11 18:27); T0001606 $443.80 (agent_01 to QuickData Hub, 11-11 11:52).
[E7] Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant QuickData Hub.
[E8] Also flagged: A301dda7de9 (new merchant burst, severity 6, in your queue, raised 11-15 18:45) shares merchant QuickData Hub.
[E9] Also flagged: A8a3ef664e1 (fan in, severity 7, in your queue, raised 11-15 18:45) shares merchant QuickData Hub; agent agent_01.
[E10] Before this alert, agent_01 made 33 payments over 16 d 2 h (about 2.0 a day), mostly to Brightline Print Co., Fernway Foods, Vectorly, Quillbase.
```

1. **summary** — Agent made several payments just under the approval threshold to an untrusted data merchant, matching a structuring pattern  
   _cites E1: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76._
2. **evidence** — Payments each fell within the high-percentage range of the threshold  
   _cites E3: agent_01 (team research): 4 payments, $1,829.76, each 88.8%–95.0% of its $500.00 approval threshold._
3. **evidence** — All payments occurred within one day  
   _cites E4: First payment 11-11 09:11, last 11-11 19:03: all 4 within 9 h 51 m. Timing label: "within one day"._
4. **evidence** — Recipient is flagged as untrusted data provider  
   _cites E5: QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent._
5. **evidence** — Payments clustered at the upper end of the threshold  
   _cites E6: Largest payments: T0001701 $475.22 (agent_01 to QuickData Hub, 11-11 19:03); T0001569 $462.69 (agent_01 to QuickData Hub, 11-11 09:11); T0001693 $448.05 (agent_01 to QuickData Hub, 11-11 18:27); T0001606 $443.80 (agent_01 to QuickData Hub, 11-11 11:52)._
6. **open_questions** — Is there a legitimate business purpose for using this untrusted data merchant?  
   _cites E5: QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent._
7. **open_questions** — Do other agents also transact with this merchant in a similar pattern?  
   _cites E7, E8: Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant QuickData Hub. | Also flagged: A301dda7de9 (new merchant burst, severity 6, in your queue, raised 11-15 18:45) shares merchant QuickData Hub._
8. **open_questions** — Could the agent be attempting to evade reporting limits?  
   _cites E1, E3: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76. | agent_01 (team research): 4 payments, $1,829.76, each 88.8%–95.0% of its $500.00 approval threshold._
9. **actions** — Request justification and documentation for the merchant relationship  
   _cites E5: QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent._
10. **actions** — Query the transaction history of other agents for similar activity  
   _cites E7: Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant QuickData Hub._
11. **actions** — Place the agent under enhanced monitoring for future payments  
   _cites E1: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76._
12. **reason** — Pattern aligns with structuring criteria and involves an untrusted merchant  
   _cites E1: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76._

Recommendation: **escalate** · checklist: limit_proximity ✓, time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: nothing

## Note 10: AML_TEAM_STRUCTURING (severity 8) · seed 301

```
[E1] Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42.
[E2] 6 payments totalling $677.42, from 3 agents to 1 merchant.
[E3] agent_03 (team ops): 2 payments, $169.80, each 84.3%–85.5% of its $100.00 approval threshold.
[E4] agent_08 (team ops): 2 payments, $90.22, each 89.4%–91.0% of its $50.00 approval threshold.
[E5] agent_13 (team ops): 2 payments, $417.40, each 82.2%–84.7% of its $250.00 approval threshold.
[E6] First payment 11-10 15:03, last 11-10 18:23: all 6 within 3 h 20 m. Timing label: "within one day".
[E7] Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents.
[E8] Largest payments: T0001491 $211.87 (agent_13 to Halcyon Consulting, 11-10 15:49); T0001523 $205.53 (agent_13 to Halcyon Consulting, 11-10 18:14); T0001519 $85.47 (agent_03 to Halcyon Consulting, 11-10 17:57); T0001524 $84.33 (agent_03 to Halcyon Consulting, 11-10 18:23); T0001478 $45.52 (agent_08 to Halcyon Consulting, 11-10 15:03).
[E9] Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_08.
[E10] Also flagged: Ac4f335a26a (fan in, severity 7, in your queue, raised 11-11 09:24) shares merchant Halcyon Consulting; agent agent_03, agent_08, agent_13.
[E11] Also flagged: A95acc79c3e (new merchant burst, severity 6, in your queue, raised 11-11 14:07) shares merchant Halcyon Consulting; agent agent_03.
[E12] Also flagged: A594066e122 (rapid fire, severity 5, in your queue, raised 11-11 14:07) shares agent agent_03.
[E13] Also flagged: Aa487cd1ab8 (velocity spike, severity 6, in your queue, raised 11-11 14:38) shares agent agent_03.
[E14] Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Halcyon Consulting; agent agent_08.
```

1. **summary** — Several payments from multiple agents of one owner were made just under their approval thresholds to an untrusted merchant, indicating possible structuring.  
   _cites E1: Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42._
2. **evidence** — All payments occurred within one day.  
   _cites E6: First payment 11-10 15:03, last 11-10 18:23: all 6 within 3 h 20 m. Timing label: "within one day"._
3. **evidence** — The recipient is an untrusted merchant.  
   _cites E7: Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents._
4. **open_questions** — Why were multiple agents directed to the same untrusted merchant?  
   _cites E7: Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents._
5. **open_questions** — Do the other flagged alerts share a coordinated pattern with these payments?  
   _cites E9, E10, E11, E12, E13, E14: Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_08. | Also flagged: Ac4f335a26a (fan in, severity 7, in your queue, raised 11-11 09:24) shares merchant Halcyon Consulting; agent agent_03, agent_08, agent_13. | Also flagged: A95acc79c3e (new merchant burst, severity 6, in your queue, raised 11-11 14:07) shares merchant Halcyon Consulting; agent agent_03. | Also flagged: A594066e122 (rapid fire, severity 5, in your queue, raised 11-11 14:07) shares agent agent_03. | Also flagged: Aa487cd1ab8 (velocity spike, severity 6, in your queue, raised 11-11 14:38) shares agent agent_03. | Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Halcyon Consulting; agent agent_08._
6. **open_questions** — Is there a legitimate business reason linking these agents and the merchant?  
   _cites E2: 6 payments totalling $677.42, from 3 agents to 1 merchant._
7. **actions** — Review the business relationship between the owner and the merchant.  
   _cites E7: Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents._
8. **actions** — Examine the other flagged alerts for similar agent-merchant links.  
   _cites E9, E10: Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_08. | Also flagged: Ac4f335a26a (fan in, severity 7, in your queue, raised 11-11 09:24) shares merchant Halcyon Consulting; agent agent_03, agent_08, agent_13._
9. **actions** — Query the agents for purpose of these near-threshold payments.  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $169.80, each 84.3%–85.5% of its $100.00 approval threshold. | agent_08 (team ops): 2 payments, $90.22, each 89.4%–91.0% of its $50.00 approval threshold. | agent_13 (team ops): 2 payments, $417.40, each 82.2%–84.7% of its $250.00 approval threshold._
10. **reason** — The pattern matches structuring criteria with multiple near-threshold payments to an untrusted party.  
   _cites E1: Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42._

Recommendation: **escalate** · checklist: limit_proximity ✓, time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {'contains a spelled-out number': 3}
