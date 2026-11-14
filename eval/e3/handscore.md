# E3 hand-score pack (10 notes)

For each sentence, mark Supported (Y/N) and Useful (Y/N) in handscore.csv. Evidence rows are the same ones the investigator saw. SIMULATED money, synthetic data.

## Note 1: AML_TEAM_STRUCTURING (severity 8) — the case you flagged in hand review

```
Alert A6c2d42955a: rule AML_TEAM_STRUCTURING, severity 8, subject owner ops.
Rule explanation (computed by code): 10 payments from 3 agents of one owner, each just under its approval threshold, totalling $3,844.39.

Transactions:
T0001998 | 2026-11-09 14:22 | agent_08 (team ops, approval threshold $500.00) | Orbit Tools (software, untrusted) | $452.45
T0001999 | 2026-11-09 11:55 | agent_08 (team ops, approval threshold $500.00) | Orbit Tools (software, untrusted) | $449.21
T0002000 | 2026-11-09 16:57 | agent_08 (team ops, approval threshold $500.00) | Orbit Tools (software, untrusted) | $492.57
T0002001 | 2026-11-09 20:41 | agent_08 (team ops, approval threshold $500.00) | Orbit Tools (software, untrusted) | $481.19
T0002002 | 2026-11-10 16:10 | agent_03 (team ops, approval threshold $100.00) | Nimbus Resell (compute, untrusted) | $89.65
T0002003 | 2026-11-10 14:15 | agent_03 (team ops, approval threshold $100.00) | Nimbus Resell (compute, untrusted) | $93.56
T0002004 | 2026-11-10 08:38 | agent_08 (team ops, approval threshold $500.00) | Nimbus Resell (compute, untrusted) | $435.21
T0002005 | 2026-11-10 15:17 | agent_08 (team ops, approval threshold $500.00) | Nimbus Resell (compute, untrusted) | $441.97
T0002006 | 2026-11-10 09:14 | agent_13 (team ops, approval threshold $500.00) | Nimbus Resell (compute, untrusted) | $484.12
T0002007 | 2026-11-10 13:06 | agent_13 (team ops, approval threshold $500.00) | Nimbus Resell (compute, untrusted) | $424.45
```

Recommendation: **escalate**

1. All transactions are directed to untrusted merchants in the software and compute categories, which heightens the risk profile

## Note 2: AML_FAN_IN (severity 7)

```
Alert A7e59c626f7: rule AML_FAN_IN, severity 7, subject merchant m_u05.
Rule explanation (computed by code): 3 different agents paid untrusted merchant 'Orbit Tools' within 24h.

Transactions:
T0002216 | 2026-11-09 17:38 | agent_12 (team finance, approval threshold $100.00) | Orbit Tools (software, untrusted) | $19.99
T0002293 | 2026-11-09 12:27 | agent_12 (team finance, approval threshold $100.00) | Orbit Tools (software, untrusted) | $66.11
T0002294 | 2026-11-09 18:01 | agent_02 (team finance, approval threshold $500.00) | Orbit Tools (software, untrusted) | $286.01
T0002295 | 2026-11-09 10:55 | agent_34 (team platform, approval threshold $50.00) | Orbit Tools (software, untrusted) | $29.97
```

Recommendation: **more_info**

1. The payments vary in size but all fall below the individual agents' approval thresholds, suggesting deliberate splitting to avoid alerts

## Note 3: AML_HIGH_RISK_CATEGORY (severity 6)

```
Alert A8c45304f2c: rule AML_HIGH_RISK_CATEGORY, severity 6, subject merchant m_u02.
Rule explanation (computed by code): 1 payments, $14.98, to a merchant in high-risk category 'gift_cards'.

Transactions:
T0002227 | 2026-11-12 16:08 | agent_36 (team research, approval threshold $250.00) | Apex Vouchers (gift_cards, untrusted) | $14.98
```

Recommendation: **more_info**

1. A single low-value payment was made to a merchant classified as high-risk gift cards, which triggers the high‑risk category rule.
2. However, the merchant is untrusted and falls within a high‑risk category, so further context about the purpose of the purchase is needed.

## Note 4: AML_LOOKALIKE_MERCHANT (severity 9)

