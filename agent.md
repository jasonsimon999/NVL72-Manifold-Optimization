# AGENT.md — GB200 NVL72 Rack Thermal/Hydraulic Manifold Optimization

**Project:** Calculation-based optimization of the liquid-cooling distribution system for an NVIDIA GB200 NVL72–class rack  
**Primary use:** Engineering model, design-space exploration, and optimization of rack supply/return manifolds, tray branch flows, pressure drop, pump power, and coolant temperatures  
**Research date:** 2026-09-11  
**System focus:** NVIDIA GB200 NVL72, especially the 72-GPU single-rack configuration and Dell/HPE/OCP implementations derived from NVIDIA’s reference design

---

## 0. Agent mission

You are an engineering-analysis agent tasked with building and improving a **physics-based hydraulic and thermal model of an NVIDIA GB200 NVL72 liquid-cooled rack**.

The final model must be able to answer questions such as:

1. How much coolant flow should each of the 18 compute trays and 9 NVLink switch trays receive?
2. How do supply- and return-manifold pressure gradients create tray-to-tray flow maldistribution?
3. How much pressure drop occurs in:
   - rack headers/manifolds,
   - tray branches,
   - quick disconnects / blind-mate couplings,
   - hoses/tubing,
   - cold plates,
   - valves/fittings,
   - the CDU secondary circuit?
4. What tray outlet temperatures result from a given workload and flow distribution?
5. What rack flow, pump head, and pump power are required?
6. How does manifold geometry affect:
   - maximum chip/coolant temperature,
   - flow maldistribution,
   - total pressure drop,
   - pumping power?
7. Can an optimized tapered manifold and/or tuned branch restrictions outperform a conventional constant-diameter manifold?
8. Does the optimized design remain compatible with plausible CDU operating envelopes and facility-water conditions?

The intended final outcome is **not** a replica of NVIDIA’s proprietary internal design. Public data are incomplete. The goal is an **NVL72-inspired, literature- and vendor-grounded engineering model** that is transparent about which quantities are verified, derived, estimated, or assumed.

---

# 1. Evidence and confidence rules

Every number used in the model must be tagged internally as one of the following:

- **[NVIDIA]** — explicitly published by NVIDIA.
- **[OEM]** — explicitly published by a system OEM such as Dell, HPE, QCT, Lenovo, Vertiv, Motivair, Delta, etc.
- **[OCP]** — published by the Open Compute Project or in NVIDIA’s OCP contribution.
- **[3P]** — credible third-party technical source such as ServeTheHome, SemiAnalysis, or an engineering conference slide.
- **[DERIVED]** — calculated directly from published values.
- **[ESTIMATE]** — engineering estimate used where public data do not exist.
- **[ASSUMPTION]** — chosen modeling input, to be swept in sensitivity analysis.

Never silently convert an estimate into a fact.

If two sources disagree:
1. prefer newer first-party information for the exact platform,
2. preserve both values,
3. explain why they may differ,
4. model the uncertainty as a range.

---

# 2. What the GB200 NVL72 physically is

The GB200 NVL72 is a rack-scale NVIDIA system in which 72 Blackwell GPUs are connected into one large NVLink domain.

## 2.1 Core rack topology

For the 72-GPU single-rack configuration:

- **18 compute trays**
- **4 Blackwell GPUs per compute tray**
- **2 Grace CPUs per compute tray**
- therefore:
  - **72 Blackwell GPUs**
  - **36 Grace CPUs**
- **9 NVLink switch trays**
- **2 NVSwitch ASICs per switch tray**
- therefore:
  - **18 NVSwitch ASICs**
- management/top-of-rack switches
- power shelves
- rack busbar
- NVLink cable-cartridge backplane
- rack-level supply and return liquid-cooling manifolds

[NVIDIA]

NVIDIA’s DGX GB rack documentation states that each NVL72 rack has 18 1RU compute trays and 9 1RU NVLink switch trays.

Source:  
NVIDIA DGX GB Rack Scale Systems User Guide — Hardware  
https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html

NVIDIA’s SuperPOD documentation states that each switch tray contains 2 NVLink switch chips.

Source:  
https://docs.nvidia.com/dgx-superpod/reference-architecture-scalable-infrastructure-gb200/latest/dgx-superpod-components.html

---

## 2.2 Approximate vertical arrangement

Public rack diagrams show:

- a block of compute trays above the NVLink switch region,
- 9 NVLink switch trays grouped near the middle,
- another block of compute trays below,
- power shelves distributed in the rack,
- coolant manifolds running vertically at the rear,
- blind-mate liquid connections at each tray.

NVIDIA rack-management examples place:
- lower compute trays around rack positions 11–18,
- switch trays around positions 19–27,
- upper compute trays around positions 28–35+.

Exact OEM rack positions can vary, and Dell explicitly notes that customer configurations are not all identical.

For hydraulic modeling, do **not** hard-code exact vertical positions as universal truth. Instead define the 27 liquid-cooled tray branch elevations parametrically.

Suggested branch order for a reference model:

```text
Top of rack

C18
C17
C16
C15
C14
C13
C12
C11
C10
S9
S8
S7
S6
S5
S4
S3
S2
S1
C8
C7
C6
C5
C4
C3
C2
C1

Bottom / CDU connection region
```

A 27th hydraulic branch can be represented if the OEM layout includes an additional distinct liquid-cooled infrastructure branch; otherwise the primary tray branches are the **18 compute + 9 switch = 27** liquid-cooled trays.

---

# 3. Electrical power and heat-load model

This section is critical. Electrical power consumed inside the rack eventually becomes heat.

## 3.1 NVIDIA rack design power

NVIDIA documentation describes the GB200 NVL72 rack as approximately:

- **120 kW rack power**
- approximately **85% liquid cooled / 15% air cooled** in earlier GB200 reference material.

[NVIDIA]

NVIDIA’s GB200 partition guide labels the rack approximately:

- 120 kW
- ~2900 lb
- ~85% LC / 15% air

Source:  
https://docs.nvidia.com/multi-node-nvlink-systems/partition-guide-v1-2.pdf

NVIDIA’s current rack documentation also states approximately 120 kW power consumption.

Source:  
https://docs.nvidia.com/dgx/dgxgb200-user-guide/dgxgb200-user-guide.pdf

---

## 3.2 NVIDIA current per-component power budgeting

A particularly useful NVIDIA Mission Control power-budget example gives:

### Per GPU
- **1.2 kW max power per GB200 Blackwell GPU**

### Per compute node/tray
- four GPUs:  
  \[
  4(1.2)=4.8\text{ kW}
  \]
- GPU + CPU PRS-managed power:
  \[
  5.8\text{ kW}
  \]
- therefore the two Grace CPUs are budgeted at:
  \[
  5.8-4.8=1.0\text{ kW}
  \]
- or approximately:
  \[
  0.5\text{ kW per Grace CPU}
  \]

[NVIDIA]

Source:  
NVIDIA Mission Control Software Administration Guide — Power Resource Scheduler FAQ  
https://docs.nvidia.com/mission-control/docs/systems-administration-guide/2.2.0/prs/faq.html

### Rack totals from this breakdown

GPU power:

\[
72(1.2)=86.4\text{ kW}
\]

CPU power:

\[
36(0.5)=18.0\text{ kW}
\]

GPU + CPU:

\[
86.4+18.0=104.4\text{ kW}
\]

---

## 3.3 NVLink switch tray power

NVIDIA Dynamic Power Software documentation recommends using a GB200 rack static NVSwitch aggregate of:

\[
11{,}160\text{ W}
\]

for all 9 switch trays.

[NVIDIA]

Therefore:

\[
P_{\text{switch tray,avg}}
=
\frac{11.16}{9}
=
1.24\text{ kW/tray}
\]

This value is extremely useful for the hydraulic model.

Source:  
NVIDIA Dynamic Power Software runbook  
https://docs.nvidia.com/datacenter/dps/versions/0.8/guides/runbooks/maxlps-simple-mode-pilot/

---

## 3.4 Coherent liquid heat-load decomposition

Using NVIDIA’s published power budgets:

| Component | Count | Power each | Total |
|---|---:|---:|---:|
| Blackwell GPU | 72 | 1.2 kW | 86.4 kW |
| Grace CPU | 36 | 0.5 kW | 18.0 kW |
| NVLink switch tray aggregate | 9 trays | ~1.24 kW/tray | 11.16 kW |
| **Modeled high-power liquid load** |  |  | **115.56 kW** |

[DERIVED]

This is an unusually strong cross-check because HPE independently specifies:

- **132 kW total rack power**
- **115 kW liquid cooled**
- **17 kW air cooled**

[OEM]

Source:  
HPE NVIDIA GB200 NVL72 product page / data sheet  
https://buy.hpe.com/us/en/compute/rack-scale-system/nvidia-nvl-system/nvidia-gb200-nvl72-by-hpe/p/1014890104  
https://www.hpe.com/psnow/generateDDS/NVIDIA%20GB200%20NVL72%20by%20HPE%20data%20sheet-PSN1014890104IEEN.pdf

Thus the NVIDIA component power budget gives:

\[
115.56\text{ kW}
\]

which is essentially identical to HPE’s:

\[
115\text{ kW liquid load}
\]

This should be the **preferred high-load liquid-side thermal model**.

---

## 3.5 Recommended project heat-load cases

Implement at least three thermal cases.

### Case A — NVIDIA nominal reference
- total rack electrical: 120 kW
- liquid fraction: ~85%
- liquid load:
  \[
  Q_L \approx 102\text{ kW}
  \]

### Case B — component-resolved full-load model
- GPU load: 86.4 kW
- CPU load: 18.0 kW
- NVSwitch load: 11.16 kW
- liquid load:
  \[
  Q_L=115.56\text{ kW}
  \]

### Case C — HPE/OEM full-rack envelope
- rack: 132 kW
- liquid: 115 kW
- air: 17 kW

Use **Case B** as the primary manifold optimization case because it resolves the 27 tray branch heat loads.

---

# 4. Tray-level thermal loads

## 4.1 Compute tray

Each compute tray:

- 4 GPUs:
  \[
  4(1.2)=4.8\text{ kW}
  \]
- 2 Grace CPUs:
  \[
  2(0.5)=1.0\text{ kW}
  \]

Therefore:

\[
\boxed{Q_{\text{compute tray}}\approx5.8\text{ kW}}
\]

[NVIDIA + DERIVED]

There may be additional liquid-cooled NIC / I/O components depending on OEM implementation. NVIDIA describes hybrid cooling in which Grace CPU, Blackwell GPU, ConnectX, NVLink switch ASICs, and in some configurations OSFPs are liquid cooled, while remaining components are air cooled.

Source:  
https://docs.nvidia.com/multi-node-nvlink-systems/multi-node-tuning-guide/system.html

For first-order modeling, use **5.8 kW per compute tray** and treat extra auxiliary liquid load as a sensitivity parameter.

---

## 4.2 NVLink switch tray

Recommended rack-level aggregate:

\[
11.16\text{ kW}
\]

Nine trays gives:

\[
\boxed{Q_{\text{switch tray}}\approx1.24\text{ kW}}
\]

[NVIDIA + DERIVED]

