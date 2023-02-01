#  __  __           ___                   _
# |  \/  |__ _ _ __| __|__ _ _ _ __  __ _| |_
# | |\/| / _` | '_ \ _/ _ \ '_| '  \/ _` |  _|
# |_|  |_\__,_| .__/_|\___/_| |_|_|_\__,_|\__|
#             |_|
# Map Format
from random import random as pyrandom
import uuid
from typing import List, Optional
import logging


class TimberbornSize(dict):
    def __init__(self, X: int, Y: int):
        dict.__init__(self, X=X, Y=Y)


class TimberbornArray(dict):
    def __init__(self, Array: List[object]):

        array_str = " ".join([str(x) for x in Array])

        dict.__init__(self, Array=array_str)


class TimberbornMapSize(dict):
    def __init__(self, Size: TimberbornSize):
        dict.__init__(self, Size=Size)


class TimberbornTerrainMap(dict):
    def __init__(self, Heights: TimberbornArray):
        dict.__init__(self, Heights=Heights)


class TimberbornSoilMoistureSimulator(dict):
    def __init__(self, MoistureLevels: TimberbornArray):
        dict.__init__(self, MoistureLevels=MoistureLevels)


class TimberbornWaterMap(dict):
    def __init__(self, WaterDepths: TimberbornArray, Outflows: TimberbornArray):
        dict.__init__(self, WaterDepths=WaterDepths, Outflows=Outflows)


class TimberbornSingletons(dict):
    def __init__(
        self,
        MapSize: TimberbornMapSize,
        SoilMoistureSimulator: TimberbornSoilMoistureSimulator,
        TerrainMap: TimberbornTerrainMap,
        WaterMap: TimberbornWaterMap,
    ):
        dict.__init__(
            self,
            MapSize=MapSize,
            SoilMoistureSimulator=SoilMoistureSimulator,
            TerrainMap=TerrainMap,
            WaterMap=WaterMap,
        )


class TimberbornEntity(dict):
    def __init__(self, TemplateName: str):
        id = f"{uuid.uuid4()}"
        dict.__init__(self, Id=id, TemplateName=TemplateName)


class TimberbornCoordinates(dict):
    def __init__(self, X: int, Y: int, Z: int):
        dict.__init__(self, X=X, Y=Y, Z=Z)


class TimberbornOrientation(dict):
    def __init__(self, Value: str = "Cw0"):
        dict.__init__(self, Value=Value)


class TimberbornBlockObject(dict):
    def __init__(self, Coordinates: TimberbornCoordinates, Orientation: TimberbornOrientation):
        dict.__init__(self, Coordinates=Coordinates, Orientation=Orientation)


class TimberbornGrowable(dict):
    def __init__(self, GrowthProgress: float = 1.0):
        dict.__init__(self, GrowthProgress=GrowthProgress)


class TimberbornCoordinatesOffset(dict):
    def __init__(self, X: float, Y: float):
        dict.__init__(self, X=X, Y=Y)


class TimberbornCoordinatesOffseter(dict):
    def __init__(self, CoordinatesOffset: TimberbornCoordinatesOffset):
        dict.__init__(self, CoordinatesOffset=CoordinatesOffset)

    @classmethod
    def random(cls) -> "TimberbornCoordinatesOffseter":
        return cls(TimberbornCoordinatesOffset(pyrandom() * 0.25, pyrandom() * 0.25))


class TimberbornNaturalResourceModelRandomizer(dict):
    def __init__(self, Rotation: float, DiameterScale: float, HeightScale: float, round_to: int = 6):
        if round_to:
            Rotation = round(Rotation, round_to)
            DiameterScale = round(DiameterScale, round_to)
            HeightScale = round(HeightScale, round_to)

        dict.__init__(self, Rotation=Rotation, DiameterScale=DiameterScale, HeightScale=HeightScale)

    @classmethod
    def random(cls) -> "TimberbornNaturalResourceModelRandomizer":
        scale = (pyrandom() * 0.75) + 0.5
        return TimberbornNaturalResourceModelRandomizer(pyrandom() * 360, scale, scale)


class TimberbornYielderCuttable(dict):
    def __init__(self, Id: str, Amount: int):
        dict.__init__(
            self,
            Yield={
                "Good": {
                    "Id": Id,
                },
                "Amount": Amount,
            },
        )


# New Gatherable Objects
class TimberbornGatherableYieldGrower(dict):
    def __init__(self, GrowthProgress: float = -1.0, round_to: int = 2):
        if GrowthProgress < 0.0:
            GrowthProgress = pyrandom()
        if round_to:
            GrowthProgress = round(GrowthProgress, round_to)
        dict.__init__(self, GrowthProgress=GrowthProgress)


class TimberbornYielderGatherable(TimberbornYielderCuttable):
    pass


class TimberbornWateredObject(dict):
    def __init__(self, IsDry: bool):
        dict.__init__(self, IsDry=IsDry)


class TimberbornLivingNaturalResource(dict):
    def __init__(self, IsDead: bool):
        dict.__init__(self, IsDead=IsDead)


class TimberbornPrioritizable(dict):
    def __init__(self, Priority="Normal"):
        dict.__init__(self, Priority={"Value": Priority})


class TimberbornTreeComponents(dict):
    def __init__(
        self,
        BlockObject: TimberbornBlockObject,
        CoordinatesOffseter: TimberbornCoordinatesOffseter,
        Growable: TimberbornGrowable,
        LivingNaturalResource: TimberbornLivingNaturalResource,
        NaturalResourceModelRandomizer: TimberbornNaturalResourceModelRandomizer,
        WateredObject: TimberbornWateredObject,
        YielderCuttable: TimberbornYielderCuttable,
        GatherableYieldGrower: Optional[TimberbornGatherableYieldGrower] = None,
        YielderGatherable: Optional[TimberbornYielderGatherable] = None,
    ):
        dict.__init__(
            self,
            BlockObject=BlockObject,
            BuilderJob={},
            CoordinatesOffseter=CoordinatesOffseter,
            Demolishable={},
            Growable=Growable,
            LivingNaturalResource=LivingNaturalResource,
            NaturalResourceModelRandomizer=NaturalResourceModelRandomizer,
            Prioritizable=TimberbornPrioritizable(),
            WateredObject=WateredObject,
        )
        self["Yielder:Cuttable"] = YielderCuttable
        self["Inventory:GoodStack"] = {"Storage": {"Goods": []}}
        if GatherableYieldGrower:
            if not YielderGatherable:
                logging.error("Components spefied GatherableYieldGrower but not YielderGatherable,"
                              " may result game crashing on map validation.")
            else:
                self["GatherableYieldGrower"] = GatherableYieldGrower
                self["Yielder:Gatherable"] = YielderGatherable


class TimberbornTree(TimberbornEntity):
    def __init__(self, species: str, Components: TimberbornTreeComponents):
        TimberbornEntity.__init__(self, species)
        self["Components"] = Components


class TimberbornMap(dict):
    def __init__(
        self,
        GameVersion: str,
        Singletons: TimberbornSingletons,
        Entities: List[TimberbornEntity],
    ):
        dict.__init__(self, GameVersion=GameVersion, Singletons=Singletons, Entities=Entities)
