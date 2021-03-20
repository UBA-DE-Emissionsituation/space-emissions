# -*- coding: utf-8 -*-

from enum import Enum, auto

class Pollutant(Enum):
    NOx = auto()
    SO2 = auto()
    NH3 = auto()
    PM2_5 = auto()

class GNFR(Enum):
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