---

## 4.3 Why equal flow per tray is not thermally optimal

A compute tray dissipates:

\[
5.8\text{ kW}
\]

A switch tray dissipates:

\[
1.24\text{ kW}
\]

Therefore the heat-load ratio is:

\[
\frac{5.8}{1.24}\approx4.68
\]

If identical coolant temperature rise is desired:

\[
\dot m_i
=
\frac{Q_i}{c_p\Delta T}
\]

then compute trays should receive approximately **4.7× the coolant mass flow of switch trays**.

This is a key project opportunity.

A manifold optimized only for **equal branch flow** may actually be thermally inferior to a manifold optimized for **heat-load-proportional flow**.

Therefore define two possible objective formulations:

### Hydraulic uniformity objective
\[
\dot m_i \approx \dot m_j
\]

### Thermal uniformity objective
\[
\frac{\dot m_i}{Q_i}
\approx
\frac{\dot m_j}{Q_j}
\]

The second is usually more meaningful for a heterogeneous NVL72 rack.

---

# 5. Liquid-cooling architecture

## 5.1 Two-loop concept

A typical NVL72 liquid-cooling system contains:

### Secondary / Technology Cooling System (TCS) loop
This is the clean IT-side coolant loop.

Flow path:

```text
CDU secondary supply
        |
        v
rack cold supply manifold
        |
        +--> compute tray branches
        +--> NVLink switch tray branches
        |
rack hot return manifold
        |
        v
CDU secondary return
```

### Primary / Facility Water System (FWS) loop
This loop carries heat away from the CDU to the data-center heat-rejection infrastructure.

Flow path:

```text
facility water supply
        |
        v
CDU plate heat exchanger
        |
        v
facility water return
        |
        v
dry cooler / cooling tower / chiller / heat reuse
```

The CDU therefore:
1. hydraulically isolates the clean IT loop from facility water,
2. pumps the IT coolant,
3. filters it,
4. controls secondary supply temperature,
5. transfers heat through a liquid-to-liquid heat exchanger,
6. monitors flow, pressure, temperatures, alarms, and leakage.

---

# 6. Rack manifolds and blind-mate tray connections

NVIDIA’s GB200 OCP contribution explicitly includes:

- enhanced blind-mate liquid-cooling manifolds,
- floating blind-mate tray connections,
- rack manifolds capable of handling the rack cooling requirement,
- tray blind-mate geometry intended to tolerate alignment variation.

[NVIDIA/OCP]

Source:  
https://developer.nvidia.com/blog/?p=90182

ServeTheHome’s Dell factory tour shows the Dell IR7000 implementation using:

- hot and cold vertical rack manifolds,
- blind-mate liquid nozzles aligned with each tray,
- no need for a technician to manually attach hoses to each tray during service,
- CDU at the bottom / rack cooling infrastructure,
- rear power busbar and NVLink cable cartridges integrated around the cooling manifolds.

[3P — direct observation of Dell factory]

Source:  
https://www.servethehome.com/inside-the-dell-factory-that-builds-ai-factories/3/

The Dell article also emphasizes that IR7000 builds vary with customer CDU, rack, power, and facility requirements.

Source:  
https://www.servethehome.com/inside-the-dell-factory-that-builds-ai-factories/

---

# 7. Published coolant temperature and flow envelopes

## 7.1 QCT implementation

QCT publishes an NVL72 cooling example with:

- maximum liquid inlet temperature: **45°C**
- maximum liquid return temperature: **65°C**
- rack flow up to approximately **130 LPM**
- liquid heat requirement approximately **115 kW**
- air heat requirement approximately **17 kW**

[OEM]

Source:  
QCT QoolRack / GB200 NVL72 thermal-management publication  
https://blog.qct.io/wp-content/uploads/2025/04/QCT-Qoolrack-Stand-Alone_Advanced-Liquid-Cooling-for-NVIDIA-GB200-NVL72-Systems.pdf

Important:

**45°C and 65°C are maximum acceptance limits, not a mandatory 20 K operating delta-T.**

Do not automatically model:

\[
45\rightarrow65^\circ C
\]

as the nominal operating point.

---

## 7.2 QCT standalone cooling example

QCT also describes a cooling solution operating around:

- ~110 LPM for a 75 kW operating point
- three pumps in a 2+1 redundant configuration in one example.

This demonstrates that NVL72 implementations may operate at different flow / thermal-load points.

---

## 7.3 OCP flow clue

An Open Compute Project white paper summarizing NVIDIA’s GB200 contribution includes a figure listing:

- “Liquid Cool Flow Rates — 5 liter/min”

[OCP]

Source:  
https://www.opencompute.org/documents/ocp-open-systems-for-ai-whitepaper-v1-0-0-final-pdf

The exact scope of the 5 L/min value is not completely explicit in the text extraction. It appears in the tray/rack contribution context and is consistent with an approximate tray-level design value.

Treat **5 L/min as a useful architecture clue, not a universal rack branch specification**.

---

# 8. Coolant properties

Dell and Vertiv support water or inhibited propylene-glycol mixtures on suitable loops. Vertiv explicitly lists **water or PG-25 with inhibitors** for its rack CDU.

For a reference PG25-like fluid, a DOWFROST LC 25 property table gives approximately at 40°C:

- density:
  \[
  \rho\approx1020\text{ kg/m}^3
  \]
- specific heat:
  \[
  c_p\approx4.12\text{ kJ/kg-K}
  \]
- thermal conductivity:
  \[
  k\approx0.476\text{ W/m-K}
  \]
- viscosity:
  \[
  \mu\approx1.47\text{ mPa-s}
  \]

At 50°C:
- \(\rho\approx1015\text{ kg/m}^3\)
- \(c_p\approx4.13\text{ kJ/kg-K}\)
- \(\mu\approx1.15\text{ mPa-s}\)

[3P/vendor technical property table]

For code, make properties temperature-dependent.

Recommended function interfaces:

```python
rho = coolant_density(T, glycol_fraction)
cp  = coolant_cp(T, glycol_fraction)
mu  = coolant_viscosity(T, glycol_fraction)
k   = coolant_conductivity(T, glycol_fraction)
```

Do not use constant water properties when comparing pressure-drop or heat-transfer results against PG25 systems.

---

# 9. Heat-balance calculations

For each branch:

\[
Q_i=\dot m_i c_p(T_{out,i}-T_{in,i})
\]

Therefore:

\[
T_{out,i}
=
T_{in,i}
+
\frac{Q_i}{\dot m_i c_p}
\]

For the whole liquid loop:

\[
Q_L=\dot m_{rack}c_p\Delta T_{rack}
\]

---

## 9.1 Example: 115.56 kW at 130 LPM

Assume:

\[
\dot V=130\text{ L/min}
\]

Convert:

\[
130\text{ L/min}
=
0.002167\text{ m}^3/s
\]

Using:

\[
\rho=1020\text{ kg/m}^3
\]

\[
\dot m=2.21\text{ kg/s}
\]

Then:

\[
\Delta T
=
\frac{115{,}560}
{2.21(4120)}
\approx12.7^\circ C
\]

So a plausible operating point could be approximately:

\[
40^\circ C\rightarrow52.7^\circ C
\]

or:

\[
45^\circ C\rightarrow57.7^\circ C
\]

depending on facility/CDU conditions.

This is comfortably below a 65°C return maximum.

---

## 9.2 Example compute-tray branch

At:

\[
Q_c=5.8\text{ kW}
\]

and 5 LPM PG25:

\[
\dot V=8.33\times10^{-5}\text{ m}^3/s
\]

\[
\dot m\approx0.085\text{ kg/s}
\]

Then:

\[
\Delta T
=
\frac{5800}{0.085(4120)}
\approx16.6^\circ C
\]

Thus a 5 LPM compute-tray flow is physically plausible for a high-temperature liquid loop.

---

# 10. Dell-supported CDU options

Dell’s IR9048 / XE9712 documentation lists the following cooling distribution units as supported examples.

## In-rack
- Vertiv XDU100B / CoolChip CDU 121
- Delta LCHD124A4QA

## In-row
- Motivair MCDU-50
- Vertiv XDU1350

[OEM]

Source:  
Dell IR9048 Installation and Service Manual — CDU  
https://www.dell.com/support/manuals/en-us/poweredge-xe9712/pe_ir9048_ism_pub/coolant-distribution-unit-cdu

This matters because the manifold design must lie inside an actual pump/cooling envelope.

---

# 11. Vertiv CoolChip CDU 121 baseline

This is a very useful **single-rack reference CDU**.

Published specifications:

- liquid-to-liquid CDU
- nominal cooling capacity:
  \[
  \boxed{121\text{ kW}}
  \]
- rated at:
  \[
  \boxed{4^\circ C\text{ approach temperature difference}}
  \]
- nominal secondary flow:
  \[
  \boxed{120\text{ LPM}}
  \]
- available / rated secondary differential pressure:
  \[
  \boxed{1.15\text{ bar}=115\text{ kPa}}
  \]
- coolant:
  - water
  - or PG25 with inhibitors
- 50 μm or 25 μm filtration
- 1.5 in sanitary-flange connections
- redundant pumps
- nominal power consumption around:
  \[
  \boxed{0.875\text{ kW}}
  \]

[OEM — Vertiv]

Source:  
https://www.vertiv.com/4a1be9/globalassets/shared/vertiv-coolchip-cdu-100_datasheet_en.pdf

### Interpretation

A 121 kW CDU is closely matched to a ~115 kW liquid rack.

However:

- QCT cites up to 130 LPM,
- Vertiv nominal is 120 LPM,
- full-load margin is limited.

Therefore a real deployment may:
- use a slightly different operating temperature rise,
- use a different in-rack CDU,
- use an in-row CDU,
- or operate below worst-case simultaneous silicon power.

The project should **not assume every NVL72 uses one Vertiv CDU121**.

Use it as one realistic pump/HX boundary condition.

---

# 12. Vertiv XDU1350 in-row reference

Published specifications include:

- nominal cooling:
  \[
  1368\text{ kW at }4^\circ C\text{ ATD}
  \]
- two pumps:
  \[
  1200\text{ LPM at }2.44\text{ bar external DP}
  \]
- three pumps:
  \[
  1800\text{ LPM at }1.98\text{ bar external DP}
  \]
- primary-side pressure drop:
  \[
  0.84\text{ bar at }1200\text{ LPM}
  \]
  with a referenced glycol condition
- secondary coolant temperature range:
  \[
  10-52^\circ C
  \]
- pump power:
  - ~13.7 kW with two pumps at maximum condition
  - ~20.5 kW with three pumps

[OEM — Vertiv]

Source:  
https://www.vertiv.com/499c46/globalassets/products/thermal-management/high-density-solutions/liebert-xdu-coolant-distribution-units/liebert-xdu1350-coolant-distribution-unitcdu-ds-en-na-sl-70799-web.pdf

This CDU is appropriate for **multiple racks** and is useful for an in-row architecture.

For eight racks:

\[
8(115)\approx920\text{ kW liquid load}
\]

At 130 LPM/rack:

\[
8(130)=1040\text{ LPM}
\]

Both lie inside the XDU1350 nominal thermal and flow envelope.

---

