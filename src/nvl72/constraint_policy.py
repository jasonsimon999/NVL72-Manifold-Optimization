"""Separate physical/user requirements from unverified rating extrapolations."""
ADVISORY = {
 'CDU_external_head':'Published nominal head point, not a measured pump envelope.',
 'pump_curve':'Assumed shutoff parabola; manufacturer curve unavailable.',
 'CDU_aggregate_flow':'CDU121 nominal flow is not a verified maximum.',
 'HX_capacity':'Heuristic rating scaling, not a measured HX capacity map.',
 'HX_approach':'Published rating approach, not a universal minimum approach.',
 'chip_assumed_target':'Assumed resistance and 80°C design target; not a verified hardware limit.',
 'CDU_secondary_max_temperature':'Conservatively applied at both ends; vendor range boundary needs confirmation.',
 'CDU_secondary_min_temperature':'Conservatively applied at both ends; vendor range boundary needs confirmation.',
}

def apply_policy(c, constraints):
    policy=c.get('constraint_policy',{})
    strict=policy.get('enforce_assumptions',False)
    overrides=policy.get('enforced',{})
    if not isinstance(strict,bool) or not isinstance(overrides,dict) or any(not isinstance(v,bool) for v in overrides.values()):
        raise ValueError('Constraint policy requires boolean enforcement settings')
    unknown=set(overrides)-set(constraints)
    if unknown: raise ValueError(f'Unknown constraint override: {sorted(unknown)}')
    physical={'HX_cold_pinch','HX_hot_pinch'}
    for name,v in constraints.items():
        advisory=name in ADVISORY
        if name=='CDU_aggregate_flow' and c['cdu']['mode']=='in_row': advisory=False
        enforced=bool(overrides.get(name,not advisory or strict))
        if name in physical: enforced=True
        v.update(enforced=enforced,basis=ADVISORY[name] if advisory else 'Physical condition or explicitly configured design requirement.')
