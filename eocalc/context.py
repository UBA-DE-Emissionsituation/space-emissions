# -*- coding: utf-8 -*-
"""Defines some classes useful in the context of emission reporting."""

from enum import Enum, auto


class Pollutant(Enum):
    """Defines list of air pollutants considered for this project."""

    NO2 = auto()
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
    B_Industry = auto()
    C_OtherStationaryComb = auto()
    D_Fugitive = auto()
    E_Solvents = auto()
    F_RoadTransport = auto()
    G_Shipping = auto()
    H_Aviation = auto()
    I_Offroad = auto()
    J_Waste = auto()
    K_AgriLivestock = auto()
    L_AgriOther = auto()
    M_Other = auto()
    N_Natural = auto()
    O_AviCruise = auto()
    P_IntShipping = auto()
    z_Memo = auto()

    def __str__(self):
        return self.name
