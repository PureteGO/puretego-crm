"""
PURETEGO CRM - SaaS Limits & Constants
Defines default limits for each plan tier.
"""

# Plan Tiers
PLAN_SOLO = 'solo'
PLAN_LEAN = 'lean'
PLAN_PURETEGO = 'puretego'  # Full, unrestricted package

PLAN_CHOICES = [
    (PLAN_SOLO, 'Solo Pro (Freelancer)'),
    (PLAN_LEAN, 'Agency Lean (Small Team)'),
    (PLAN_PURETEGO, 'PureteGO Official (Full Scale)')
]

# Default Configuration per Plan
PLAN_DEFAULTS = {
    PLAN_SOLO: {
        'max_users': 2,
        'included_roles': ['owner', 'sdr'],  # Solo usually acts as both
        'modules': ['crm', 'gbp_basic', 'proposals'],
        'max_locations': 5,
        'monthly_health_checks': 15,
        'max_keywords': 50,
        'support_level': 'email'
    },
    PLAN_LEAN: {
        'max_users': 5,
        'included_roles': ['owner', 'manager', 'sales', 'sdr'],
        'modules': ['crm', 'gbp_basic', 'gbp_advanced', 'proposals', 'reports'],
        'max_locations': 25,
        'monthly_health_checks': 60,
        'max_keywords': 250,
        'support_level': 'priority_email'
    },
    PLAN_PURETEGO: {
        'max_users': 9999,  # Unlimited
        'included_roles': ['owner', 'manager', 'sales', 'sdr', 'traffic', 'creative', 'finance'],
        'modules': ['crm', 'gbp_basic', 'gbp_advanced', 'proposals', 'reports', 'projects', 'tickets', 'finance'],
        'max_locations': 9999, # Tiered / Unlimited
        'monthly_health_checks': 9999,
        'max_keywords': 9999,
        'support_level': 'dedicated'
    }
}

def get_plan_config(plan_tier):
    """Returns the default configuration for a given plan tier."""
    return PLAN_DEFAULTS.get(plan_tier, PLAN_DEFAULTS[PLAN_SOLO])
