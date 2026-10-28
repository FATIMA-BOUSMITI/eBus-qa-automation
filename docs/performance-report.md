# Measured JMeter performance smoke

Execution: 2026-10-26 UTC. Tool: native Apache JMeter 5.6.3, distribution verified with Apache SHA-512. Target: dedicated local QA Spring backend and PostgreSQL. **One user, one iteration, seven HTTP samples**, paced by 500 ms timer intervals.

| Measured quantity | Result |
| --- | ---: |
| HTTP samples | 7 |
| Failed samples | 0 |
| Error rate | 0% |
| Mean response time | 311.71 ms |
| P90 / P95 / P99 | 604 / 604 / 604 ms |
| Measured first-start to last-completion interval | 5.420 s |
| Throughput over that interval | 1.292 requests/s |

Samplers: health, bus catalogue, line catalogue, ticket catalogue, synthetic login, current subscription and subscription history. Every sampler asserted HTTP 200. JTL/Dashboard evidence is under `reports/jmeter/native-20261026-184823/`; `summary.json` was produced at `2026-10-26T18:48:58.8952824Z`.

Percentiles use nearest rank. With seven heterogeneous samples, all three high percentiles select the maximum sample. These values are not a reliable latency distribution or capacity measurement. Throughput includes configured pacing in the observed interval and does not estimate maximum server throughput. No performance acceptance threshold was agreed, so no SLA claim is made.

The progressive profile (five users, 30-second ramp, 60 seconds) and endurance profile (two users, 300 seconds) are **not executed**. Further work: agree local resource/traffic limits and acceptance criteria, collect repeated homogeneous endpoint samples and server resource metrics, then perform an explicitly authorized run. Never extrapolate this smoke result to Render performance.
