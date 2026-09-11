"""Regenerate checked-in tables. Optional build dependency: iapws==1.5.5.

Water: IAPWS97 at 0.1 MPa. PG25: preserves agent.md 40/50 C anchors;
linear rho/cp, log-linear mu extrapolation are explicitly ESTIMATE outside anchors.
Conductivity slope 0.0009 W/m/K² is ASSUMPTION; only 40 C is supplied.
"""
from pathlib import Path
import csv
import math
from iapws import IAPWS97
root = Path(__file__).resolve().parents[1]
with (root/'data/coolant_properties.csv').open('w') as f:
    writer = csv.writer(f)
    writer.writerow(['coolant','T_K','rho_kg_m3','cp_J_kg_K','mu_Pa_s','k_W_m_K','category','source'])
    for C in range(5,96,5):
        w = IAPWS97(T=C+273.15,P=0.1)
        writer.writerow(['water',C+273.15,w.rho,w.cp*1000,w.mu,w.k,'DERIVED','IAPWS97, iapws 1.5.5, 0.1 MPa'])
        writer.writerow(['PG25',C+273.15,1020-0.5*(C-40),4120+(C-40),0.00147*math.exp(math.log(1.15/1.47)*(C-40)/10),0.476+0.0009*(C-40),'3P' if C==40 else 'ESTIMATE','agent.md section 8 anchors; other values modeled extensions'])
