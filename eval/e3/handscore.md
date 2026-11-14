# E3 hand-score pack (10 notes)

For each sentence, mark Supported (Y/N) and Useful (Y/N) in handscore.csv. Evidence rows are the same ones the investigator saw. SIMULATED money, synthetic data.

## Note 1: AML_FAN_IN (severity 7)

```
Alert A7e59c626f7: rule AML_FAN_IN, severity 7, subject merchant m_u05.
Rule explanation (computed by code): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h.

Transactions:
T0002216 | 2026-11-09 17:38 | agent_12 (team finance, approval threshold $100.00) | Orbit Tools (software, untrusted) | $19.987219
T0002293 | 2026-11-09 12:27 | agent_12 (team finance, approval threshold $100.00) | Orbit Tools (software, untrusted) | $66.111432
T0002294 | 2026-11-09 18:01 | agent_02 (team finance, approval threshold $500.00) | Orbit Tools (software, untrusted) | $286.005564
T0002295 | 2026-11-09 10:55 | agent_34 (team platform, approval threshold $50.00) | Orbit Tools (software, untrusted) | $29.971903
```

Recommendation: **more_info**

1. Each payment was made by agents from separate teams—finance and platform—using their standard approval thresholds, which suggests routine procurement rather than collusion [T0002216] [T0002293] [T0002294] [T0002295].
2. The merchant is flagged as untrusted, but the amounts are modest and fall just under higher‑risk thresholds, consistent with legitimate software purchases across departments [T0002216] [T0002293] [T0002294] [T0002295].

## Note 2: AML_HIGH_RISK_CATEGORY (severity 6)

```
Alert A8c45304f2c: rule AML_HIGH_RISK_CATEGORY, severity 6, subject merchant m_u02.
Rule explanation (computed by code): 1 payments, $14.976246, to a merchant in high-risk category 'gift_cards'.

Transactions:
T0002227 | 2026-11-12 16:08 | agent_36 (team research, approval threshold $250.00) | Apex Vouchers (gift_cards, untrusted) | $14.976246
```

Recommendation: **more_info**

1. The alert involves a single payment to a merchant classified in a high‑risk category for gift cards [T0002227].
2. The amount is just under the agent's approval threshold, which may explain why it was not flagged earlier [T0002227].
3. Because the merchant is marked as untrusted, the transaction could still be legitimate if it represents a routine purchase for research purposes [T0002227].
4. However, the combination of a high‑risk merchant and a payment that skirts the approval limit warrants further clarification [T0002227].

## Note 3: AML_LOOKALIKE_MERCHANT (severity 9)

```
Alert Aa0ea638f1f: rule AML_LOOKALIKE_MERCHANT, severity 9, subject merchant m_u11.
Rule explanation (computed by code): Paid 'C0reCloud', which resembles trusted merchant 'CoreCloud': 3 payments, $85.65627.

Transactions:
T0002301 | 2026-11-10 17:46 | agent_38 (team ops, approval threshold $50.00) | C0reCloud (compute, untrusted) | $34.867484
T0002302 | 2026-11-10 12:43 | agent_38 (team ops, approval threshold $50.00) | C0reCloud (compute, untrusted) | $26.286882
T0002303 | 2026-11-10 12:54 | agent_38 (team ops, approval threshold $50.00) | C0reCloud (compute, untrusted) | $24.501904
```

Recommendation: **clear**

1. Each payment is below the agent's approval threshold, indicating they were authorized without higher‑level review.
2. The transactions occurred within a short time window on the same day, suggesting routine activity rather than structuring.
3. The merchant is classified as untrusted, but the similarity to a trusted name appears to be a naming coincidence rather than intentional fraud.

## Note 4: AML_NEW_MERCHANT_BURST (severity 6)

```
Alert Af8b5bd96bf: rule AML_NEW_MERCHANT_BURST, severity 6, subject agent agent_12.
Rule explanation (computed by code): 3 first-time merchants inside 24h.

Transactions:
T0002217 | 2026-11-09 12:27 | agent_12 (team finance, approval threshold $100.00) | Pixel Forge Studio (software, untrusted) | $29.891462
T0002218 | 2026-11-09 12:38 | agent_12 (team finance, approval threshold $100.00) | Swiftpay Transfer (money_transfer, untrusted) | $21.595508
T0002293 | 2026-11-09 12:27 | agent_12 (team finance, approval threshold $100.00) | Orbit Tools (software, untrusted) | $66.111432
```

Recommendation: **more_info**

1. They occurred within a short window and each merchant is flagged as untrusted
2. The amounts are well below the agent’s approval threshold, which could explain the lack of internal review
3. However the rapid succession of first‑time merchants may indicate a testing or layering behavior, warranting further clarification

## Note 5: AML_RAPID_FIRE (severity 5)

