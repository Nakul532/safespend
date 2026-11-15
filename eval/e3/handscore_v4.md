# E3 v4 hand-score pack (10 notes)

Note 1 is the frozen reference case (A6c2d42955a, data before the whole-cent / ID-order fix). Notes 2–10 are the first nine v4 notes with kept lines (synth-v2 data). For each line mark Supported (Y/N) and Useful (Y/N/Partly) in handscore_v4.csv. SIMULATED money, synthetic data.

## Note 1: AML_TEAM_STRUCTURING (severity 8) · reference (frozen, pre-fix data)

```
[E1] Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.39.
[E2] 10 payments totalling $3,844.39, from 3 agents to 2 merchants.
[E3] agent_03 (team ops): 2 payments, $183.21, each 89.6%–93.6% of its $100.00 approval threshold.
[E4] agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold.
[E5] agent_13 (team ops): 2 payments, $908.57, each 84.9%–96.8% of its $500.00 approval threshold.
[E6] First payment 11-09 11:55, last 11-10 16:10: all 10 within 28 h 15 m.
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

1. **evidence** — Agent 08 made multiple payments each just under its higher threshold  
   _cites E4: agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold._
2. **open_questions** — Why did multiple agents target the same untrusted merchants?  
   _cites E7, E8: Nimbus Resell (compute, untrusted): 6 payments, $1,968.96, from 3 agents. | Orbit Tools (software, untrusted): 4 payments, $1,875.43, from 1 agent._
3. **open_questions** — What prompted the switch of agent 08 between merchants?  
   _cites E9: agent_08 switched from Orbit Tools to Nimbus Resell between 11-09 20:41 and 11-10 08:38 (11 h 57 m apart)._
4. **actions** — Review the risk profiles of the untrusted merchants involved  
   _cites E7: Nimbus Resell (compute, untrusted): 6 payments, $1,968.96, from 3 agents._
5. **actions** — Examine the business justification and approval workflow for each agent's payments  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $183.21, each 89.6%–93.6% of its $100.00 approval threshold. | agent_08 (team ops): 6 payments, $2,752.61, each 87.0%–98.5% of its $500.00 approval threshold. | agent_13 (team ops): 2 payments, $908.57, each 84.9%–96.8% of its $500.00 approval threshold._
6. **actions** — Query whether the agents share a common operational purpose or directive  
   _cites E1: Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.39._

Recommendation: **escalate** · checklist: limit_proximity ✓, time_window ✗, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {'claims a short period without support': 3, 'contains a spelled-out number': 2, "argues against the alert's computed facts": 1}

## Note 2: AML_TEAM_STRUCTURING (severity 8) · reported (synth-v2)

```
[E1] Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.34.
[E2] 10 payments totalling $3,844.34, from 3 agents to 2 merchants.
[E3] agent_03 (team ops): 2 payments, $183.20, each 89.6%–93.6% of its $100.00 approval threshold.
[E4] agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold.
[E5] agent_13 (team ops): 2 payments, $908.56, each 84.9%–96.8% of its $500.00 approval threshold.
[E6] First payment 11-09 11:55, last 11-10 16:10: all 10 within 28 h 15 m.
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

1. **evidence** — Agent 03 contributed payments near its low threshold  
   _cites E3: agent_03 (team ops): 2 payments, $183.20, each 89.6%–93.6% of its $100.00 approval threshold._
2. **evidence** — Agent 08 contributed the bulk of payments near its higher threshold  
   _cites E4: agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold._
3. **evidence** — Agent 13 also made payments near its threshold  
   _cites E5: agent_13 (team ops): 2 payments, $908.56, each 84.9%–96.8% of its $500.00 approval threshold._
4. **evidence** — Payments were directed to an untrusted compute merchant  
   _cites E7: Nimbus Resell (compute, untrusted): 6 payments, $1,968.93, from 3 agents._
5. **evidence** — Payments were also directed to an untrusted software merchant  
   _cites E8: Orbit Tools (software, untrusted): 4 payments, $1,875.41, from 1 agent._
6. **open_questions** — Are there any approved contracts or services that justify the near-threshold amounts?  
   _cites E1: Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.34._
7. **actions** — Request documentation of contracts with the compute and software merchants  
   _cites E7, E8: Nimbus Resell (compute, untrusted): 6 payments, $1,968.93, from 3 agents. | Orbit Tools (software, untrusted): 4 payments, $1,875.41, from 1 agent._
