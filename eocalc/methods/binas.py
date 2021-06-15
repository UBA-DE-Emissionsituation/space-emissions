# -*- coding: utf-8 -*-
"""Basic selection of standard parameters."""


earth_radius = 6378. #km
# atom masses (table 38)
xm_H     =    1.00790e-3     # kg/mol
xm_N     =   14.00670e-3     # kg/mol
xm_C     =   12.01115e-3     # kg/mol
xm_S     =   32.06400e-3     # kg/mol
xm_O     =   15.99940e-3     # kg/mol

# molecule masses:
xm_H2O   =  xm_H*2 + xm_O    # kg/mol
xm_NO    =  xm_N + xm_O      # kg/mol
xm_NO2   =  xm_N + xm_O * 2  # kg/mol
xm_NH3   =  xm_N + xm_H * 3  # kg/mol
xm_SO2   =  xm_S + xm_O * 2  # kg/mol

# Avogadro number
Avog = 6.02205e23      # mlc/mol

conversion_factor_mol_m2_1e15_molecules_cm2 = 6.02214e+4