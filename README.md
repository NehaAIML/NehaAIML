# Neha Purohit

**Infrastructure & Security Engineering Leader | High-Throughput Compute, Kernel Telemetry & Zero-Trust Cloud Platforms**

Architecting and operating performance-critical infrastructure, low-overhead security control planes, and automated policy engines across large-scale distributed fleets and multi-cloud environments.

---

### Core Technical Pillars

* **Kernel & Fabric-Level Observability**: Zero-overhead in-kernel instrumentation via eBPF tracepoints and lockless ringbuffers, eliminating process execution jitter in long-running semiconductor (EDA) and HPC simulations.
* **SmartNIC / DPU Security Offload**: Moving packet classification, microsegmentation, and RoCEv2 fabric governance off host CPU cores onto dedicated hardware accelerators.
* **Workload Identity & Ephemeral Secrets**: Just-In-Time credential federation (SPIFFE/SPIRE, HashiCorp Vault) bound directly to cluster batch schedulers (Slurm / LSF).
* **Policy-as-Code & Automated Evidence**: Continuous admission gates (Open Policy Agent / Rego) enforcing hardware fabric isolation (InfiniBand PKeys) and converting SOC2 / ISO27001 compliance into verifiable engineering outputs.

---

### Featured Systems Infrastructure

| Repository | Focus & Architecture | Key Technologies |
| :--- | :--- | :--- |
| [**ebpf-hpc-flow-guard**](https://github.com/NehaAIML/ebpf-hpc-flow-guard) | In-kernel telemetry probe reducing syscall monitoring latency to <0.18µs without thread stalls | Go, C, eBPF, Linux Kernel |
| [**slurm-ephemeral-iam-broker**](https://github.com/NehaAIML/slurm-ephemeral-iam-broker) | Ephemeral credential broker injecting scoped SPIFFE identities at Slurm job prolog/epilog | Go, Slurm SPANK, SPIFFE, Vault |
| [**dpu-offload-packet-inspector**](https://github.com/NehaAIML/dpu-offload-packet-inspector) | Line-rate out-of-band packet classifier and RoCEv2 firewall preserving 100% of host compute | Python, SmartNIC/DPU, RoCEv2 |
| [**eda-cluster-policy-enforcer**](https://github.com/NehaAIML/eda-cluster-policy-enforcer) | Zero-trust admission controller enforcing InfiniBand partitioning and automated SOC2 audit gates | Go, OPA, Rego, InfiniBand |
| [**autonomous-executive-agent**](https://github.com/NehaAIML/autonomous-executive-agent) | Event-driven, zero-host-tax email intelligence pipeline with local/cloud fallback execution | Python, Groq, Ollama, GitHub Actions |

---

### Contact & Collaboration
* **Location**: Los Angeles, CA
* **Portfolio**: [github.com/NehaAIML](https://github.com/NehaAIML)