# 13. Facility-side heat exchanger model

A liquid-to-liquid CDU contains a plate heat exchanger separating:

- FWS: facility water
- TCS: rack/server coolant

Define:

\[
T_{FWS,in}
\]

\[
T_{FWS,out}
\]

\[
T_{TCS,supply}
\]

\[
T_{TCS,return}
\]

The **approach temperature difference** can be approximated at the cold end as:

\[
ATD
=
T_{TCS,supply}-T_{FWS,in}
\]

For a CDU rated at a 4°C approach:

If:

\[
T_{TCS,supply}=45^\circ C
\]

then a first-order facility supply target is:

\[
T_{FWS,in}\approx41^\circ C
\]

A commercial GB200-support CDU example from nVent/Hoffman publishes a GB200 design condition near:

- FWS supply:
  \[
  41^\circ C
  \]
- TCS supply:
  \[
  45^\circ C
  \]
- 4 K approach.

This is a useful consistency check.

Facility heat balance:

\[
Q
=
\dot m_{FWS}c_{p,FWS}
(T_{FWS,out}-T_{FWS,in})
\]

TCS heat balance:

\[
Q
=
\dot m_{TCS}c_{p,TCS}
(T_{TCS,return}-T_{TCS,supply})
\]

Heat exchanger effectiveness model:

\[
\epsilon
=
\frac{Q}
{C_{min}(T_{hot,in}-T_{cold,in})}
\]

NTU model:

\[
NTU=\frac{UA}{C_{min}}
\]

For project scope, the CDU heat exchanger can usually be treated as a boundary condition rather than optimized unless the project explicitly expands into CDU design.

---

# 14. Residual air cooling

GB200 NVL72 is not necessarily 100% liquid cooled.

HPE explicitly gives:

\[
115\text{ kW liquid}
\]

\[
17\text{ kW air}
\]

for a 132 kW rack.

[OEM]

This air load includes components not directly cold-plated, potentially including:

- portions of networking,
- storage,
- board electronics,
- lower-power VRMs,
- management hardware,
- power electronics,
- residual chassis losses.

The hydraulic model should only cool the **liquid-side load**.

Do not incorrectly force 132 kW into the TCS loop for this reference case.

---

# 15. Pressure-drop reality: what is public and what is not

NVIDIA does **not** publish a complete public pressure-drop-vs-flow curve for every GB200 compute tray, switch tray, branch connector, or rack manifold.

Therefore pressure-drop modeling must combine:

1. published CDU available head,
2. engineering equations,
3. component pressure-loss estimates,
4. calibration to credible system-level references.

Never claim a branch pressure drop is an official NVIDIA value unless it is explicitly sourced.

---

# 16. Credible system-level pressure-drop reference

A Georg Fischer data-center engineering presentation gives an example system analysis for an:

> NVIDIA NVL GB200 NVL72 132 kW technical loop

with total technical-loop pressure drop approximately:

\[
\boxed{2.32\text{ bar}}
\]

and a percentage distribution approximately:

| Loss category | Share |
|---|---:|
| Cold plates | 52% |
| Small QDCs | 22.2% |
| 1/4 in hoses | 12.5% |
| GAE / additional equipment | 7.7% |
| Fittings | 2.9% |
| Technical-loop pipes | 1.9% |
| Valves | ~1.0% |
| Manifold pipe | ~0.14% |

[3P — engineering conference slide; not an NVIDIA official rack specification]

Source:  
https://www.datacenter-forum.com/georg-fischer/high-performance-polymers-in-secondary-fluid-network-applications-slide-deck/download

The percentages sum to approximately 100% with rounding.

If scaled directly to 2.32 bar:

| Loss category | Approx. ΔP |
|---|---:|
| Cold plates | ~120.6 kPa |
| Small QDCs | ~51.5 kPa |
| 1/4 in hoses | ~29.0 kPa |
| GAE / equipment | ~17.9 kPa |
| Fittings | ~6.7 kPa |
| Technical pipes | ~4.4 kPa |
| Valves | ~2.3 kPa |
| Manifold pipe | ~0.3 kPa |

[DERIVED]

### Crucial caution

The 2.32 bar figure appears to represent a broader **technical loop**, not necessarily only the bare rack manifold between an in-rack CDU’s secondary ports.

This cannot be blindly combined with the Vertiv CDU121’s 1.15 bar available pressure.

Treat it as:
- a useful pressure-loss **distribution pattern**,
- and an in-row / broader-loop system reference.

---

# 17. Two recommended hydraulic boundary-condition cases

## Case 1 — in-rack CDU

Use:

\[
Q=115\text{ kW}
\]

\[
\dot V=110-120\text{ LPM}
\]

\[
\Delta P_{available}\le115\text{ kPa}
\]

This corresponds to a Vertiv CDU121-like boundary.

The rack + tray circuit must fit inside this head.

---

## Case 2 — in-row CDU / technical loop

Use:

\[
Q\approx115\text{ kW/rack}
\]

\[
\dot V\approx110-130\text{ LPM/rack}
\]

and allow:

\[
\Delta P_{loop}
\approx150-230\text{ kPa}
\]

depending on piping distance and selected CDU.

For a multi-rack XDU1350-like system, available head can be approximately 2 bar or more at high aggregate flow.

This case is closer to the Georg Fischer pressure-loss example.

---

# 18. Hydraulic network representation

Represent the rack as a pair of vertical headers joined by 27 parallel tray branches.

```text
                 Supply header
CDU SUPPLY -> o---o---o---o---o--- ... ---o
              |   |   |   |             |
             B1  B2  B3  B4           B27
              |   |   |   |             |
CDU RETURN <- o---o---o---o---o--- ... ---o
                 Return header
```

Each branch contains:

```text
supply header tap
 -> blind-mate QDC
 -> tray tubing / hose
 -> GPU/CPU or NVSwitch cold-plate network
 -> internal fittings
 -> return blind-mate QDC
 -> return header
```

For branch \(i\):

\[
\Delta P_{branch,i}
=
\Delta P_{QDC,s,i}
+
\Delta P_{tube,i}
+
\Delta P_{coldplates,i}
+
\Delta P_{minor,i}
+
\Delta P_{QDC,r,i}
\]

and:

\[
P_{supply,i}-P_{return,i}
=
\Delta P_{branch,i}
\]

---

# 19. Header segment equations

For each manifold segment:

\[
V_j=\frac{\dot m_j}{\rho A_j}
\]

\[
Re_j=\frac{\rho V_jD_j}{\mu}
\]

Darcy friction:

\[
\Delta P_{f,j}
=
f_j\frac{L_j}{D_j}\frac{\rho V_j^2}{2}
\]

Minor losses:

\[
\Delta P_{m,j}
=
K_j\frac{\rho V_j^2}{2}
\]

Total:

\[
\Delta P_j
=
\left(
f_j\frac{L_j}{D_j}
+
\sum K_j
\right)
\frac{\rho V_j^2}{2}
\]

Use:
- laminar:
  \[
  f=64/Re
  \]
- turbulent: Colebrook, Haaland, or Swamee-Jain.

---

# 20. Branch pressure-drop model

For turbulent cold plates and QDC-dominated branches, a useful reduced-order relation is:

\[
\Delta P_i=K_i\dot m_i^2
\]

where \(K_i\) is calibrated to a reference pressure drop.

This is computationally efficient for optimization.

If a component has published pressure-drop vs flow data, fit:

\[
\Delta P=a\dot V^2+b\dot V+c
\]

or interpolate the manufacturer curve.

---

# 21. Cold-plate model

Detailed internal NVIDIA cold-plate geometry is proprietary.

Use one of two approaches.

## Level 1 — hydraulic resistance model

For compute tray:

\[
\Delta P_{CP,c}
=
K_c\dot m_c^2
\]

For switch tray:

\[
\Delta P_{CP,s}
=
K_s\dot m_s^2
\]

Calibrate \(K_c\) and \(K_s\) to chosen reference flow/pressure data.

---

## Level 2 — simplified microchannel model

For each cold plate:

\[
Re=\frac{\rho VD_h}{\mu}
\]

\[
Nu=f(Re,Pr)
\]

\[
h=\frac{Nu k}{D_h}
\]

Convection resistance:

\[
R_{conv}=\frac{1}{hA}
\]

Chip/coolant temperature:

\[
T_{chip}
=
T_{coolant}
+
Q
(R_{TIM}+R_{plate}+R_{conv})
\]

The project does not require exact proprietary fin geometry to study manifold distribution.

---

# 22. Flow-distribution objective metrics

## 22.1 Conventional flow maldistribution

\[
M_f
=
\frac{\dot m_{max}-\dot m_{min}}
{\dot m_{avg}}
\]

or standard deviation:

\[
CV_f
=
\frac{\sigma_{\dot m}}
{\overline{\dot m}}
\]

---

## 22.2 Thermally normalized maldistribution

For heterogeneous heat loads, define:

\[
r_i=\frac{\dot m_i}{Q_i}
\]

Then:

\[
M_T
=
\frac{r_{max}-r_{min}}{r_{avg}}
\]

A better objective may be minimizing maximum outlet-temperature spread:

\[
\Delta T_{out,spread}
=
T_{out,max}-T_{out,min}
\]

or:

\[
T_{out,max}
\]

This directly links hydraulics to thermal performance.

---

# 23. Recommended design variables

The optimization should vary parameters that can actually enter equations.

## Primary design variables

### 1. Supply manifold diameter profile

Constant baseline:

\[
D_s(x)=D_{s0}
\]

Tapered design:

\[
D_s(x)=D_{s0}-k_sx
\]

or piecewise segment diameters:

\[
D_{s,1},D_{s,2},...,D_{s,n}
\]

---

### 2. Return manifold diameter profile

\[
D_r(x)
\]

Do not assume supply and return must have the same taper.

---

### 3. Branch restriction / orifice coefficients

Each branch:

\[
K_{o,i}
\]

or equivalent orifice diameter:

\[
D_{o,i}
\]

A practical reduced design may use only two classes:

- compute-tray orifice \(D_{o,c}\)
- switch-tray orifice \(D_{o,s}\)

A more advanced design may tune branch groups by vertical position.

---

### 4. Total rack flow

\[
\dot V_{rack}
\]

Possible sweep:

\[
90-140\text{ LPM}
\]

provided CDU limits are enforced.

---

# 24. Geometry assumptions where public dimensions are unavailable

Do not invent a proprietary manifold diameter and call it factual.

Use a design range.

Vertiv CDU121 has 1.5-in sanitary connections. Therefore a useful manifold-ID design sweep is approximately:

\[
25\text{ mm}\le D_h\le50\text{ mm}
\]

[ASSUMPTION]

This range should be justified as a design envelope, not an NVIDIA dimension.

Branch tubing / connector flow paths can be represented with equivalent hydraulic diameters calibrated to total pressure loss.

---

# 25. Constraints

The optimization should include at least the following.

## 25.1 CDU pump-head constraint

For CDU121-like single-rack case:

\[
\boxed{\Delta P_{system}\le115\text{ kPa}}
\]

at approximately 120 LPM.

For in-row case, use the actual selected CDU curve.

---

## 25.2 Maximum rack flow

Example:

