# -*- coding: utf-8 -*-
"""Defines some classes useful in the context of emission reporting."""

from enum import Enum, auto


class Pollutant(Enum):
    """Defines list of air pollutants to be consideres in this project."""

    NOx = auto()
    SO2 = auto()
    NH3 = auto()
    PM2_5 = auto()


class GNFR(Enum):
    """
    Defines list of gridded NFR (GNFR) sectors.

    Defines complete list of GNFR (Gridded Nomenclature For Reporting)
    sectors, as defined in the context of the UNECE/LRTAP convention
    and the relevant guidelines.
    """

    A_PublicPower = auto()
    B_IndustrialComb = auto()
    C_SmallComb = auto()
    D_IndProcess = auto()
    E_Fugitive = auto()
    F_Solvents = auto()
    G_RoadRail = auto()
    H_Shipping = auto()
    I_OffRoadMob = auto()
    J_AviLTO = auto()
    K_CivilAviCruise = auto()
    L_OtherWasteDisp = auto()
    M_WasteWater = auto()
    N_WasteIncin = auto()
    O_AgriLivestock = auto()
    P_AgriOther = auto()
    Q_AgriWastes = auto()
    R_Other = auto()
    S_Natural = auto()
    T_IntAviCruise = auto()
    z_Memo = auto()
