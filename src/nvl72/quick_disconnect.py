"""QD loss models; diameter scaling is an estimate, not a vendor Cv curve."""
import numpy as np

def mass_coefficient(branch,rho):
    mode=branch.get('qdc_model','fixed')
    if mode=='fixed': return branch['qdc_K']
    if mode!='diameter_scaled': raise ValueError('QD model must be fixed or diameter_scaled')
    diameter=branch.get('qdc_diameter_m',0)
    reference=branch.get('qdc_reference_diameter_m',0)
    density=branch.get('qdc_reference_density_kg_m3',0)
    if min(diameter,reference,density,rho)<=0:
        raise ValueError('QD diameter, reference diameter and reference density must be positive')
    # Constant dimensionless loss referenced to QD bore velocity:
    # dp = zeta*m²/(2*rho*A²). Kh_ref already covers the complete QD path.
    return branch['qdc_K']*(reference/diameter)**4*density/rho

def velocity(mass_flow,rho,branch):
    diameter=branch.get('qdc_diameter_m')
    return None if diameter is None else float(mass_flow/(rho*np.pi*diameter**2/4))