```
Alert Aa0ea638f1f: rule AML_LOOKALIKE_MERCHANT, severity 9, subject merchant m_u11.
Rule explanation (computed by code): Paid 'C0reCloud', which resembles trusted merchant 'CoreCloud': 3 payments, $85.66.

Transactions:
T0002301 | 2026-11-10 17:46 | agent_38 (team ops, approval threshold $50.00) | C0reCloud (compute, untrusted) | $34.87
T0002302 | 2026-11-10 12:43 | agent_38 (team ops, approval threshold $50.00) | C0reCloud (compute, untrusted) | $26.29
T0002303 | 2026-11-10 12:54 | agent_38 (team ops, approval threshold $50.00) | C0reCloud (compute, untrusted) | $24.50
```

Recommendation: **escalate**

1. The agent made several payments to a merchant name that closely resembles a trusted entity, each amount staying just under the approval threshold

## Note 5: AML_TEAM_STRUCTURING (severity 8)

```
Alert A66911940a4: rule AML_TEAM_STRUCTURING, severity 8, subject owner ops.
Rule explanation (computed by code): 6 payments from 3 agents of one owner, each just under its approval threshold, totalling $677.44.

Transactions:
T0002241 | 2026-11-10 18:23 | agent_03 (team ops, approval threshold $100.00) | Halcyon Consulting (other, untrusted) | $84.34
T0002242 | 2026-11-10 17:57 | agent_03 (team ops, approval threshold $100.00) | Halcyon Consulting (other, untrusted) | $85.47
T0002243 | 2026-11-10 15:03 | agent_08 (team ops, approval threshold $50.00) | Halcyon Consulting (other, untrusted) | $45.52
T0002244 | 2026-11-10 18:10 | agent_08 (team ops, approval threshold $50.00) | Halcyon Consulting (other, untrusted) | $44.70
T0002245 | 2026-11-10 15:49 | agent_13 (team ops, approval threshold $250.00) | Halcyon Consulting (other, untrusted) | $211.88
T0002246 | 2026-11-10 18:14 | agent_13 (team ops, approval threshold $250.00) | Halcyon Consulting (other, untrusted) | $205.53
```

Recommendation: **escalate**

1. All transactions were directed to the same untrusted merchant, which reinforces the fan‑in concern for this owner

## Note 6: AML_VELOCITY_SPIKE (severity 6)

```
Alert Abfed45050d: rule AML_VELOCITY_SPIKE, severity 6, subject agent agent_27.
Rule explanation (computed by code): 18 payments in a burst, far above this agent's usual rate.

Transactions:
T0001320 | 2026-11-10 17:43 | agent_27 (team finance, approval threshold $250.00) | Pageturn Books (books, trusted) | $19.20
T0001321 | 2026-11-10 17:46 | agent_27 (team finance, approval threshold $250.00) | CityCab (rides, trusted) | $64.64
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

Recommendation: **more_info**

1. The agent executed a burst of payments within a short window, with multiple transactions recorded in rapid succession
2. All payments were directed to trusted merchants and were uniformly low in value, each at the minimal amount

## Note 7: AML_FAN_IN (severity 7)

```
Alert A19516591ae: rule AML_FAN_IN, severity 7, subject merchant m_u04.
Rule explanation (computed by code): 6 different agents paid untrusted merchant 'Swiftpay Transfer' within 24h.

Transactions:
T0002214 | 2026-11-09 18:44 | agent_35 (team growth, approval threshold $500.00) | Swiftpay Transfer (money_transfer, untrusted) | $136.31
T0002218 | 2026-11-09 12:38 | agent_12 (team finance, approval threshold $100.00) | Swiftpay Transfer (money_transfer, untrusted) | $21.60
T0002296 | 2026-11-10 16:55 | agent_00 (team growth, approval threshold $500.00) | Swiftpay Transfer (money_transfer, untrusted) | $225.14
T0002297 | 2026-11-10 10:26 | agent_04 (team platform, approval threshold $250.00) | Swiftpay Transfer (money_transfer, untrusted) | $127.62
T0002298 | 2026-11-10 08:02 | agent_33 (team ops, approval threshold $50.00) | Swiftpay Transfer (money_transfer, untrusted) | $23.43
T0002299 | 2026-11-10 15:31 | agent_08 (team ops, approval threshold $50.00) | Swiftpay Transfer (money_transfer, untrusted) | $27.62
T0002319 | 2026-11-10 09:55 | agent_35 (team growth, approval threshold $500.00) | Swiftpay Transfer (money_transfer, untrusted) | $421.52
```

Recommendation: **escalate**

1. Multiple agents across several teams made payments to the untrusted merchant Swiftpay Transfer within a short window, indicating a fan‑in pattern consistent with the rule detection

## Note 8: AML_FAN_IN (severity 7)

```
Alert A5dc119776f: rule AML_FAN_IN, severity 7, subject merchant m_u02.
Rule explanation (computed by code): 4 different agents paid untrusted merchant 'Apex Vouchers' within 24h.