\[
\boxed{\dot V_{rack}\le130\text{ LPM}}
\]

based on the QCT published system envelope.

---

## 25.3 Coolant return temperature

Use OEM maximum:

\[
\boxed{T_{return}\le65^\circ C}
\]

for the QCT example.

A design target should include safety margin, e.g.:

\[
T_{return,target}\le60^\circ C
\]

[ASSUMPTION]

---

## 25.4 Supply temperature

QCT maximum inlet:

\[
\boxed{T_{supply}\le45^\circ C}
\]

The design may choose a lower value depending on facility water.

---

## 25.5 Minimum branch flow

Minimum flow should be calculated from:

\[
\dot m_{min,i}
=
\frac{Q_i}
{c_p(T_{out,max}-T_{in})}
\]

Do not use an arbitrary minimum if a thermal limit can generate it.

---

## 25.6 Velocity limit

To avoid excessive erosion/noise/pressure loss, use an engineering constraint such as:

\[
V_{header}\le2-3\text{ m/s}
\]

[ASSUMPTION]

Perform sensitivity analysis because allowed velocities depend on piping material and OEM guidance.

---

## 25.7 Pumping power

\[
P_{pump}
=
\frac{\Delta P\dot V}{\eta_p}
\]

Use pump efficiency range:

\[
0.5\le\eta_p\le0.8
\]

unless a vendor curve is available.

---

# 26. Pump characteristics

A pump is not a constant-pressure source.

The pump curve can be approximated as:

\[
\Delta P_{pump}
=
\Delta P_{shutoff}
-
a\dot V^2
\]

The system curve is approximately:

\[
\Delta P_{system}
=
K_{sys}\dot V^2
\]

Operating point occurs where:

\[
\Delta P_{pump}
=
\Delta P_{system}
\]

For a variable-speed pump, affinity laws:

\[
\dot V\propto N
\]

\[
\Delta P\propto N^2
\]

\[
P\propto N^3
\]

where \(N\) is rotational speed.

This is important because a manifold redesign that cuts pressure drop can reduce pump power significantly.

---

# 27. Heat exchanger / facility constraints

For a 121 kW, 4 K-approach CDU:

\[
Q_{HX}\le121\text{ kW nominal}
\]

and:

\[
T_{TCS,supply}
\gtrsim
T_{FWS,in}+4^\circ C
\]

at the rating point.

If the facility provides warmer water, the available cooling capacity may decrease unless flow or heat-exchanger area changes.

The agent must never treat “121 kW” as independent of:
- approach temperature,
- FWS temperature,
- TCS temperature,
- fluid properties,
- flow.

---

# 28. Baseline design to beat

The academic project needs an improvement over an existing/simple solution.

Define the baseline as:

### Baseline
- constant-diameter supply header
- constant-diameter return header
- identical branch restriction for all compute trays
- identical branch restriction for all switch trays
- no location-specific balancing
- fixed total rack flow

This is not a claim that NVIDIA’s actual system is this primitive. It is a **reference engineering baseline**.

The optimized design should beat this baseline.

---

# 29. Candidate improved designs

Test at least four architectures.

## Design A — constant header, no balancing
Reference baseline.

## Design B — tapered supply and return
Reduce header cross section as flow decreases downstream.

## Design C — constant header + tuned branch restrictions
Use intentional branch resistance to flatten branch pressure sensitivity.

## Design D — tapered headers + two-class branch tuning
Separate:
- compute-tray restrictions
- switch-tray restrictions.

## Design E — fully optimized location-specific restrictions
Optimize:
\[
D_{o,1},...,D_{o,27}
\]

This may be mathematically best but less manufacturable.

---

# 30. Recommended final design philosophy

A good practical final result will probably **not** minimize hydraulic maldistribution to zero.

Instead it should minimize thermal variation with manageable pumping penalty.

Possible objective:

\[
J
=
w_1
\frac{T_{out,max}-T_{out,min}}{T_{ref}}
+
w_2
\frac{\Delta P_{system}}{\Delta P_{limit}}
+
w_3
\frac{P_{pump}}{P_{ref}}
\]

or multiobjective Pareto optimization.

A strong final claim would look like:

> Compared with a constant-diameter, untuned baseline, the optimized tapered supply/return manifold with separate compute- and switch-tray branch restrictions reduces thermally normalized branch maldistribution by X%, reduces maximum tray outlet temperature by Y°C, and remains below Z kPa total rack pressure drop at 115 kW liquid load.

Do not fabricate X, Y, or Z. They must come from the model.

---

# 31. Numerical solution strategy

## 31.1 Unknowns

For each branch \(i\):

\[
\dot m_i
\]

For each header node:

\[
P_{s,i}
\]

\[
P_{r,i}
\]

Possibly:

\[
T_i
\]

if thermal coupling is solved simultaneously.

---

## 31.2 Governing equations

### Continuity at each supply node

\[
\dot m_{header,j+1}
=
\dot m_{header,j}-\dot m_{branch,j}
\]

### Return header

\[
\dot m_{return,j+1}
=
\dot m_{return,j}+\dot m_{branch,j}
\]

### Branch pressure equality

\[
P_{s,i}-P_{r,i}
=
\Delta P_{branch,i}(\dot m_i)
\]

### Header pressure drop

\[
P_{j+1}
=
P_j-\Delta P_j
\]

### Total flow

\[
\sum_i\dot m_i
=
\dot m_{rack}
\]

Solve nonlinearly using:
- `scipy.optimize.root`
- `scipy.optimize.least_squares`
- Newton-Raphson
- network iteration.

---

# 32. Thermal coupling

After solving branch flow:

\[
T_{out,i}
=
T_{in,i}
+
\frac{Q_i}{\dot m_i c_p(T)}
\]

The return header mixes streams.

At mixing node:

\[
T_{mix}
=
\frac{\sum_j \dot m_jc_{p,j}T_j}
{\sum_j\dot m_jc_{p,j}}
\]

For small \(c_p\) differences:

\[
T_{mix}
\approx
\frac{\sum_j\dot m_jT_j}
{\sum_j\dot m_j}
\]

Because return fluid warms as tray streams join, the return header temperature is not constant.

---

# 33. Temperature-dependent fluid properties

Iterate:

1. assume fluid properties,
2. solve flow,
3. calculate branch temperatures,
4. update \(\rho,\mu,c_p,k\),
5. repeat until convergence.

Convergence criterion:

\[
\max|T_i^{n+1}-T_i^n|<0.01^\circ C
\]

and:

\[
\max
\left|
\frac{\dot m_i^{n+1}-\dot m_i^n}
{\dot m_i^n}
\right|
<10^{-4}
\]

---

# 34. Optimization variables and bounds — suggested starter set

```python
design_bounds = {
    "supply_header_D_in_mm": (25, 50),
    "supply_header_D_out_mm": (15, 50),
    "return_header_D_in_mm": (15, 50),
    "return_header_D_out_mm": (25, 50),
    "compute_branch_K": (Kc_min, Kc_max),
    "switch_branch_K": (Ks_min, Ks_max),
    "rack_flow_LPM": (90, 130),
}
```

The taper must obey manufacturability:

```text
D_out <= D_in
```

for a supply header whose flow decreases downstream, with return geometry defined according to flow direction.

---

# 35. Recommended outputs

For every design point, calculate:

### Hydraulic
- total rack flow
- each tray flow
- branch pressure differential
- supply-header pressure profile
- return-header pressure profile
- total system pressure drop
- Reynolds number per segment
- velocity per segment
- pump power

### Thermal
- tray inlet temperature
- tray outlet temperature
- rack return temperature
- compute-tray temperature rise
- switch-tray temperature rise
- maximum outlet temperature
- outlet-temperature spread

### Performance metrics
- flow maldistribution
- thermally normalized maldistribution
- pumping power
- pressure-drop margin
- CDU thermal margin
- CDU hydraulic margin

---

# 36. Plots required

At minimum produce:

1. **Supply and return pressure vs rack height**
2. **Branch flow vs tray number**
3. **Tray heat load vs branch flow**
4. **Tray outlet temperature vs tray number**
5. **Pressure-drop contribution pie/bar chart**
6. **Flow maldistribution vs manifold diameter**
7. **Flow maldistribution vs taper ratio**
8. **Pressure drop vs taper ratio**
9. **Pump power vs thermal uniformity**
10. **Pareto frontier: temperature spread vs pump power**
11. **Baseline vs optimized design comparison**
12. **Sensitivity to rack flow: 90–130 LPM**
13. **Sensitivity to TCS supply temperature**
14. **Sensitivity to cold-plate resistance uncertainty**

---

# 37. Sensitivity / uncertainty analysis

Because proprietary geometry is unavailable, uncertainty analysis is mandatory.

Sweep:

### Cold-plate ΔP coefficient
\[
K_{CP}\pm30\%
\]

### QDC loss coefficient
\[
K_{QDC}\pm30\%
\]

### manifold roughness
range appropriate to stainless/polymer implementation

### tray heat loads
- GPU:
  \[
  0.8-1.2\text{ kW}
  \]
  or workload duty factor
- CPU:
  lower load to 0.5 kW max design value
- switch:
  \[
  \pm20\%
  \]

### CDU flow
\[
90-130\text{ LPM}
\]

### supply temperature
e.g.
\[
25-45^\circ C
\]

### PG concentration
0–25% if comparing water vs PG25.

The optimized geometry should remain useful across this uncertainty.

---

# 38. Pressure-drop calibration strategy

A good calibration procedure:

## Step 1
Select:
\[
\dot V_{rack}=120\text{ LPM}
\]

## Step 2
Use GF percentage distribution as an initial relative resistance estimate.

## Step 3
Scale total rack-only loss so that:

\[
\Delta P_{rack}
\le115\text{ kPa}
\]

for the in-rack CDU case.

## Step 4
Build a second “extended loop” model that includes:
- CDU-to-rack hoses,
- row piping,
- isolation valves,
- filters / additional equipment,

and calibrate toward:

\[
\Delta P\sim2.3\text{ bar}
\]

for the broader technical-loop reference.

This avoids mixing two incompatible system boundaries.

---

# 39. Example normalized 115 kPa rack pressure-loss budget

If the GF loss fractions are used only as **relative guidance** and normalized to a 115 kPa in-rack CDU budget:

| Component | Approx. normalized ΔP |
|---|---:|
| cold plates | ~60 kPa |
| QDCs | ~25.5 kPa |
| branch hoses | ~14.4 kPa |
| other equipment | ~8.9 kPa |
| fittings | ~3.3 kPa |
| piping | ~2.2 kPa |
| valves | ~1.15 kPa |
| bare manifold | <<1 kPa |

[DERIVED / MODEL INITIALIZATION ONLY]

This table is **not a published NVIDIA specification**.

It is a starting calibration distribution.

The interesting engineering implication is that the **bare manifold friction may be a small share of total system pressure loss**, yet header pressure gradients can still strongly affect branch distribution because branch flow depends on differential pressure.

---

# 40. Important physical insight for the project

The optimization is not simply:

> make the manifold as large as possible.

A very large header:
- decreases header pressure gradient,
- improves raw flow uniformity,