```
Alert Ab8db42ee72: rule AML_RAPID_FIRE, severity 5, subject agent agent_27.
Rule explanation (computed by code): 16 payments with at least 15 inside 60s.

Transactions:
T0001984 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Tallyhouse Software (software, trusted) | $5.00
T0001985 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Brightline Print Co. (print, trusted) | $5.00
T0001986 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Quillbase (software, trusted) | $5.00
T0001987 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | CoreCloud (compute, trusted) | $5.00
T0001988 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Fernway Foods (food, trusted) | $5.00
T0001989 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Ledgerly (software, trusted) | $5.00
T0001990 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | CityCab (rides, trusted) | $5.00
T0001991 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Northwind Air (flights, trusted) | $5.00
T0001992 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Tallyhouse Software (software, trusted) | $5.00
T0001993 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Mapwise (data, trusted) | $5.00
T0001994 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Mapwise (data, trusted) | $5.00
T0001995 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Lexa AI (ai_api, trusted) | $5.00
T0001996 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | CoreCloud (compute, trusted) | $5.00
T0001997 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Brightline Print Co. (print, trusted) | $5.00
T0001998 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Fernway Foods (food, trusted) | $5.00
T0001999 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Tallyhouse Software (software, trusted) | $5.00
```

Recommendation: **clear**

1. The agent executed a burst of payments to a variety of trusted merchants within a very short window, with several transactions occurring at the same minute and the remainder within the next minute [T0001984 T0001985 T0001986 T0001987 T0001988 T0001989 T0001990 T0001991 T0001992 T0001993 T0001994 T0001995 T0001996 T0001997 T0001998 T0001999].
2. All recipients are flagged as trusted and the amounts are well below the agent's approval threshold, which reduces the risk of illicit intent [T0001984 T0001999].
3. The pattern resembles routine automated procurement or system testing rather than structuring or layering, especially given the agent's history of occasional legitimate payments to similar merchants such as CityCab [T0001990].

## Note 6: AML_ROUND_AMOUNTS (severity 4)

```
Alert Ace44491292: rule AML_ROUND_AMOUNTS, severity 4, subject agent agent_30.
Rule explanation (computed by code): 3 payments in exact multiples of $10.00.

Transactions:
T0002185 | 2026-11-09 16:12 | agent_30 (team growth, approval threshold $250.00) | Ledgerly (software, trusted) | $20.00
T0002186 | 2026-11-09 17:10 | agent_30 (team growth, approval threshold $250.00) | Ledgerly (software, trusted) | $30.00
T0002187 | 2026-11-09 17:00 | agent_30 (team growth, approval threshold $250.00) | Ledgerly (software, trusted) | $20.00
```

Recommendation: **clear**

1. They were made to a trusted software vendor and are well below the agent's approval threshold
2. Such round‑amount payments to a regular vendor are common and can be explained by routine subscription or licensing fees

## Note 7: AML_STRUCTURING (severity 8)

```
Alert Ae623be73af: rule AML_STRUCTURING, severity 8, subject agent agent_01.
Rule explanation (computed by code): 4 payments each just under the $500.00 approval threshold, totalling $1,829.785731.

Transactions:
T0002234 | 2026-11-11 09:11 | agent_01 (team research, approval threshold $500.00) | QuickData Hub (data, untrusted) | $462.696877
T0002235 | 2026-11-11 11:52 | agent_01 (team research, approval threshold $500.00) | QuickData Hub (data, untrusted) | $443.809894
T0002236 | 2026-11-11 18:27 | agent_01 (team research, approval threshold $500.00) | QuickData Hub (data, untrusted) | $448.055927
T0002237 | 2026-11-11 19:03 | agent_01 (team research, approval threshold $500.00) | QuickData Hub (data, untrusted) | $475.223033
```

Recommendation: **escalate**

1. This pattern matches the structuring rule, which flags multiple sub‑threshold transactions that together approach a larger amount
2. While the agent’s history shows payments to other vendors, the concentration on a single untrusted merchant could be explained by a legitimate project requiring frequent data pulls

## Note 8: AML_TEAM_STRUCTURING (severity 8)

```
Alert A66911940a4: rule AML_TEAM_STRUCTURING, severity 8, subject owner ops.
Rule explanation (computed by code): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.442546.

Transactions:
T0002241 | 2026-11-10 18:23 | agent_03 (team ops, approval threshold $100.00) | Halcyon Consulting (other, untrusted) | $84.337011
T0002242 | 2026-11-10 17:57 | agent_03 (team ops, approval threshold $100.00) | Halcyon Consulting (other, untrusted) | $85.472685
T0002243 | 2026-11-10 15:03 | agent_08 (team ops, approval threshold $50.00) | Halcyon Consulting (other, untrusted) | $45.522597
T0002244 | 2026-11-10 18:10 | agent_08 (team ops, approval threshold $50.00) | Halcyon Consulting (other, untrusted) | $44.704244
T0002245 | 2026-11-10 15:49 | agent_13 (team ops, approval threshold $250.00) | Halcyon Consulting (other, untrusted) | $211.875689
T0002246 | 2026-11-10 18:14 | agent_13 (team ops, approval threshold $250.00) | Halcyon Consulting (other, untrusted) | $205.53032
```

