# Multi-Tenant Environment Isolation in Data Centre Information Systems

Reproducibility artifacts for the ISD 2026 (Prague) poster:
**A Comparative Study of Commercial and Open-Source Load Balancers**
(F5 BIG-IP LTM vs. HAProxy + Keepalived).

This repository contains the configurations, topology details, and
measurement scripts used to evaluate multi-tenant isolation, traffic
distribution, and high availability of the two stacks on a single-site,
IPv6-only testbed (VMware Workstation 17.6.4, isolated LAN segments).

> All addressing uses the documentation prefix `2001:db8::/32`.
> Two tenants: **A = healthcare.com** (`2001:db8:_a_::/48`),
> **B = fitness.com** (`2001:db8:_b_::/48`).
> The leading nibble of the third hextet selects the stack:
> **F5 = `1`**, **HAProxy = `2`**.

## Repository structure

```
.
├── f5/                     # Commercial ADC (F5 BIG-IP LTM VE)
│   └── final.ucs           # Full F5 configuration archive (UCS)
├── haproxy/                # Open-source stack (HAProxy + Keepalived on Linux)
│   ├── haproxy-hp-a.cfg            # HAProxy configuration
│   ├── keepalived-hp-a.conf        # Keepalived (VRRPv3) configuration
│   ├── check-haproxy.sh.txt        # Health-check helper script
│   ├── ipv6-addresses.txt          # Per-tenant IPv6 addressing plan
│   ├── ipv6-rules.txt              # VRF / VLAN / routing rules (ip vrf, 802.1Q)
│   ├── all-links-detailed.txt      # Interface / link inventory
│   ├── haproxy-version.txt         # Pinned HAProxy version
│   ├── keepalived-version.txt      # Pinned Keepalived version
│   └── kernel-version.txt          # Pinned kernel version
├── scripts/                # Measurement harness
│   ├── t4-node-error/      # T4 — pool-member failure (partial degradation)
│   └── t5-failover/        # T5 — load-balancer VIP takeover (Keepalived)
└── README.md
```

## Test environment

| Component        | Detail                                                      |
|------------------|-------------------------------------------------------------|
| Virtualisation   | VMware Workstation 17.6.4, isolated LAN segments            |
| Commercial stack | F5 BIG-IP LTM VE (single instance) — routing domains `%10`/`%20`, administrative partitions, strict isolation |
| Open-source stack| Single HAProxy on a Linux VM + Keepalived (VRRPv3)          |
| Data plane isolation | F5: routing domains (strict) · HAProxy: Linux VRF (`ip vrf`, tables 110/120) over per-tenant VLANs (10/20) |
| Tenants          | A = healthcare.com, B = fitness.com (3-member pool each)    |

Exact software versions are pinned in `haproxy/*-version.txt`.

## Experiments

| ID  | Scenario                          | Artifacts                          |
|-----|-----------------------------------|------------------------------------|
| T1a | Traffic distribution (Round Robin)| `scripts/` output (per-backend hits, latency) |
| T1b | Host-header L7 steering           | `scripts/` output (100% correct routing) |
| T2  | Cross-tenant data plane isolation | leak test (cross-tenant blocked, same-tenant reachable) |
| T3  | Management plane isolation        | partitions/RBAC (F5) vs. operator-discipline note (HAProxy) |
| T4  | Pool-member failure               | `scripts/t4-node-error/` (n=30)    |
| T5  | LB failover / VIP takeover        | `scripts/t5-failover/` (n=32, open-source stack) |
| T6  | CPU utilisation sanity check      | captured during T1                 |

> **Note on F5 measurements.** The F5 BIG-IP runs on a **trial VE
> licence**, which enforces a data-plane throughput policer
> (~1 Mbps). F5 throughput and latency are therefore **not** comparable
> to the open-source stack and are excluded; only correctness
> (distribution, L7 steering, isolation) is reported for F5. A symmetric
> F5 active/standby failover (T5) could not be established in the
> available window and is left to future work.
