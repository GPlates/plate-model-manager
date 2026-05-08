from enum import Enum


class ReferenceFrame(Enum):
    PmagReferenceFrame = "PMAG"
    MantleReferenceFrame = "MantleFrame"


class GenerationMethod(Enum):
    Isochrons = "UsingIsochrons"
    Topologies = "UsingTopologies"