Recommendation: **escalate**

1. This pattern matches a classic structuring scenario where amounts are deliberately kept below limits to avoid detection [T0002241,T0002242,T0002243,T0002244,T0002245,T0002246].
2. However, the transactions could be explained innocently if the payments represent separate legitimate invoices that happen to fall just under the thresholds [T0002241,T0002242,T0002243,T0002244,T0002245,T0002246].

## Note 9: AML_VELOCITY_SPIKE (severity 6)

```
Alert Abfed45050d: rule AML_VELOCITY_SPIKE, severity 6, subject agent agent_27.
Rule explanation (computed by code): 18 payments in a burst, far above this agent's usual rate.

Transactions:
T0001320 | 2026-11-10 17:43 | agent_27 (team finance, approval threshold $250.00) | Pageturn Books (books, trusted) | $19.20021
T0001321 | 2026-11-10 17:46 | agent_27 (team finance, approval threshold $250.00) | CityCab (rides, trusted) | $64.635454
T0001984 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Tallyhouse Software (software, trusted) | $5.00
T0001985 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Brightline Print Co. (print, trusted) | $5.00
T0001986 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Quillbase (software, trusted) | $5.00
T0001987 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | CoreCloud (compute, trusted) | $5.00
T0001988 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Fernway Foods (food, trusted) | $5.00
T0001989 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Ledgerly (software, trusted) | $5.00
T0001990 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | CityCab (rides, trusted) | $5.00
T0001991 | 2026-11-10 18:25 | agent_27 (team finance, approval threshold $250.00) | Northwind Air (flights, trusted) | $5.00
T0001992 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Tallyhouse Software (software, trusted) | $5.00
T0001993 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Mapwise (data, trusted) | $5.00
T0001994 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Mapwise (data, trusted) | $5.00
T0001995 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Lexa AI (ai_api, trusted) | $5.00
T0001996 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | CoreCloud (compute, trusted) | $5.00
T0001997 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Brightline Print Co. (print, trusted) | $5.00
T0001998 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Fernway Foods (food, trusted) | $5.00
T0001999 | 2026-11-10 18:26 | agent_27 (team finance, approval threshold $250.00) | Tallyhouse Software (software, trusted) | $5.00
```

Recommendation: **clear**

1. The agent executed a rapid series of low‑value payments to a range of trusted merchants, with several transactions clustered within the same minute and others spaced just minutes apart
2. All merchants are on the agent’s approved list and the amounts are well below the approval threshold, matching the typical pattern of routine operational expenses
3. The burst is explained by a batch of small purchases likely for routine supplies and services rather than an attempt to evade controls

## Note 10: AML_FAN_IN (severity 7)

```
Alert A19516591ae: rule AML_FAN_IN, severity 7, subject merchant m_u04.
Rule explanation (computed by code): 6 different agents paid untrusted merchant 'Swiftpay Transfer' within 24h.

Transactions:
T0002214 | 2026-11-09 18:44 | agent_35 (team growth, approval threshold $500.00) | Swiftpay Transfer (money_transfer, untrusted) | $136.305836
T0002218 | 2026-11-09 12:38 | agent_12 (team finance, approval threshold $100.00) | Swiftpay Transfer (money_transfer, untrusted) | $21.595508
T0002296 | 2026-11-10 16:55 | agent_00 (team growth, approval threshold $500.00) | Swiftpay Transfer (money_transfer, untrusted) | $225.139882
T0002297 | 2026-11-10 10:26 | agent_04 (team platform, approval threshold $250.00) | Swiftpay Transfer (money_transfer, untrusted) | $127.615566
T0002298 | 2026-11-10 08:02 | agent_33 (team ops, approval threshold $50.00) | Swiftpay Transfer (money_transfer, untrusted) | $23.434362
T0002299 | 2026-11-10 15:31 | agent_08 (team ops, approval threshold $50.00) | Swiftpay Transfer (money_transfer, untrusted) | $27.62301
T0002319 | 2026-11-10 09:55 | agent_35 (team growth, approval threshold $500.00) | Swiftpay Transfer (money_transfer, untrusted) | $421.515966
```

Recommendation: **more_info**

1. One agent, agent_35, appears twice, further concentrating activity on the same merchant [T0002214,T0002319]
2. All payments are below the agents' approval thresholds, so they passed internal controls but still involve an untrusted recipient, which could be benign if the merchant provides a legitimate service used by multiple teams [T0002214,T0002218,T0002296,T0002297,T0002298,T0002299,T0002319]
