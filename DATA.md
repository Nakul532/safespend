# DATA.md: existing code and facts AgentGuard may reuse

## Existing repos (clone both as references)
- ComplianceGuard AI: https://github.com/Nakul532/Complianceguard-ai (Streamlit, Python)
- AgentPay AI: https://github.com/Nakul532/agentpay-ai (Streamlit, Python)

## ComplianceGuard facts (from Nakul's earlier work; generated data, not real bank data)
- 49,937 transactions across 5,000 customers; 12 detection rules: structuring, smurfing, OFAC sanctions screening, high-risk geography, velocity, layering, TBML, cash CTR, dormancy, round-amount wires, high-risk MCC, rapid-fire transfers.
- Explainable 0–100 risk scoring; SAR narrative drafts mapped to BSA, FinCEN and OFAC.
- Alert-fatigue fix: high-risk cases cut from 6,948 to 26 by recalibrating risk-score weights (average score 97.6 → 30.8).

## AgentPay facts
- 3-agent system on Gemini 2.0 Flash (to be replaced by gpt-oss via Groq/OpenRouter).
- Mock USDC settlement under 400 ms; agent wallets with spending policies; live treasury analytics.
- MVP scoped after benchmarking Coinbase x402 and Visa Intelligent Commerce.

## Keys and budget
- GROQ_API_KEY (free) for the live site; OPENROUTER_API_KEY (prepaid, credit-limited) for evals, pinned to Groq with fallbacks off. Nakul adds keys himself.