but:
- increases size,
- mass,
- coolant inventory,
- cost,
- rack packaging difficulty.

Likewise, adding strong branch restrictions:
- improves balancing,
- makes branch flow less sensitive to header pressure,

but:
- increases pump head,
- pump energy,
- CDU requirement.

Therefore the real optimum is a trade:

\[
\boxed{
\text{thermal uniformity}
\leftrightarrow
\text{pressure drop}
\leftrightarrow
\text{packaging}
}
\]

---

# 41. Possible project goal parameter

For a class requiring one quantifiable goal parameter, the strongest option is:

## Goal parameter
**Thermally normalized flow maldistribution**

\[
M_T
=
\frac{(\dot m/Q)_{max}-(\dot m/Q)_{min}}
{(\dot m/Q)_{avg}}
\]

or, if the instructor prefers a more conventional parameter:

**Maximum tray coolant outlet temperature**

\[
T_{out,max}
\]

The second may be easier to explain.

---

# 42. Possible design constraint

Use:

## Constraint parameter
**Rack pressure drop**

\[
\Delta P_{rack}
\]

Possible project boundary:

\[
\Delta P_{rack}\le115\text{ kPa}
\]

for a Vertiv CDU121-like in-rack pumping envelope.

This is a real, equation-linked constraint.

---

# 43. Possible design variables for the class table

Use at least:

1. **Supply/return manifold taper ratio**
   \[
   \tau=\frac{D_{out}}{D_{in}}
   \]

2. **Branch restriction diameter**
   \[
   D_o
   \]

For a richer project:

3. **Inlet manifold diameter**
   \[
   D_{in}
   \]

4. **Total coolant flow**
   \[
   \dot V
   \]

Each directly affects equations.

---

# 44. Comparison to existing/public solution

Do not claim that your optimized design beats NVIDIA’s proprietary actual manifold unless you have measured or published NVIDIA baseline data.

Instead define:

> a conventional constant-diameter manifold reference design based on public NVL72 heat loads, flow ranges, and CDU constraints.

Then say:

> the proposed optimized geometry improves the modeled baseline.

If later you obtain OCP CAD or manufacturer pressure/geometry data, update the baseline.

---

# 45. Dell factory observations relevant to model realism

ServeTheHome’s Dell Franklin factory tour provides several physical-system insights:

- Dell builds complete IR7000 NVIDIA GB200 NVL72 racks at factory scale.
- The rack integrates:
  - liquid cooling,
  - power busbar,
  - NVLink cartridges,
  - compute trays,
  - NVLink switch trays,
  - management networking.
- supply/return manifolds are mounted at the rear.
- tray connections blind mate when trays slide into the rack.
- no manual tray hose connection is required in the field for this architecture.
- the CDU exchanges heat between the rack loop and external facility loop.
- Dell can build customer-specific rack/CDU/power combinations.
- fully populated racks are roughly ~3000 lb class and require specialized handling.

[3P]

Sources:
- https://www.servethehome.com/inside-the-dell-factory-that-builds-ai-factories/
- https://www.servethehome.com/inside-the-dell-factory-that-builds-ai-factories/3/

This means the model should prioritize:
- serviceable branch architecture,
- fixed blind-mate locations,
- no manually adjustable hoses at every service event,
- compact rear manifold packaging.

---

# 46. OCP mechanical context

NVIDIA contributed major parts of the GB200 NVL72 mechanical infrastructure to OCP, including:

- NVLink cable-cartridge mechanical envelope,
- enhanced busbar,
- blind-mate manifold,
- floating blind-mate connectors,
- rack reinforcement,
- tray form-factor details.

NVIDIA states the rack cooling design is roughly in the 120–130 kW class.

Source:
https://developer.nvidia.com/blog/?p=90182

The OCP system architecture provides a defensible reason to model a common vertical manifold feeding all tray positions.

---

# 47. Power infrastructure facts useful for thermal modeling

NVIDIA rack power shelves:

- six 5.5 kW PSUs per shelf
- up to:
  \[
  33\text{ kW/shelf}
  \]
- multiple shelves
- nominal ~50–51 V DC rack busbar
- NVIDIA documents eight shelves in some reference DGX GB200 systems for redundancy.

[NVIDIA]

Source:
https://docs.nvidia.com/dgx-superpod/reference-architecture-scalable-infrastructure-gb200/latest/dgx-superpod-components.html

Power-supply inefficiency and air-cooled rack electronics contribute to the non-liquid heat load.

---

# 48. Networking components and cooling

A compute tray includes high-speed networking such as ConnectX and BlueField devices depending on exact OEM/reference configuration.

NVIDIA’s tuning guide states that in hybrid-cooled configurations:

- Grace CPU
- Blackwell GPU
- ConnectX-7
- NVLink Switch ASIC
- some OSFP components

can be liquid cooled, while other components remain air cooled.

This means exact tray liquid power can vary slightly by OEM.

The model should expose:

```python
compute_tray_aux_liquid_W
switch_tray_aux_liquid_W
```

as user-adjustable inputs.

---

# 49. Model default values

Recommended starter configuration:

```yaml
rack:
  compute_trays: 18
  switch_trays: 9

power:
  gpu_W_each: 1200
  gpus_per_compute_tray: 4
  grace_cpu_W_each: 500
  cpus_per_compute_tray: 2
  switch_rack_total_W: 11160

thermal:
  liquid_load_W: 115560
  residual_air_W_reference: 17000
  TCS_supply_C: 40
  TCS_return_max_C: 65

flow:
  rack_flow_LPM: 120
  rack_flow_max_LPM: 130

coolant:
  type: "PG25"
  property_model: "temperature-dependent"

cdu:
  reference: "Vertiv CoolChip CDU121"
  cooling_capacity_kW: 121
  nominal_secondary_flow_LPM: 120
  available_external_dp_kPa: 115
  approach_K: 4

optimization:
  objective: "minimize maximum tray outlet temperature + pump power"
```

---

# 50. First-order target branch flows

For constant desired coolant rise:

\[
\dot m_i\propto Q_i
\]

At total flow 120 LPM:

Total heat:
\[
115.56\text{ kW}
\]

Compute-tray flow:

\[
120
\frac{5.8}{115.56}
\approx6.02\text{ LPM}
\]

Switch-tray flow:

\[
120
\frac{1.24}{115.56}
\approx1.29\text{ LPM}
\]

Check:

\[
18(6.02)+9(1.29)\approx120\text{ LPM}
\]

At 130 LPM:

Compute:
\[
\approx6.52\text{ LPM/tray}
\]

Switch:
\[
\approx1.39\text{ LPM/tray}
\]

These are **thermally proportional ideal flows**, not official NVIDIA branch specifications.

They make an excellent optimization target.

---

# 51. More realistic objective than equal flow

Define desired branch flow:

\[
\dot m_{i,target}
=
\dot m_{rack}
\frac{Q_i}{\sum_jQ_j}
\]

Then error:

\[
e_i
=
\frac{\dot m_i-\dot m_{i,target}}
{\dot m_{i,target}}
\]

Objective:

\[
J_f
=
\sqrt{
\frac{1}{N}
\sum_ie_i^2
}
\]

This RMS normalized-flow error is a clean optimization metric.

---

# 52. Pump-power model example

If:

\[
\Delta P=115\text{ kPa}
\]

\[
\dot V=120\text{ LPM}=0.002\text{ m}^3/s
\]

Hydraulic power:

\[
P_h=\Delta P\dot V
\]

\[
P_h
=
115000(0.002)
=
230\text{ W}
\]

At pump efficiency:

\[
\eta=0.6
\]

electrical pump power:

\[
P_e
=
\frac{230}{0.6}
\approx383\text{ W}
\]

The actual CDU consumes more than ideal hydraulic power because of controls, redundant pump arrangements, motor inefficiency, filtration, electronics, and operating margin.

Vertiv’s rack CDU nominal electrical use around 0.875 kW is therefore plausible.

---

# 53. Why pressure-drop reduction matters even at 120 kW rack power

A few hundred watts of pump power sounds small relative to 120 kW compute.

However the engineering value is not only energy.

Lower pressure drop can enable:

- smaller pumps,
- more hydraulic margin,
- higher reliability,
- lower leakage stress,
- more racks per in-row CDU,
- warmer coolant operation,
- better fault tolerance,
- future higher-power trays.

Thus the primary benefit can be **capacity and robustness**, not only rack PUE.

---

# 54. Fault scenarios the agent should eventually model

Optional advanced work:

### One branch partially blocked
Increase:
\[
K_i
\]

by 2–10×.

### One QDC degraded
Increase branch minor-loss coefficient.

### Pump reduced speed
Apply affinity laws.

### One pump failed
Use N+1 degraded pump curve.

### Compute tray removed
Set branch flow path to closed or bypass condition.

### Workload imbalance
Some compute trays at 100%, others at 50%.

### Switch-heavy communication workload
Raise switch load.

Evaluate whether optimized manifold remains safe.

---

# 55. Validation checks

Every simulation must pass:

### Mass balance
\[
\left|
\dot m_{rack}
-
\sum_i\dot m_i
\right|
<0.1\%
\]

### Energy balance
\[
\left|
Q_{rack}
-
\dot m_{rack}c_p(T_r-T_s)
\right|
<1\%
\]

### Pressure-loop closure
Pressure residual at every loop below numerical tolerance.

### Monotonic physics sanity
At fixed geometry:
- increasing total flow should generally increase pressure drop,
- increasing header diameter should reduce header friction,
- increasing branch resistance should reduce branch flow,
- lower branch flow should increase tray coolant temperature rise.

---

# 56. Suggested code architecture

```text
project/
├── AGENT.md
├── README.md
├── data/
│   ├── sources.yaml
│   ├── cdu_specs.yaml
│   ├── coolant_properties.csv
│   └── baseline_config.yaml
├── src/
│   ├── coolant.py
│   ├── hydraulics.py
│   ├── thermal.py
│   ├── manifold.py
│   ├── cdu.py
│   ├── solver.py
│   ├── objectives.py
│   └── optimize.py
├── studies/
│   ├── baseline.py
│   ├── taper_sweep.py
│   ├── branch_balancing.py
│   ├── uncertainty.py
│   └── pareto.py
└── tests/
    ├── test_mass_balance.py
    ├── test_energy_balance.py
    ├── test_pressure_drop.py
    └── test_regression.py
```

---

# 57. Data-source schema

Every input in `sources.yaml` should contain:

```yaml
gpu_max_power_W:
  value: 1200
  confidence: NVIDIA
  source: "NVIDIA Mission Control PRS FAQ"
  url: "https://docs.nvidia.com/mission-control/docs/systems-administration-guide/2.2.0/prs/faq.html"
  notes: "GB200 current published per-GPU max power budget"
```

For estimates:

```yaml
header_inner_diameter_mm:
  value: 38
  confidence: ASSUMPTION
  source: null
  notes: "Initial design value; optimize 25-50 mm"
```

This prevents accidental mixing of facts and assumptions.

---

# 58. Source hierarchy for this project

Prefer in this order:

1. NVIDIA current documentation
2. NVIDIA OCP contribution
3. OEM product / installation manuals
4. CDU manufacturer data sheets
5. OCP white papers
6. ServeTheHome direct physical observations
7. engineering conference presentations
8. reputable technical analysis
9. generic blogs only for cross-checks, not primary design values

