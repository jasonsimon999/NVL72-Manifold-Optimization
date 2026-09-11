"""Optional equivalent tray channel model, not an individual silicon prediction."""
import numpy as np
from .components import friction_factor

def channel_model(m, heat, mean_T, props, spec):
    w=spec['channel_width_m']; b=spec['channel_height_m']; n=spec['channels']
    dh=2*w*b/(w+b); v=m/(props.rho*n*w*b); re=props.rho*v*dh/props.mu
    f=friction_factor(re)
    nu_t=(f/8)*np.maximum(re-1000,0)*props.Pr/(1+12.7*np.sqrt(f/8)*(props.Pr**(2/3)-1))
    blend=np.clip((re-2300)/1700,0,1)
    nu=(1-blend)*spec['laminar_Nu']+blend*nu_t
    h=nu*props.k/dh
    rconv=1/(h*spec['heated_area_m2'])
    total=spec['tim_K_W']+spec['spreader_K_W']+spec['plate_K_W']+rconv
    return {'Re':re,'Pr':props.Pr,'Nu':nu,'h_W_m2_K':h,'R_conv_K_W':rconv,
            'T_chip_equivalent_K':mean_T+heat*total,
            'channel_dp_Pa':f*spec['length_m']/dh*props.rho*v*v/2}
