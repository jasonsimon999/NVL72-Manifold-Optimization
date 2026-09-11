"""Temperature-dependent tabular properties and exact piecewise-linear cp integrals."""
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Properties:
    rho: np.ndarray
    cp: np.ndarray
    mu: np.ndarray
    k: np.ndarray
    @property
    def Pr(self): return self.cp * self.mu / self.k

class Coolant:
    def __init__(self, name: str, file: str, viscosity_multiplier: float = 1.0):
        frame = _read(file)
        frame = frame[frame.coolant == name].sort_values('T_K')
        if frame.empty: raise ValueError(f'Unknown coolant {name}')
        self.name = name
        self.T = frame.T_K.to_numpy()
        self.table = frame[['rho_kg_m3', 'cp_J_kg_K', 'mu_Pa_s', 'k_W_m_K']].to_numpy()
        if len(self.T)<2 or np.any(np.diff(self.T)<=0) or np.any(~np.isfinite(self.table)) or np.any(self.table<=0):
            raise ValueError('Property table must have increasing temperatures and positive finite properties')
        self.mu_factor = viscosity_multiplier
        self.cp_slope = np.diff(self.table[:, 1]) / np.diff(self.T)
        self.H = np.r_[0, np.cumsum(np.diff(self.T) * (self.table[1:, 1] + self.table[:-1, 1]) / 2)]

    def _check(self, t):
        t = np.asarray(t, dtype=float)
        if np.any(~np.isfinite(t)) or np.any(t < self.T[0]) or np.any(t > self.T[-1]):
            raise ValueError(f'{self.name} property range {self.T[0]-273.15:g}–{self.T[-1]-273.15:g} °C exceeded; no silent extrapolation')
        return t

    def properties(self, T) -> Properties:
        t = self._check(T)
        vals = [np.interp(t, self.T, self.table[:, i]) for i in range(4)]
        # Log interpolation preserves positive viscosity and its curved trend.
        vals[2] = np.exp(np.interp(t, self.T, np.log(self.table[:, 2]))) * self.mu_factor
        return Properties(*vals)

    def enthalpy(self, T):
        t = self._check(T)
        i = np.clip(np.searchsorted(self.T, t, side='right') - 1, 0, len(self.T)-2)
        d = t-self.T[i]
        return self.H[i] + self.table[i, 1]*d + self.cp_slope[i]*d*d/2

    def temperature(self, h):
        h = np.asarray(h, dtype=float)
        if np.any(~np.isfinite(h)) or np.any(h < -1e-8) or np.any(h > self.H[-1]+1e-8):
            raise ValueError(f'{self.name} enthalpy outside property range; insufficient coolant flow or invalid thermal state')
        i = np.clip(np.searchsorted(self.H, h, side='right')-1, 0, len(self.H)-2)
        dh = h-self.H[i]; cp = self.table[i, 1]; slope = self.cp_slope[i]
        d = 2*dh/(cp + np.sqrt(cp*cp+2*slope*dh))
        return self.T[i]+d

@lru_cache(maxsize=8)
def _read(file): return pd.read_csv(file)