8. **actions** — Interview the ops owner to explain the agents' activity and merchant selection  
   _cites E1: Rule explanation (computed by code, true): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.34._
9. **actions** — Check for any prior approvals or exemptions for near-threshold payments  
   _cites E4: agent_08 (team ops): 6 payments, $2,752.58, each 87.0%–98.5% of its $500.00 approval threshold._

Recommendation: **more_info** · checklist: limit_proximity ✓, time_window ✗, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {'claims a short period without support': 2, "argues against the alert's computed facts": 2, 'contains a spelled-out number': 1}

## Note 3: AML_FAN_IN (severity 7) · seed 301

```
[E1] Rule explanation (computed by code, true): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h.
[E2] 4 payments totalling $402.06, from 3 agents to 1 merchant.
[E3] agent_02 (team finance): 1 payment, $286.00, at 57.2% of its $500.00 approval threshold.
[E4] agent_12 (team finance): 2 payments, $86.09, each 20.0%–66.1% of its $100.00 approval threshold.
[E5] agent_34 (team platform): 1 payment, $29.97, at 59.9% of its $50.00 approval threshold.
[E6] First payment 11-09 10:55, last 11-09 18:01: all 4 within 7 h 6 m.
[E7] Orbit Tools (software, untrusted): 4 payments, $402.06, from 3 agents.
[E8] Largest payments: T0001394 $286.00 (agent_02 to Orbit Tools, 11-09 18:01); T0001344 $66.11 (agent_12 to Orbit Tools, 11-09 12:27); T0001323 $29.97 (agent_34 to Orbit Tools, 11-09 10:55); T0001392 $19.98 (agent_12 to Orbit Tools, 11-09 17:38).
[E9] Also flagged: A0445b0b381 (new merchant burst, severity 6, in your queue, raised 11-09 12:38) shares merchant Orbit Tools; agent agent_12.
[E10] Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_12.
[E11] Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools.
[E12] Also flagged: Abd9a471328 (fan in, severity 7, in your queue, raised 11-12 12:53) shares agent agent_02.
[E13] Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Orbit Tools.
[E14] Also flagged: A2b2f89b8e9 (velocity spike, severity 6, in your queue, raised 11-14 01:48) shares merchant Orbit Tools.
```

1. **summary** — Several agents made several payments to an untrusted merchant within a short period, triggering a fan-in alert  
   _cites E1: Rule explanation (computed by code, true): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h._
2. **evidence** — Payments spanned a wide range of threshold percentages  
   _cites E4: agent_12 (team finance): 2 payments, $86.09, each 20.0%–66.1% of its $100.00 approval threshold._
3. **evidence** — All payments occurred within a short period  
   _cites E6: First payment 11-09 10:55, last 11-09 18:01: all 4 within 7 h 6 m._
4. **evidence** — All payments targeted the same untrusted merchant  
   _cites E7: Orbit Tools (software, untrusted): 4 payments, $402.06, from 3 agents._
5. **open_questions** — Do any of the agents share a common project or approval workflow that explains the coordinated payments?  
   _cites E9, E10: Also flagged: A0445b0b381 (new merchant burst, severity 6, in your queue, raised 11-09 12:38) shares merchant Orbit Tools; agent agent_12. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_12._
6. **actions** — Review the business justification and approval records for each payment  
   _cites E2: 4 payments totalling $402.06, from 3 agents to 1 merchant._
7. **actions** — Check for any recent onboarding or policy changes involving the merchant  
   _cites E9: Also flagged: A0445b0b381 (new merchant burst, severity 6, in your queue, raised 11-09 12:38) shares merchant Orbit Tools; agent agent_12._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {"claims 'just under the threshold' without support": 3, "argues against the alert's computed facts": 1}

## Note 4: AML_HIGH_RISK_CATEGORY (severity 6) · seed 301

