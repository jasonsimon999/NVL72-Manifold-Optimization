"""Seeded synthetic scenarios, not measured NVL72 traces."""
import numpy as np

def generate(kinds, s):
    t = np.arange(0, s['duration_s'] + s['dt_s']*.5, s['dt_s'])
    n = len(kinds); compute = np.array(kinds) == 'compute'
    u = np.ones((len(t), n)); connected = np.ones_like(u)
    low, high = s['low_load'], s['high_load']
    name = s['scenario']; event = s['event_s']
    u[:, compute] = high
    if name in ('rack_step', 'localized'):
        u[:, compute] = low
        affected = np.where(compute)[0]
        if name == 'localized': affected = affected[:int(s['localized_count'])]
        pulse = (t >= event) & (t < event+s['spike_s'])
        u[np.ix_(pulse, affected)] = high
    elif name == 'bursts':
        on = ((t % (s['spike_s']/max(s['duty'], .001))) < s['spike_s']) & (s['duty']>0)
        u[:, compute] = np.where(on, high, low)[:, None]
    elif name == 'heterogeneous':
        rng = np.random.default_rng(int(s['seed']))
        block = np.floor(t/s['spike_s']).astype(int)
        common = rng.random(block.max()+1) < s['duty']
        independent = rng.random((block.max()+1,n)) < s['duty']
        shared = rng.random((block.max()+1,n)) < s['correlation']
        binary = np.where(shared, common[:,None], independent)
        raw = low + (high-low)*binary[block]
        u[:,compute] = raw[:,compute]
        for j in range(1,len(t)):
            u[j,compute] = u[j-1,compute] + np.clip(u[j,compute]-u[j-1,compute],-s['ramp_per_s']*s['dt_s'],s['ramp_per_s']*s['dt_s'])
    if name.startswith('remove') or name == 'reinstall':
        indices = np.where(~compute if name == 'remove_switch' else compute)[0]
        indices = indices[:3 if name == 'remove_several' else 1]
        for i in indices:
            connected[t >= event,i] = 0
            if name == 'reinstall':
                after = t >= s['reconnect_s']
                connected[after,i] = np.clip((t[after]-s['reconnect_s'])/s['reconnect_ramp_s'],0,1)
            # Power disabled while disconnected and ramped with the service procedure.
            u[:,i] *= connected[:,i]
    # Explicit service schedules overlay any workload, independently per tray.
    for e in s.get('service_events',[]):
        i=int(e['tray']); start=e['disconnect_s']; end=e.get('reconnect_s')
        if not 0<=i<n:raise ValueError('Service tray index is outside this rack')
        fraction=np.ones(len(t));fraction[t>=start]=0.
        if end is not None:
            after=t>=end
            fraction[after]=np.clip((t[after]-end)/e['ramp_s'],0,1)
        connected[:,i]=np.minimum(connected[:,i],fraction)
        u[:,i]*=fraction
    return t, u, connected