Transactions:
T0002086 | 2026-11-09 18:48 | agent_28 (team ops, approval threshold $250.00) | Apex Vouchers (gift_cards, untrusted) | $46.03
T0002106 | 2026-11-10 13:29 | agent_26 (team research, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $29.00
T0002144 | 2026-11-10 05:38 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $16.87
T0002145 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $12.42
T0002146 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $13.35
T0002147 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $11.23
T0002148 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $24.39
T0002149 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $17.85
T0002150 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $25.64
T0002151 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $19.32
T0002152 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $12.32
T0002153 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $25.62
T0002154 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $25.74
T0002155 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $19.80
T0002156 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $23.27
T0002157 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $17.59
T0002158 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $14.70
T0002159 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $17.77
T0002160 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $27.35
T0002161 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $19.96
T0002162 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $10.19
T0002196 | 2026-11-09 17:05 | agent_16 (team research, approval threshold $500.00) | Apex Vouchers (gift_cards, untrusted) | $310.68
T0002197 | 2026-11-09 17:15 | agent_16 (team research, approval threshold $500.00) | Apex Vouchers (gift_cards, untrusted) | $361.68
```

Recommendation: **more_info**

1. Multiple agents across distinct teams made payments to the untrusted merchant Apex Vouchers within a short period, triggering the fan‑in red flag [T0002086][T0002106][T0002144][T0002196]
2. One agent alone generated a burst of dozens of small transactions at the same minute, further concentrating activity on the same merchant [T0002144][T0002150][T0002158][T0002162]

## Note 9: AML_HIGH_RISK_CATEGORY (severity 6)

```
Alert A67b66cf0f1: rule AML_HIGH_RISK_CATEGORY, severity 6, subject merchant m_u02.
Rule explanation (computed by code): 33 payments, $2,793.47, to a merchant in high-risk category 'gift_cards'.

Transactions:
T0002086 | 2026-11-09 18:48 | agent_28 (team ops, approval threshold $250.00) | Apex Vouchers (gift_cards, untrusted) | $46.03
T0002097 | 2026-11-11 13:55 | agent_02 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $15.45
T0002106 | 2026-11-10 13:29 | agent_26 (team research, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $29.00
T0002144 | 2026-11-10 05:38 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $16.87
T0002145 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $12.42
T0002146 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $13.35
T0002147 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $11.23
T0002148 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $24.39
T0002149 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $17.85
T0002150 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $25.64
T0002151 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $19.32
T0002152 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $12.32
T0002153 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $25.62
T0002154 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $25.74
T0002155 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $19.80
T0002156 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $23.27
T0002157 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $17.59
T0002158 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $14.70
T0002159 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $17.77
T0002160 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $27.35
T0002161 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $19.96
T0002162 | 2026-11-10 05:39 | agent_32 (team finance, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $10.19
T0002181 | 2026-11-15 15:35 | agent_33 (team ops, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $47.91
T0002182 | 2026-11-15 09:16 | agent_33 (team ops, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $63.84
T0002183 | 2026-11-15 09:45 | agent_33 (team ops, approval threshold $100.00) | Apex Vouchers (gift_cards, untrusted) | $41.06
```

Recommendation: **escalate**

1. A cluster of payments to an untrusted gift‑card merchant shows multiple agents each making amounts well under their approval limits, indicating possible structuring to avoid detection
2. The volume of transactions in a short period, especially the burst from a single agent at the same minute, matches the velocity and structuring red‑flags for high‑risk categories

## Note 10: AML_LOOKALIKE_MERCHANT (severity 9)

```
Alert A47eec2724c: rule AML_LOOKALIKE_MERCHANT, severity 9, subject merchant m_u12.
Rule explanation (computed by code): Paid 'Lexa-AI Billing', which resembles trusted merchant 'Lexa AI': 3 payments, $84.36.

Transactions:
T0002175 | 2026-11-09 15:45 | agent_03 (team ops, approval threshold $50.00) | Lexa-AI Billing (ai_api, untrusted) | $33.22
T0002176 | 2026-11-09 14:36 | agent_03 (team ops, approval threshold $50.00) | Lexa-AI Billing (ai_api, untrusted) | $17.34
T0002177 | 2026-11-09 14:20 | agent_03 (team ops, approval threshold $50.00) | Lexa-AI Billing (ai_api, untrusted) | $33.80
```

Recommendation: **escalate**

1. The agent made several payments to a merchant name that closely resembles a trusted entity, all just under the agent’s approval threshold