---

# 59. Key sources

## NVIDIA

### DGX GB Rack Scale Systems User Guide
Architecture, rack components, compute trays, switch trays, cooling, power shelves  
https://docs.nvidia.com/dgx/dgxgb200-user-guide/

### Hardware page
https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html

### GB200 NVL72 product page
https://www.nvidia.com/en-us/data-center/gb200-nvl72/

### GB200 partition guide
Approx. 120 kW, ~85% liquid / 15% air reference  
https://docs.nvidia.com/multi-node-nvlink-systems/partition-guide-v1-2.pdf

### Mission Control power budgeting
Per-GPU and per-node power budget  
https://docs.nvidia.com/mission-control/docs/systems-administration-guide/2.2.0/prs/faq.html

### Dynamic Power Software
GB200 NVSwitch aggregate recommended static load  
https://docs.nvidia.com/datacenter/dps/versions/0.8/guides/runbooks/maxlps-simple-mode-pilot/

### SuperPOD component architecture
https://docs.nvidia.com/dgx-superpod/reference-architecture-scalable-infrastructure-gb200/latest/dgx-superpod-components.html

### NVIDIA GB200 OCP contribution
https://developer.nvidia.com/blog/?p=90182

### Grace-Blackwell tuning guide
https://docs.nvidia.com/multi-node-nvlink-systems/multi-node-tuning-guide/system.html

---

## Dell

### Dell IR9048 CDU documentation
Lists supported in-rack and in-row CDU models  
https://www.dell.com/support/manuals/en-us/poweredge-xe9712/pe_ir9048_ism_pub/coolant-distribution-unit-cdu

### XE9712 cooling specs
https://www.dell.com/support/manuals/en-us/poweredge-xe9712/xe9712_ism/Cooling-specifications

### Dell IR7000 / cooling platform
https://www.dell.com/en-us/dt/corporate/newsroom/announcements/detailpage.press-releases~usa~2024~10~dell-servers-storage-at-ocp.htm

---

## HPE

### GB200 NVL72 product page
132 kW total, 115 kW liquid, 17 kW air  
https://buy.hpe.com/us/en/compute/rack-scale-system/nvidia-nvl-system/nvidia-gb200-nvl72-by-hpe/p/1014890104

### HPE data sheet
https://www.hpe.com/psnow/generateDDS/NVIDIA%20GB200%20NVL72%20by%20HPE%20data%20sheet-PSN1014890104IEEN.pdf

---

## QCT

### GB200 NVL72 QoolRack thermal-management document
45°C inlet max, 65°C return max, up to ~130 LPM, 115 kW liquid / 17 kW air reference  
https://blog.qct.io/wp-content/uploads/2025/04/QCT-Qoolrack-Stand-Alone_Advanced-Liquid-Cooling-for-NVIDIA-GB200-NVL72-Systems.pdf

---

## Vertiv

### CoolChip CDU 121 data sheet
121 kW @ 4 K ATD, 120 LPM @ 1.15 bar, PG25/water  
https://www.vertiv.com/4a1be9/globalassets/shared/vertiv-coolchip-cdu-100_datasheet_en.pdf

### XDU1350 data sheet
1368 kW @ 4 K, 1200 LPM @ 2.44 bar with two pumps  
https://www.vertiv.com/499c46/globalassets/products/thermal-management/high-density-solutions/liebert-xdu-coolant-distribution-units/liebert-xdu1350-coolant-distribution-unitcdu-ds-en-na-sl-70799-web.pdf

---

## Open Compute Project

### Open Systems for AI white paper
Includes NVIDIA GB200 NVL72 OCP contribution summary  
https://www.opencompute.org/documents/ocp-open-systems-for-ai-whitepaper-v1-0-0-final-pdf

---

## ServeTheHome

### Dell AI factory tour
https://www.servethehome.com/inside-the-dell-factory-that-builds-ai-factories/

### IR7000 GB200 rack details
https://www.servethehome.com/inside-the-dell-factory-that-builds-ai-factories/3/

### NVIDIA DGX GB200 NVL72 physical overview
https://www.servethehome.com/this-is-the-nvidia-dgx-gb200-nvl72/

### LITEON 120 kW GB200 liquid-cooled rack / CDU
https://www.servethehome.com/liteon-shows-nvidia-gb200-nvl72-rack-at-ocp-summit-2024/

---

## Engineering pressure-drop reference

### Georg Fischer technical-loop pressure-loss example
https://www.datacenter-forum.com/georg-fischer/high-performance-polymers-in-secondary-fluid-network-applications-slide-deck/download

---

# 60. Known unknowns

The following are not reliably public for the exact NVIDIA/Dell GB200 rack:

- exact internal diameter of the NVIDIA/Dell vertical rack manifolds
- exact header taper geometry, if any
- exact per-tray cold-plate ΔP-vs-flow curve
- exact blind-mate QDC \(K\) or Cv
- exact compute-tray internal plumbing topology
- exact switch-tray internal plumbing topology
- exact branch orifice sizes
- exact CDU pump curve for every customer installation
- exact facility-water design temperature at every deployment
- exact workload-dependent tray power distribution
- exact heat fraction removed from each individual component by liquid

These must be modeled parametrically.

This uncertainty is acceptable for an academic design project as long as it is transparent and the sensitivity analysis is strong.

---

# 61. Research questions still worth pursuing

Before finalizing the report, look specifically for:

1. NVIDIA/OCP downloadable CAD for blind-mate manifold geometry.
2. OCP specification for UQD04 / blind-mate connector Cv or pressure loss.
3. Dell IR7000 rack manifold dimensions.
4. Dell/Vertiv commissioning documents containing target TCS differential pressure.
5. QCT tray pressure-drop curves.
6. HPE GB200 CDU QuickSpecs with explicit TCS flow/head.
7. public telemetry traces from Mission Control containing:
   - CDU flow,
   - CDU DP,
   - supply temperature,
   - return temperature.
8. cold-plate vendor data for 1.2 kW-class B200 hardware.
9. pump performance curves for CDU121, Delta rack CDU, or Motivair MCDU-50.

---

# 62. Final project framing

Recommended project title:

> **Optimization of Coolant Manifold Flow Distribution for an NVIDIA GB200 NVL72–Class AI Rack**

Recommended technical question:

> How should rack supply/return manifold geometry and tray branch resistance be designed to minimize temperature and flow maldistribution across 18 heterogeneous compute trays and 9 NVLink switch trays while remaining within the pressure-head and flow limits of practical coolant distribution units?

Recommended main novelty:

> Unlike a simple equal-flow model, optimize the manifold around the actual heterogeneous thermal load: ~5.8 kW per compute tray and ~1.24 kW per NVLink switch tray.

Recommended comparison:

> constant-diameter baseline vs tapered/manifold-balanced design.

Recommended final deliverable:

- optimized geometry,
- branch-flow map,
- pressure map,
- coolant-temperature map,
- pump/head requirement,
- quantified improvement over baseline,
- uncertainty/sensitivity analysis.

---

# 63. Final rules for the coding agent

1. Never fabricate proprietary NVIDIA geometry.
2. Never label an estimate “NVIDIA spec.”
3. Preserve source provenance for every important numeric input.
4. Use the 18-compute + 9-switch structure.
5. Use heterogeneous tray heat loads.
6. Use temperature-dependent coolant properties.
7. Enforce mass and energy conservation.
8. Enforce a real CDU pressure/flow envelope.
9. Report pressure-drop boundary clearly:
   - rack-only,
   - or rack + external technical loop.
10. Compare every optimized result against a defined baseline.
11. Run sensitivity studies before claiming improvement.
12. Prefer a manufacturable 2–4 parameter design over a mathematically perfect 27-variable branch solution unless both are compared.
13. Produce plots and tables suitable for an engineering report.
14. Clearly separate:
   - published data,
   - derived values,
   - assumptions,
   - optimization outputs.

---

# 64. Short engineering summary

The most defensible high-load model is:

\[
72(1.2\text{ kW GPUs})
+
36(0.5\text{ kW CPUs})
+
11.16\text{ kW NVSwitch}
\approx115.56\text{ kW liquid}
\]

This matches HPE’s independent **115 kW liquid-cooled rack load** closely.

A realistic rack flow range is approximately:

\[
110-130\text{ LPM}
\]

depending on OEM/CDU and selected coolant temperature rise.

A compute tray has roughly:

\[
5.8\text{ kW}
\]

of GPU+CPU load.

A switch tray averages roughly:

\[
1.24\text{ kW}
\]

Thus the optimal flow distribution is **not equal flow**.

At 120 LPM total and equal desired coolant rise, a first-order target is approximately:

\[
6.0\text{ LPM per compute tray}
\]

and:

\[
1.3\text{ LPM per switch tray}
\]

The project should optimize manifold diameter/taper and branch restriction so that actual flows approach these thermal targets while satisfying a practical CDU pressure constraint such as:

\[
\Delta P\le115\text{ kPa}
\]

for a single-rack Vertiv CDU121-like system, or a larger pressure budget for an in-row CDU architecture.

That produces a rigorous, calculation-based, genuinely relevant AI-infrastructure thermal-fluid design project.

## Implementation research addendum — 2026-09-12

### Header/QD interpretation and constraint diagnostics — 2026-09-13