```
[E1] Rule explanation (computed by code, true): 1 payments, $14.97, to a merchant in high-risk category 'gift_cards'.
[E2] 1 payment totalling $14.97, from 1 agent to 1 merchant.
[E3] agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold.
[E4] First payment 11-12 16:08, last 11-12 16:08: all 1 within 0 s.
[E5] Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent.
[E6] Largest payments: T0001807 $14.97 (agent_36 to Apex Vouchers, 11-12 16:08).
[E7] Also flagged: A75fb5922eb (fan in, severity 7, in your queue, raised 11-13 12:51) shares agent agent_36.
[E8] Also flagged: A414852597d (new merchant burst, severity 6, not in your queue, raised 11-13 16:51) shares merchant Apex Vouchers; agent agent_36.
[E9] Also flagged: Aa6e06a7a90 (rapid fire, severity 5, in your queue, raised 11-13 16:51) shares agent agent_36.
[E10] Also flagged: Ae5db42c7b2 (velocity spike, severity 6, in your queue, raised 11-13 16:51) shares agent agent_36.
```

1. **summary** — A single low-value payment to a high-risk gift-card merchant triggered the high-risk category rule  
   _cites E1: Rule explanation (computed by code, true): 1 payments, $14.97, to a merchant in high-risk category 'gift_cards'._
2. **evidence** — payment is a small fraction of the agent's approval threshold, indicating low-risk size but still flagged due to merchant category  
   _cites E3: agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold._
3. **evidence** — merchant is classified as untrusted gift-cards, matching the high-risk category  
   _cites E5: Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent._
4. **open_questions** — Does agent_36 normally interact with gift-card merchants or is this an outlier?  
   _cites E3: agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold._
5. **open_questions** — Are there any internal approvals or documentation for this transaction?  
   _cites E2: 1 payment totalling $14.97, from 1 agent to 1 merchant._
6. **actions** — Review agent_36's transaction history for similar merchant interactions  
   _cites E3: agent_36 (team research): 1 payment, $14.97, at 6.0% of its $250.00 approval threshold._
7. **actions** — Request supporting documentation or business justification for the purchase from Apex Vouchers  
   _cites E2: 1 payment totalling $14.97, from 1 agent to 1 merchant._
8. **actions** — Check if the merchant Apex Vouchers is on any internal watchlist beyond the high-risk tag  
   _cites E5: Apex Vouchers (gift_cards, untrusted): 1 payment, $14.97, from 1 agent._
9. **reason** — the payment is low-value and isolated but involves an untrusted high-risk merchant, requiring further context  
   _cites E1: Rule explanation (computed by code, true): 1 payments, $14.97, to a merchant in high-risk category 'gift_cards'._

Recommendation: **more_info** · checklist: time_window ✗, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {'claims a burst without support': 1, "argues against the alert's computed facts": 1}

## Note 5: AML_LOOKALIKE_MERCHANT (severity 9) · seed 301

```
[E1] Rule explanation (computed by code, true): Paid 'C0reCloud', which resembles trusted merchant 'CoreCloud': 3 payments, $85.64.
[E2] 3 payments totalling $85.64, from 1 agent to 1 merchant.
[E3] agent_38 (team ops): 3 payments, $85.64, each 49.0%–69.7% of its $50.00 approval threshold.
[E4] First payment 11-10 12:43, last 11-10 17:46: all 3 within 5 h 3 m.
[E5] C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent.
[E6] Largest payments: T0001514 $34.86 (agent_38 to C0reCloud, 11-10 17:46); T0001457 $26.28 (agent_38 to C0reCloud, 11-10 12:43); T0001459 $24.50 (agent_38 to C0reCloud, 11-10 12:54).
[E7] Also flagged: Ab5257dbeab (new merchant burst, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38.
[E8] Also flagged: A20de01d7ab (rapid fire, severity 5, in your queue, raised 11-14 08:26) shares agent agent_38.
[E9] Also flagged: A8f89ab1e35 (velocity spike, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38.
[E10] Also flagged: A82197268b4 (fan in, severity 7, not in your queue, raised 11-15 18:54) shares agent agent_38.
```

1. **evidence** — Each payment approached the agent's approval limit  
   _cites E3: agent_38 (team ops): 3 payments, $85.64, each 49.0%–69.7% of its $50.00 approval threshold._
2. **evidence** — All payments occurred within a short period  
   _cites E4: First payment 11-10 12:43, last 11-10 17:46: all 3 within 5 h 3 m._
3. **evidence** — The merchant is flagged as untrusted  
   _cites E5: C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent._
4. **open_questions** — What is the business justification for using this untrusted merchant?  
   _cites E5: C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent._
