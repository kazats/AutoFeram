from src.lib.common import Vec7
from src.lib.Config import SolidSolution


BST = SolidSolution(
    mass_amu            = 40.9285,
    a0                  = 3.9435,
    Z_star              = 9.807238756,
    B11                 = 129.0286059,
    B12                 = 39.00720516,
    B44                 = 45.26949109,
    B1xx                = -143.7185938,
    B1yy                = -1.375464746,
    B4yz                = -15.02208695,
    P_k1                = -166.56247,
    P_k2                = 157.2518592,
    P_k3                = 515.9414896,
    P_k4                = 390.6570497,
    P_alpha             = 50.68630712,
    P_gamma             = -72.18357441,
    P_kappa2            = 9.4250031,
    j                   = Vec7(-2.048250285, -1.472144446, 0.6396521198, -0.5891190367, 0.0, 0.2576732039, 0.0),
    epsilon_inf         = 6.663371926,
    modulation_constant = -0.279,
    # acoustic_mass_amu   = 41.67
)