User reports manifold QDs as “-08 AN” but is unsure of their location; exact OEM/part number remains unidentified. Do not translate that label into a 12.7 mm header ID. AN -8 denotes the connection size associated with 8/16-inch tube OD, not a guaranteed QD flow bore; see [Holley/NOS size explanation](https://documents.holley.com/techlibrary_nos_system_types.pdf). The model's 38 mm is the main circular header INTERNAL diameter, independent of its equivalent 8 mm compute and 6 mm switch branch IDs and assumed QD resistance coefficients.

Primary-source research: [QCT GB200 NVL72 publication](https://blog.qct.io/wp-content/uploads/2025/04/QCT-Qoolrack-Stand-Alone_Advanced-Liquid-Cooling-for-NVIDIA-GB200-NVL72-Systems.pdf), p.3, identifies UQD04 blind-mate tray inlets. [Danfoss MGX component announcement, May 28 2026](https://www.danfoss.com/en/about-danfoss/news/dps/danfoss-power-solutions-supercharging-ai-data-centers-with-next-generation-nvidia-mgx-technology/) identifies UQD04, UQDB04 and 1-inch FD83 couplings plus EHW194-24 hose for its GB200 implementation. These do not establish the user's exact connector or a universal header diameter. AN-08 and UQD08 are not interchangeable specifications.

Calculated supply velocity at 120 L/min is 1.7635 m/s for a 38 mm ID, 2.4868 m/s for 32 mm, and 4.0744 m/s for 25 mm. The model's assumed 3 m/s ceiling alone requires at least 29.13 mm for a single full-flow circular passage. This supports 38 mm as a plausible exploration point, not a measured OEM dimension or optimum. Actual QD loss requires the mated-pair pressure-flow curve/Cv and count/topology; AN size alone cannot replace qdc_K.

Cd=0.62 remains an assumed thin sharp-edge approximation, not a calibrated value for drilled holes, chamfered entries, finite-length inserts or valve QDs. [The Lee Company](https://www.theleeco.com/insights/the-difference-between-calibrated-orifices-and-holes/?back=referrer) discusses edge geometry, viscosity/Reynolds dependence and calibrated restrictions. Do not optimize Cd as a free performance knob. A provisional sensitivity range, if used, is an engineering assumption rather than a guaranteed manufacturing tolerance.

Reproduced default-condition failures: 110 L/min gives HX_capacity margin -4643.33 W and assumed chip margin -1.421 K; 125 L/min exceeds CDU aggregate flow by 5 L/min; 35°C rack supply with 36°C FWS fails HX approach; 41°C rack supply exceeds the assumed chip target by 0.974 K; 32 mm constant headers exceed that target by only 0.075 K. These are converged nominal screens, not numerical failures. Dashboard now distinguishes these cases, shows each shortfall with an explanation, and retains computed results. Limits and physics have not been relaxed.

For controlled manual exploration at original load/PG25/40°C/120 L/min/36°C FWS, keep compute restriction zero and try switch restriction 0, 100, 150, 180, 190 million Pa/(kg/s)^2. Recomputed RMS errors are .7349, .1384, .0422, .0045, .0121; respective system heads are 79.83, 100.06, 103.56, 105.07, 105.51 kPa. These are resistance experiments, not calibrated orifice dimensions. Keep explicit orifices disabled while evaluating this added-resistance strategy to avoid unintended additive losses.

### Deployment and local startup correction — 2026-09-12

Follow-up correction for interactive Cloud errors: root `requirements.txt` now includes `.` to install the local scientific distribution, version 0.1.1, as a normal package. Preserve that installation even though the entrypoint has a source-path fallback: non-entrypoint imports and cache/worker contexts must also resolve `nvl72`. The earlier bootstrap alone was not a complete deployment dependency fix. The supplied Cloud log reports Python 3.14.7 and forcibly downgrades PyArrow 25; requirements now explicitly specifies `pyarrow<25`. Local validation remains Python 3.11, not a claim of hosted Python 3.14 validation. Regression coverage now includes repeated flow changes, all three coolant choices, in-row selection, and saved-result loading.

Streamlit Community Cloud installs declared dependencies, but the scientific package is located under `src/nvl72` and must be discoverable before importing it. `dashboard.py` now anchors `src`, configuration files and saved results to its own absolute directory. Keep this bootstrap before model imports; do not rely on a developer's installed wheel or `PYTHONPATH`. `run_app.py` starts Streamlit using the active interpreter; `.vscode/launch.json` provides F5 startup. `docs/RUNNING.md` is the primary beginner setup/deployment guide. The Cloud entrypoint remains `dashboard.py`, not the local launcher. Streamlit is pinned to the locally tested 1.63.0 in requirements and the dashboard extra. Python 3.11 is the tested Cloud selection. See [Cloud dependency handling](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies). An isolated-interpreter regression runs the dashboard outside the checkout and checks model origin, in-row configuration and saved results.

Retain the original specification above as source history. This addendum defines the new implementation parameters and overrides any implication that a computed nominal pass establishes hardware qualification.

### EG50 coolant option

`EG50` means **50% ethylene glycol by volume**, with inhibited Dow DOWTHERM SR-1 properties as a proxy. It does not mean 50% by mass or 50% commercial concentrate. Source: Dow-authored product information, June 2002, Form 180-01312-602 AMS, page 2, [archived manufacturer datasheet](https://users.obs.carnegiescience.edu/crane/pfs/man/Misc/Dowtherm-SR-1.pdf), inspected 2026-09-12. These are typical properties, not guaranteed specifications.

| Temperature °C | Density kg/m³ | cp J/(kg K) | Dynamic viscosity Pa s | Conductivity W/(m K) |
|---|---|---|---|---|
| 10 | 1078.72 | 3245 | 0.0055071 | 0.3724 |
| 40 | 1064.91 | 3361 | 0.0022567 | 0.3937 |
| 65 | 1050.05 | 3457 | 0.0012936 | 0.4062 |
| 90 | 1032.15 | 3554 | 0.0008227 | 0.4139 |
| 120 | 1006.66 | 3670 | 0.0005252 | 0.4168 |

`studies/build_property_table.py` reproduces these anchors in the combined CSV. Density, cp and conductivity interpolate linearly; viscosity interpolates logarithmically. Enthalpy integrates interpolated cp exactly. EG50 property evaluation rejects temperatures outside 10–120°C; this mathematical table range is NOT an allowable rack or pressure-dependent boiling envelope. EG50 CDU, seals, inhibitor and material qualification remains **unverified**. The supplied CDU121 data does not establish EG50 support. Fixed component mass-flow resistance curves and chip resistances remain uncalibrated across coolants; fluid comparisons capture resolved hydraulic/property effects, not a validated cold-plate performance map.

### Chip temperature and performance

[NVIDIA Grace Power and Thermals](https://docs.nvidia.com/dccpu/grace-perf-tuning-guide/power-thermals.html), inspected 2026-09-12, directs users to installed CPU thermal-zone passive/critical trip points and GPU temperature telemetry (`nvidia-smi -q -d TEMPERATURE`). Do not invent a universal optimal GPU/CPU/NVSwitch temperature band. The application reports estimated junction intervals, headroom to an assumed design ceiling, and headroom to user-entered manufacturer limits when available. No entered limit means unknown, not automatic manufacturer compliance.

New `chip_temperature` configuration defaults (all **ASSUMPTION**, not NVIDIA measurements):

| Component key | `resistance_range_K_W` | `target_max_C` | `manufacturer_limit_C` |
|---|---|---|---|
| GPU | [0.010, 0.020] | 80 | null |
| CPU | [0.020, 0.040] | 80 | null |
| NVSwitch | [0.015, 0.035] | 80 | null |

`Tj = tray outlet temperature + chip heat × total junction-to-coolant resistance`. Bounds are an engineering assumption envelope, not a confidence interval. Outlet coolant is a conservative reference; resistance must include package/interface/cold-plate effects. No flow dependence is inferred for these assumed resistances. Compute tray heat, including custom/auxiliary heat, is apportioned by configured GPU/CPU nameplate powers and counts; switch tray heat is divided over two ASICs. Default counts give 72 GPU, 36 CPU and 18 NVSwitch estimates grouped by tray/type. This conserves apportioned tray heat but does not resolve unequal device workloads. The older optional equivalent-tray channel model remains separate. A chip target failure now fails the nominal design screen. Hardware qualification remains unverified even when all entered constraints pass.

### Facility water and HX

New editable **ASSUMPTION** defaults: `facility.design_deltaT_K: 12`, `facility.minimum_hot_pinch_K: 0`, `cdu.rating_coolant: PG25`, `cdu.rating_supply_C: 40`. The 12 K design rise accommodates the original 150 L/min facility operating point; users can impose a tighter requirement. Existing facility return ceiling remains active. FWS supply and total CDU flow have independent dashboard controls; they no longer silently follow TCS supply. For an in-row CDU the flow and duty refer to all served racks.

Facility heat balance uses exact enthalpy. Allowed FWS return is the smallest of FWS supply + design rise, return ceiling, and TCS return − minimum hot pinch. Required mass flow is aggregate rack heat divided by that allowable enthalpy rise; volume flow uses inlet density. No positive allowable rise yields no finite required flow. Maximum FWS supply is TCS supply − required approach. Required counterflow UA uses both terminal differences and logarithmic mean temperature difference; nonpositive terminal differences do not yield a valid positive UA. Aggregate duty excludes unmodeled pump/motor heat and ambient gains. Facility pump head, water treatment and equipment selection require site data.

The rating screen now compares **mass flow × cp** to the PG25/40°C reference capacity rate, replacing the former calculation whose coolant density canceled and effectively compared volume flow only. This is a screening assumption, not an EG50 vendor HX rating. Capacity remains capped at the nominal rating and scaled by approach/capacity-rate ratios. Cold-end approach, hot-end pinch, return ceiling and the entered design-rise ceiling are checked independently.

### Individual orifices and design evaluation

Each branch class or `branches.overrides.<tray_id>` accepts `orifice_diameter_m` (null/absent disables) and `orifice_Cd` (assumed 0.62). Require 0 < bore < local tube ID and 0 < Cd <= 1. Let beta = bore/tube ID and Ao = pi bore²/4. Permanent loss is

`dp = m|m| [sqrt(1-beta^4(1-Cd²))-Cd beta²]² / (2 rho Cd² Ao²)`.

This incompressible thin-plate approximation includes pressure recovery, rather than treating pressure-tap differential as permanent loss. See [orifice loss research, Measurement (2025)](https://www.sciencedirect.com/science/article/abs/pii/S0263224125000466) and [ORNL velocity-of-approach relation](https://industrialresources.ornl.gov/measur/suite/docs/group__flow__calculations__adjusted__discharge__coefficient__formula). Small rack tubes and fixed Cd are not an ISO-certified meter implementation; calibrate bore, thickness, Reynolds dependence and downstream geometry before manufacturing. Added orifice loss is distinct from and additive to existing class/per-tray restrictions. Results expose bore, Cd and permanent loss per tray, plus its flow-weighted system-head contribution.

`config/orifice_example.yaml` illustrates two different bores and is explicitly not an optimized design. `config/eg50_example.yaml` illustrates all new thermal settings. `studies/extension_study.py` compares baseline and selected geometry across all three fluids and exports a separate `results/extension_study` directory, preserving historical study outputs.

### 2026-09-13 audit amendments (supersede conflicting earlier interpretations)

Read [the full current audit](docs/MODEL_AUDIT.md) before interpreting feasibility or hardware accuracy. Resolved input inventory and reproduced counterexamples are in `results/audit`; reproduce with `studies/audit_study.py`.

- **CDU ratings:** CDU121 121 kW at 4 K approach, 120 L/min at 115 kPa are nominal conditions, not a universal maximum-flow or minimum-approach envelope. The existing HX heuristic and assumed pump parabola are advisory by default. See the [Vertiv datasheet](https://www.vertiv.com/4a1be9/globalassets/shared/vertiv-coolchip-cdu-100_datasheet_en.pdf). Do not invent a larger pump/HX capability from stronger facility cooling.
- **XDU1350 reference:** default rating coolant is now water in in-row mode, matching the performance charts in the [application guide](https://www.vertiv.com/4a1b3f/globalassets/products/thermal-management/high-density-solutions/liebert-xdu1350-coolant-distribution-unit-application-and-planning-guide-sl-70618.pdf). 1,200 L/min remains the enforced two-pump aggregate flow envelope. Do not mix a three-pump flow rating with two-pump head/power. Reference property temperature 40°C remains assumed. The interpretation of the secondary 10–52°C range at both ends is provisional.
- **PG25 discrepancy:** new `PG25_Dow2023` data uses the versioned [Dow LC25 table](https://www.chempoint.com/products/download?doctype=tds&documentid=0103000121118930771670&grade=74883&language=English), Form 180-01627-01-0523, pp. 2–3. At 40°C: rho 1022.5 kg/m³, cp 3920 J/kg/K, viscosity .00158 Pa·s, conductivity .476 W/m/K. No extrapolation beyond −5–80°C. Existing `PG25` remains a legacy profile for reproducibility; its cp 4120 differs materially. Do not call either a verified installed-fluid formulation without identifying the actual product/revision.
- **Power:** [NVIDIA's power-budget example](https://docs.nvidia.com/mission-control/docs/systems-administration-guide/2.2.0/prs/faq.html) supports 5.8 kW combined GPU/CPU power per GB200 compute tray. Complete liquid capture and equal CPU splitting remain assumptions. The retained 11.16 kW switch figure was not independently reverified during this audit. Total 115.56 kW is modeled liquid duty, not full facility heat rejection.
- **Constraint semantics:** `feasible` now means all **enforced** requirements pass. `screening_pass` includes advisories. `minimum_normalized_margin` is enforced-only; `minimum_screening_margin` includes all checks. The assumed 80°C chip target is advisory, while entered manufacturer limits are enforced. Use `constraint_policy.enforce_assumptions: true` for strict screening or `constraint_policy.enforced` for explicit individual policy. Positive HX terminal differences cannot be disabled. The 1e-4 K guard is numerical, not a design margin. Old reports retain historical policy and must not be compared as unchanged pass-rate definitions.
- **Facility:** flow controls have no arbitrary upper cap. Optional `facility.available_capacity_W` and `facility.UA_W_K` are enforced if entered; null means unknown. `maximum_FWS_supply_C` is retained as a compatibility field but is only the supply corresponding to the nominal approach, not a proven physical maximum. Facility design rise/return ceilings and rack limits are separately editable assumptions/reference requirements. Primary-side hydraulic capability and control stability need site/CDU data.
- **Automatic orifices:** `balancing_mode: auto_equivalent` replaces class/per-tray balancing Kh with an equivalent thin-plate bore, preserving cold-plate and QD losses. With `z=(pi D²/4)sqrt(2 rho Kh)`, `d=D/[1+Cd²(2z+z²)]^(1/4)`. Kh=0 means no plate. Density is evaluated at solved branch mean temperature; default Cd=.62 remains uncalibrated. Automatic plus explicit fixed bore is rejected. The fixed-orifice YAML clears balancing Kh and saves per-tray bores; use it for off-design analysis. Mathematical inversion is verified, manufacturing accuracy is not.

The dashboard and reports expose mass, enthalpy/energy, pressure/friction, orifice, pump, HX, chip and optimization equations through `src/nvl72/equations.py`. Design CSVs contain constraint status, qualification gaps, weighted objective, flow error, temperature spread, estimated chip ceiling/headroom, head, pump power, header volume and facility requirements. Objective remains the existing normalized weighted sum of flow error, outlet spread, pressure, pump power and header volume; a low score never overrides failed constraints. Compare geometry scores under matched operating boundaries and weights. Coolant comparisons intentionally change fluid and retain the selected load/geometry/controls; pump mode can produce different operating flows. A static nominal screen is not a robustness probability or proof of an optimal design.

## 2026-09-20 — Separate dynamic fixed-versus-active comparison

User-requested scope: preserve the original fixed-orifice page and add a separate **Dynamic Flow Control** page. Entry is `pages/1_Dynamic_Flow_Control.py`; implementation is `src/nvl72/dynamic/`. Do not merge this UI into or replace the original analysis. `dashboard.py` only provides a session-state design handoff. Nested module changes must invalidate the recursive model fingerprint.

The frozen passive baseline is the original page’s current/exported design, or the existing `balance_locations` result at optimized-example geometry. This is minimum-head exact location balancing at fixed geometry, not a globally optimal manifold. Freeze bores once before changing workload or running parameter sweeps. Active valves replace balancing plates, retain all other losses, and add explicit valve-body loss. Both designs must receive the same pump-control policy. Demand-following pump control must protect the most under-supplied branch; tracking only summed flow can hide severe switch starvation. Do not claim that this heuristic is a proven global pump-energy optimizer.

Verified research: NVIDIA hardware confirms 18 compute/9 switch architecture. NVIDIA DPS recommends 11,160 W for the GB200 9-switch static electrical aggregate (1,240 W/tray if equally divided), not measured liquid heat. OCP manifold Table 3 gives a 1.5 m/s advisory; do not replace the original user constraint with a universal limit. OCP cold-plate loop guidance supports zero branch flow when dripless QDs disconnect. Belimo LRB24-SR is a representative NON-fail-safe HVAC actuator with 90 s stroke, 1.5 W running and 0.4 W holding. It is not a verified NVL72 component; commanded communications-loss opening assumes remaining power. Source URLs, parameter values, classifications and ranges are in `dynamic/sources.py`, downloadable from the new page; full rationale is `docs/DYNAMIC_FLOW_CONTROL.md`.

Transient thermal assumptions: whole-tray solid/coolant nodes, compute R=.004 K/W and Cs=12000 J/K, switch R=.012 K/W and Cs=4000 J/K, local coolant C=1200 J/K. These are low-confidence adjustable estimates. The representative solid temperature is not a GPU/CPU junction prediction. The 80°C target is assumed, not an OEM throttle limit. Electrical-to-liquid fractions remain explicit; defaults of one preserve the original heat assignment and are not calorimetry. Hydraulic rho/mu are frozen at reference thermal conditions; cp is fixed at inlet. Preserve this limitation in all conclusions. Maintained inlet temperature requires facility/CDU capacity; report HX/flow/velocity screens separately.

Solver shares the original hydraulic component evaluator, closes every open pump-to-branch loop, eliminates manifold-node mass balance by downstream cumulative flow, and advances thermal storage conservatively with implicit Euler. Zero-leakage valves and disconnected QDs can give exact zero flow. Detached trays have zero applied power but retain heat storage; their stagnant-fluid temperatures are excluded from operating thermal screens until reconnection. No air-purge, water-hammer, throttling/shutdown, or pump efficiency map is modeled.

Research studies: six synthetic workload families plus maintenance/reinstallation, four active controllers (including optimized variable diameter) versus three pump policies, stuck/sensor/communications/pump-lag faults, commanded fallback comparison, 27 physical/economic sensitivity axes, operating-condition break-even sweeps and finite-horizon sustained thermal capacity. Random traces are inspired by published H100 measurements, not fitted NVL72 traces. Cost ranges are engineering budgets, not supplier quotes. Annualized economics are conditional on repeating the chosen scenario; include actuator electricity and incremental maintenance. Never present an energy-saving but thermally failing configuration as preferable.

Reproduce results with `python studies/dynamic_flow_study.py --full`; outputs reside in `results/dynamic/`. Run the full pytest suite, including `tests/test_dynamic.py`, before delivery. Read `docs/DYNAMIC_RESULTS.md` for calculated outcomes; do not hardcode a favorable active-control conclusion.

### 2026-09-20 — optimized active diameter selection

The Dynamic Flow Control sidebar now exposes an **Optimized variable orifice diameter** strategy. For each controlled branch, the controller maps the power-derived target mass flow to an effective area using the quadratic restriction relation `d ∝ sqrt(m_dot)`, then applies bounded temperature trim and finite actuator stroke. The hydraulic solver records `orifice_diameter_mm` at every timestep; this is an effective diameter from the surrogate valve-area model, not a measured valve Cv curve or a manufacturing recommendation.

The comparison always computes both the fixed baseline and an active trial. In optimized mode, the active trial is accepted only when it passes thermal, pressure-closure, mass-closure and energy-closure screens and has a lower dimensionless weighted score (flow mismatch, temperature overshoot, pump/auxiliary power, peak head, worst flow error and actuator travel). Otherwise the displayed active result is an exact fixed-orifice fallback and economics use zero incremental active hardware. This prevents a worse active configuration from being presented as an improvement. Other controller modes remain available as diagnostic experiments and are shown without automatic winner selection.

The score weights and fallback tolerance are editable advanced assumptions. They are a selection rule, not a proof of global optimality. The page reports the rejected active trial separately in the downloaded JSON (`active_candidate`) and explains every headline output in the **What each output means** guide. A run is explicit: changing controls hides stale results until the user runs the comparison again. Full regression validation after this change: 63 tests passed; one matplotlib legend warning is cosmetic.

### 2026-09-22 — active-page audit corrections (supersedes September 20 sizing claims)

The earlier square-root correction applied to actuator opening was not the solver's bore inversion. `hydraulic.size_positions` now evaluates the existing permanent-loss coefficient, scales it by `(actual mass / target mass)^2`, inverts that SAME coefficient law to a bore and maps bore area to actuator position. The network is then solved again with finite actuator response. This is local hydraulic feedback sizing, not a global optimizer; local pressure is held only for the sizing step. No temperature-feedback claim is made for this mode.

Compare raw adaptive operation and active valves held at initial resistance-matching positions, retaining real body losses and holding/control electricity. Offline design selection can retain fixed hardware if no thermally passing active candidate lowers the score without worsening peak solid/outlet temperature, auxiliary power, peak head, RMS or worst flow mismatch (1e-7 numerical tolerance). Fixed selection is NOT active hardware physically bypassing its losses. Fault trials bypass offline fallback so their consequences remain visible. All raw trials are retained in outputs. Zero controlled hardware now correctly removes active overhead capital and incremental maintenance. Stationary active hardware still costs money and consumes holding power.

Fixed no-plate branches display pipe ID in bore heat maps, explicitly identified as unrestricted. All-tray adaptive bore and bore-change maps plus flow/difference maps expose rejected trials. Main controls, advanced assumptions and individual service schedules are in the sidebar; equations use separate LaTeX blocks. Output explanations include units and interpretation.

Heat-spike correction: do not truncate at 80% of duration; pulses run from event to event+spike, clipped only by the simulation window. Duty zero means no bursts, duty one means continuous high load. `service_events` overlays independently selected trays with disconnect/reconnect/ramp times, validated for temporal ordering. Events are resolved at the next timestep. Disconnection closes QDs and removes applied heat; reconnect ramps QD area and workload together as an assumed procedure. It does not model air purge, fluid replacement, operator sequencing or pressure surge. All timing/load statistics remain synthetic, not NVL72 measured values.

Primary-source recheck on 2026-09-22: OCP Cold Plate Cooling Loop Requirements Rev 2, p.13 supports closure at both ends of disconnected dripless QDs (https://www.opencompute.org/documents/cold-plate-cooling-loop-requirements-rev-2-pdf). Belimo LRB24-SR official page still lists 90 s stroke, 1.5 W running, 0.4 W holding (https://www.belimo.com/us/shop/en_US/p?code=LRB24-SR). These are HVAC example actuator values, not an NVL72 component qualification. Numerical tests include independent servicing, exact local sizing-law inversion, endpoint duty/spike behavior, non-regression selection, zero-increment fallback economics, and preservation of fault consequences.

Validation for September 22 revision: 73 tests passed, including Streamlit sidebar servicing inputs and rendered LaTeX, independent two-tray service events, mass/energy/pressure conservation, local bore-law inversion, duty endpoints, and selection/fault behavior. Local browser inspection verified same-tab entry, populated comparison and heat maps, and rendered equation typography. Hosted Streamlit deployment was not performed in this audit.