5. **open_questions** — Does the agent have a history of similar transactions with other merchants?  
   _cites E7, E8, E9: Also flagged: Ab5257dbeab (new merchant burst, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A20de01d7ab (rapid fire, severity 5, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A8f89ab1e35 (velocity spike, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38._
6. **open_questions** — Are there any internal policies that permit payments at this proportion of the threshold?  
   _cites E2: 3 payments totalling $85.64, from 1 agent to 1 merchant._
7. **actions** — Review the agent's transaction history and role justification  
   _cites E3: agent_38 (team ops): 3 payments, $85.64, each 49.0%–69.7% of its $50.00 approval threshold._
8. **actions** — Conduct due-diligence on the merchant's legitimacy  
   _cites E5: C0reCloud (compute, untrusted): 3 payments, $85.64, from 1 agent._
9. **actions** — Monitor related alerts sharing the same agent for patterns  
   _cites E7, E8, E9: Also flagged: Ab5257dbeab (new merchant burst, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A20de01d7ab (rapid fire, severity 5, in your queue, raised 11-14 08:26) shares agent agent_38. | Also flagged: A8f89ab1e35 (velocity spike, severity 6, in your queue, raised 11-14 08:26) shares agent agent_38._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {"claims 'just under the threshold' without support": 2}

## Note 6: AML_NEW_MERCHANT_BURST (severity 6) · seed 301

```
[E1] Rule explanation (computed by code, true): 3 first-time merchants inside 24h.
[E2] 3 payments totalling $117.59, from 1 agent to 3 merchants.
[E3] agent_12 (team finance): 3 payments, $117.59, each 21.6%–66.1% of its $100.00 approval threshold.
[E4] First payment 11-09 12:27, last 11-09 12:38: all 3 within 10 m.
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

1. **evidence** — Shows each payment is a high proportion of the agent's threshold  
   _cites E3: agent_12 (team finance): 3 payments, $117.59, each 21.6%–66.1% of its $100.00 approval threshold._
2. **evidence** — Identifies the first merchant as untrusted software  
   _cites E5: Orbit Tools (software, untrusted): 1 payment, $66.11, from 1 agent._
3. **evidence** — Identifies the second merchant as untrusted software  
   _cites E6: Pixel Forge Studio (software, untrusted): 1 payment, $29.89, from 1 agent._
4. **evidence** — Identifies the third merchant as untrusted money transfer  
   _cites E7: Swiftpay Transfer (money_transfer, untrusted): 1 payment, $21.59, from 1 agent._
5. **open_questions** — What business justification does the finance team have for using these untrusted software and transfer services?  
   _cites E5, E6, E7: Orbit Tools (software, untrusted): 1 payment, $66.11, from 1 agent. | Pixel Forge Studio (software, untrusted): 1 payment, $29.89, from 1 agent. | Swiftpay Transfer (money_transfer, untrusted): 1 payment, $21.59, from 1 agent._
6. **open_questions** — Do the other alerts sharing these merchants indicate a coordinated pattern?  
   _cites E11, E12, E13, E14, E15, E16: Also flagged: A19310559d0 (fan in, severity 7, in your queue, raised 11-09 18:01) shares merchant Orbit Tools; agent agent_12. | Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant Swiftpay Transfer. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares merchant Swiftpay Transfer; agent agent_12. | Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Orbit Tools, Swiftpay Transfer. | Also flagged: A6accdc0dcf (round amounts, severity 4, in your queue, raised 11-12 14:18) shares merchant Pixel Forge Studio. | Also flagged: A7e1b8dcd5f (velocity spike, severity 6, in your queue, raised 11-13 04:41) shares merchant Swiftpay Transfer._
7. **actions** — Request documentation of approved vendors for the finance team and verify contracts for the listed merchants.  
   _cites E5, E6, E7: Orbit Tools (software, untrusted): 1 payment, $66.11, from 1 agent. | Pixel Forge Studio (software, untrusted): 1 payment, $29.89, from 1 agent. | Swiftpay Transfer (money_transfer, untrusted): 1 payment, $21.59, from 1 agent._
8. **actions** — Cross-check the agent's recent activity against internal policy for first-time merchant usage.  
   _cites E17: Before this alert, agent_12 made 33 payments over 12 d 22 h (about 2.6 a day), mostly to Mapwise, Fernway Foods, Deskline Supplies, Northwind Air._
9. **actions** — Escalate to the senior AML team for a comprehensive review of the linked alerts.  
   _cites E11, E12, E13: Also flagged: A19310559d0 (fan in, severity 7, in your queue, raised 11-09 18:01) shares merchant Orbit Tools; agent agent_12. | Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant Swiftpay Transfer. | Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares merchant Swiftpay Transfer; agent agent_12._

Recommendation: **escalate** · checklist: time_window ✗, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✗, next_steps ✓
Dropped by the checker: {'claims a burst without support': 1, 'contains a spelled-out number': 1, "argues against the alert's computed facts": 2}

## Note 7: AML_RAPID_FIRE (severity 5) · seed 301

```
[E1] Rule explanation (computed by code, true): 16 payments with at least 15 inside 60s.
[E2] 16 payments totalling $80.00, from 1 agent to 10 merchants.
[E3] agent_27 (team finance): 16 payments, $80.00, each 2.0%–2.0% of its $250.00 approval threshold.
[E4] First payment 11-10 18:25, last 11-10 18:26: all 16 within 30 s.
[E5] Busiest stretch: 16 payments within 30 s (11-10 18:25–18:26).
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

1. **evidence** — defines rapid-fire condition met  
   _cites E1: Rule explanation (computed by code, true): 16 payments with at least 15 inside 60s._
2. **evidence** — payments are each a small percent of threshold  
   _cites E3: agent_27 (team finance): 16 payments, $80.00, each 2.0%–2.0% of its $250.00 approval threshold._
3. **evidence** — all transactions occurred within seconds  
   _cites E4: First payment 11-10 18:25, last 11-10 18:26: all 16 within 30 s._
4. **evidence** — captures the busiest stretch  
   _cites E5: Busiest stretch: 16 payments within 30 s (11-10 18:25–18:26)._
5. **evidence** — shows swift switches between merchants  
   _cites E16: agent_27 switched from Tallyhouse Software to Brightline Print Co. between 11-10 18:25 and 11-10 18:25 (2 s apart)._
6. **evidence** — other high-severity alerts involve same agent  
   _cites E22: Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27._
7. **open_questions** — Is there any documented batch payment schedule for this agent?  
   _cites E25: Before this alert, agent_27 made 60 payments over 13 d 3 h (about 4.6 a day), mostly to CityCab, Pageturn Books._
8. **open_questions** — Do any of the merchants share ownership or backend accounts?  
   _cites E6, E7, E8, E9, E10, E11, E12, E13, E14, E15: Brightline Print Co. (print, trusted): 2 payments, $10.00, from 1 agent. | CityCab (rides, trusted): 1 payment, $5.00, from 1 agent. | CoreCloud (compute, trusted): 2 payments, $10.00, from 1 agent. | Fernway Foods (food, trusted): 2 payments, $10.00, from 1 agent. | Ledgerly (software, trusted): 1 payment, $5.00, from 1 agent. | Lexa AI (ai_api, trusted): 1 payment, $5.00, from 1 agent. | Mapwise (data, trusted): 2 payments, $10.00, from 1 agent. | Northwind Air (flights, trusted): 1 payment, $5.00, from 1 agent. | Quillbase (software, trusted): 1 payment, $5.00, from 1 agent. | Tallyhouse Software (software, trusted): 3 payments, $15.00, from 1 agent._
9. **actions** — Request a business justification for the rapid multi-merchant payments from the agent's supervisor  
   _cites E3: agent_27 (team finance): 16 payments, $80.00, each 2.0%–2.0% of its $250.00 approval threshold._
10. **actions** — Verify the legitimacy and relationship of each merchant despite trusted status  
   _cites E6, E7, E8, E9, E10, E11, E12, E13, E14, E15: Brightline Print Co. (print, trusted): 2 payments, $10.00, from 1 agent. | CityCab (rides, trusted): 1 payment, $5.00, from 1 agent. | CoreCloud (compute, trusted): 2 payments, $10.00, from 1 agent. | Fernway Foods (food, trusted): 2 payments, $10.00, from 1 agent. | Ledgerly (software, trusted): 1 payment, $5.00, from 1 agent. | Lexa AI (ai_api, trusted): 1 payment, $5.00, from 1 agent. | Mapwise (data, trusted): 2 payments, $10.00, from 1 agent. | Northwind Air (flights, trusted): 1 payment, $5.00, from 1 agent. | Quillbase (software, trusted): 1 payment, $5.00, from 1 agent. | Tallyhouse Software (software, trusted): 3 payments, $15.00, from 1 agent._
11. **actions** — Cross-check the agent's activity against the other flagged alerts for patterns  
   _cites E22, E23, E24: Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27. | Also flagged: Aea86239f87 (velocity spike, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27. | Also flagged: A8a3ef664e1 (fan in, severity 7, in your queue, raised 11-15 18:45) shares agent agent_27._
12. **reason** — pattern meets rapid-fire criteria and coincides with multiple other high-severity alerts involving the same agent  
   _cites E1, E5, E22: Rule explanation (computed by code, true): 16 payments with at least 15 inside 60s. | Busiest stretch: 16 payments within 30 s (11-10 18:25–18:26). | Also flagged: A48f0463e50 (new merchant burst, severity 6, in your queue, raised 11-10 18:26) shares agent agent_27._

Recommendation: **escalate** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {"claims 'just under the threshold' without support": 1, "argues against the alert's computed facts": 1}

## Note 8: AML_ROUND_AMOUNTS (severity 4) · seed 301

```
[E1] Rule explanation (computed by code, true): 3 payments in exact multiples of $10.00.
[E2] 3 payments totalling $70.00, from 1 agent to 1 merchant.
[E3] agent_30 (team growth): 3 payments, $70.00, each 8.0%–12.0% of its $250.00 approval threshold.
[E4] First payment 11-09 16:12, last 11-09 17:10: all 3 within 57 m.
[E5] Ledgerly (software, trusted): 3 payments, $70.00, from 1 agent.
[E6] Largest payments: T0001387 $30.00 (agent_30 to Ledgerly, 11-09 17:10); T0001378 $20.00 (agent_30 to Ledgerly, 11-09 16:12); T0001385 $20.00 (agent_30 to Ledgerly, 11-09 17:00).
[E7] Also flagged: A35f7572ae2 (fan in, severity 7, in your queue, raised 11-13 09:40) shares agent agent_30.
[E8] Also flagged: Afa1aeff6e1 (structuring, severity 8, in your queue, raised 11-13 17:23) shares agent agent_30.
[E9] Also flagged: Ae645828e69 (high risk category, severity 6, in your queue, raised 11-15 14:16) shares agent agent_30.
[E10] Before this alert, agent_30 made 24 payments over 13 d 2 h (about 1.8 a day), mostly to Promptworks, DataLoom, Quillbase.
```

1. **summary** — Agent 30 made several round-amount payments to a trusted software vendor within a short period, triggering a round-amount rule.  
   _cites E1, E4: Rule explanation (computed by code, true): 3 payments in exact multiples of $10.00. | First payment 11-09 16:12, last 11-09 17:10: all 3 within 57 m._
2. **evidence** — payments represent a notable share of the agent's approval threshold  
   _cites E3: agent_30 (team growth): 3 payments, $70.00, each 8.0%–12.0% of its $250.00 approval threshold._
3. **evidence** — the recipient is a trusted software provider  
   _cites E5: Ledgerly (software, trusted): 3 payments, $70.00, from 1 agent._
4. **open_questions** — Do the other alerts linked to the same agent indicate a broader pattern of concern?  
   _cites E7, E8, E9: Also flagged: A35f7572ae2 (fan in, severity 7, in your queue, raised 11-13 09:40) shares agent agent_30. | Also flagged: Afa1aeff6e1 (structuring, severity 8, in your queue, raised 11-13 17:23) shares agent agent_30. | Also flagged: Ae645828e69 (high risk category, severity 6, in your queue, raised 11-15 14:16) shares agent agent_30._
5. **open_questions** — Could the agent's recent activity level explain the timing of these payments?  
   _cites E10: Before this alert, agent_30 made 24 payments over 13 d 2 h (about 1.8 a day), mostly to Promptworks, DataLoom, Quillbase._
6. **actions** — Review the details of the linked alerts sharing the same agent  
   _cites E7: Also flagged: A35f7572ae2 (fan in, severity 7, in your queue, raised 11-13 09:40) shares agent agent_30._
7. **actions** — Request supporting documentation for the payments to the software vendor  
   _cites E5: Ledgerly (software, trusted): 3 payments, $70.00, from 1 agent._
8. **actions** — Interview the agent's team to confirm the business purpose of the transactions  
   _cites E3: agent_30 (team growth): 3 payments, $70.00, each 8.0%–12.0% of its $250.00 approval threshold._
9. **reason** — the pattern involves round amounts within a short period to a trusted vendor, but no explicit justification is present.  
   _cites E1, E4: Rule explanation (computed by code, true): 3 payments in exact multiples of $10.00. | First payment 11-09 16:12, last 11-09 17:10: all 3 within 57 m._

Recommendation: **more_info** · checklist: time_window ✓, merchant_concentration ✓, cross_alert_links ✓, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {'contains a spelled-out number': 1, 'claims a burst without support': 1, "argues against the alert's computed facts": 1}

## Note 9: AML_STRUCTURING (severity 8) · seed 301

```
[E1] Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76.
[E2] 4 payments totalling $1,829.76, from 1 agent to 1 merchant.
[E3] agent_01 (team research): 4 payments, $1,829.76, each 88.8%–95.0% of its $500.00 approval threshold.
[E4] First payment 11-11 09:11, last 11-11 19:03: all 4 within 9 h 51 m.
[E5] QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent.
[E6] Largest payments: T0001701 $475.22 (agent_01 to QuickData Hub, 11-11 19:03); T0001569 $462.69 (agent_01 to QuickData Hub, 11-11 09:11); T0001693 $448.05 (agent_01 to QuickData Hub, 11-11 18:27); T0001606 $443.80 (agent_01 to QuickData Hub, 11-11 11:52).
[E7] Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant QuickData Hub.
[E8] Also flagged: A301dda7de9 (new merchant burst, severity 6, in your queue, raised 11-15 18:45) shares merchant QuickData Hub.
[E9] Also flagged: A8a3ef664e1 (fan in, severity 7, in your queue, raised 11-15 18:45) shares merchant QuickData Hub; agent agent_01.
[E10] Before this alert, agent_01 made 33 payments over 16 d 2 h (about 2.0 a day), mostly to Brightline Print Co., Fernway Foods, Vectorly, Quillbase.
```

1. **summary** — Agent made several payments just under the approval threshold to an untrusted merchant within a short period, indicating possible structuring  
   _cites E1, E3, E4: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76. | agent_01 (team research): 4 payments, $1,829.76, each 88.8%–95.0% of its $500.00 approval threshold. | First payment 11-11 09:11, last 11-11 19:03: all 4 within 9 h 51 m._
2. **evidence** — payments each just under the threshold  
   _cites E3: agent_01 (team research): 4 payments, $1,829.76, each 88.8%–95.0% of its $500.00 approval threshold._
3. **evidence** — merchant is flagged as untrusted data provider  
   _cites E5: QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent._
4. **evidence** — payments are among the largest near-threshold amounts  
   _cites E6: Largest payments: T0001701 $475.22 (agent_01 to QuickData Hub, 11-11 19:03); T0001569 $462.69 (agent_01 to QuickData Hub, 11-11 09:11); T0001693 $448.05 (agent_01 to QuickData Hub, 11-11 18:27); T0001606 $443.80 (agent_01 to QuickData Hub, 11-11 11:52)._
5. **open_questions** — Why does the agent repeatedly use this untrusted merchant despite other regular vendors?  
   _cites E10: Before this alert, agent_01 made 33 payments over 16 d 2 h (about 2.0 a day), mostly to Brightline Print Co., Fernway Foods, Vectorly, Quillbase._
6. **open_questions** — Are the other flagged alerts related to coordinated activity with this merchant?  
   _cites E7, E8, E9: Also flagged: A43df955213 (new merchant burst, severity 6, in your queue, raised 11-09 18:44) shares merchant QuickData Hub. | Also flagged: A301dda7de9 (new merchant burst, severity 6, in your queue, raised 11-15 18:45) shares merchant QuickData Hub. | Also flagged: A8a3ef664e1 (fan in, severity 7, in your queue, raised 11-15 18:45) shares merchant QuickData Hub; agent agent_01._
7. **actions** — Conduct a merchant risk assessment for the data provider  
   _cites E5: QuickData Hub (data, untrusted): 4 payments, $1,829.76, from 1 agent._
8. **actions** — Request a business justification from the agent's team for these payments  
   _cites E10: Before this alert, agent_01 made 33 payments over 16 d 2 h (about 2.0 a day), mostly to Brightline Print Co., Fernway Foods, Vectorly, Quillbase._
9. **actions** — Add monitoring for future near-threshold payments to this merchant  
   _cites E1: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76._
10. **reason** — pattern matches structuring with multiple near-threshold payments to an untrusted merchant  
   _cites E1: Rule explanation (computed by code, true): 4 payments each just under the $500.00 approval threshold, totalling $1,829.76._

Recommendation: **escalate** · checklist: limit_proximity ✓, time_window ✓, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {'contains a spelled-out number': 1, "argues against the alert's computed facts": 1}

## Note 10: AML_TEAM_STRUCTURING (severity 8) · seed 301

```
[E1] Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42.
[E2] 6 payments totalling $677.42, from 3 agents to 1 merchant.
[E3] agent_03 (team ops): 2 payments, $169.80, each 84.3%–85.5% of its $100.00 approval threshold.
[E4] agent_08 (team ops): 2 payments, $90.22, each 89.4%–91.0% of its $50.00 approval threshold.
[E5] agent_13 (team ops): 2 payments, $417.40, each 82.2%–84.7% of its $250.00 approval threshold.
[E6] First payment 11-10 15:03, last 11-10 18:23: all 6 within 3 h 20 m.
[E7] Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents.
[E8] Largest payments: T0001491 $211.87 (agent_13 to Halcyon Consulting, 11-10 15:49); T0001523 $205.53 (agent_13 to Halcyon Consulting, 11-10 18:14); T0001519 $85.47 (agent_03 to Halcyon Consulting, 11-10 17:57); T0001524 $84.33 (agent_03 to Halcyon Consulting, 11-10 18:23); T0001478 $45.52 (agent_08 to Halcyon Consulting, 11-10 15:03).
[E9] Also flagged: A7ad9c0c8fe (fan in, severity 7, in your queue, raised 11-10 16:55) shares agent agent_08.
[E10] Also flagged: Ac4f335a26a (fan in, severity 7, in your queue, raised 11-11 09:24) shares merchant Halcyon Consulting; agent agent_03, agent_08, agent_13.
[E11] Also flagged: A95acc79c3e (new merchant burst, severity 6, in your queue, raised 11-11 14:07) shares merchant Halcyon Consulting; agent agent_03.
[E12] Also flagged: A594066e122 (rapid fire, severity 5, in your queue, raised 11-11 14:07) shares agent agent_03.
[E13] Also flagged: Aa487cd1ab8 (velocity spike, severity 6, in your queue, raised 11-11 14:38) shares agent agent_03.
[E14] Also flagged: A1b7690874c (new merchant burst, severity 6, in your queue, raised 11-11 18:28) shares merchant Halcyon Consulting; agent agent_08.
```

1. **summary** — Several agents under the same owner made a series of payments just under approval thresholds to an untrusted merchant in a short period, indicating possible structuring  
   _cites E1: Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42._
2. **evidence** — All payments occurred within a short period  
   _cites E6: First payment 11-10 15:03, last 11-10 18:23: all 6 within 3 h 20 m._
3. **evidence** — Payments were directed to an untrusted merchant  
   _cites E7: Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents._
4. **open_questions** — Why were multiple agents used instead of a single agent?  
   _cites E3, E4, E5: agent_03 (team ops): 2 payments, $169.80, each 84.3%–85.5% of its $100.00 approval threshold. | agent_08 (team ops): 2 payments, $90.22, each 89.4%–91.0% of its $50.00 approval threshold. | agent_13 (team ops): 2 payments, $417.40, each 82.2%–84.7% of its $250.00 approval threshold._
5. **open_questions** — Are there any approved exceptions for payments near thresholds to this merchant?  
   _cites E1: Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42._
6. **actions** — Request documentation of the business purpose for these payments  
   _cites E7: Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents._
7. **actions** — Obtain information on the merchant's legitimacy and relationship to the owner  
   _cites E7: Halcyon Consulting (other, untrusted): 6 payments, $677.42, from 3 agents._
8. **actions** — Monitor future transactions from these agents for similar patterns  
   _cites E6: First payment 11-10 15:03, last 11-10 18:23: all 6 within 3 h 20 m._
9. **reason** — Pattern matches structuring criteria with multiple near-threshold payments to an untrusted merchant  
   _cites E1: Rule explanation (computed by code, true): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.42._

Recommendation: **escalate** · checklist: limit_proximity ✗, time_window ✓, merchant_concentration ✓, cross_alert_links ✗, recommendation_with_reason ✓, next_steps ✓
Dropped by the checker: {'contains a spelled-out number': 3, "argues against the alert's computed facts": 1}
