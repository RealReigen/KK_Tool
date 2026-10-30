"""Registro de pestañas. Para añadir una: crear su archivo y añadirla a TABS."""
from .read_tab import ReadTab
from .futa_tab import FutaTab
from .donor_tab import DonorTab
from .repair_tab import RepairTab

TABS = [ReadTab, FutaTab, DonorTab, RepairTab]
