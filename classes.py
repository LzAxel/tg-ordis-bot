from pydantic import Field, BaseModel, validator
from typing import Optional
import re


class SortieMission(BaseModel):
    mission_type: str = Field(alias="missionType")
    modifier: str
    description: str = Field(alias="modifierDescription")
    location: str = Field(alias="node")


class Sortie(BaseModel):
    boss: str
    faction: str
    eta: str
    missions: list[SortieMission] = Field(alias="variants")


class Reward(BaseModel):
    name: str = Field(alias="asString")

    class Config:
        validate_assignment = True

    @validator('name')
    def set_empty_item(cls, name):
        if not name:
            return "None"
        else:
            return name
        

class AlertMission(BaseModel):
    location: str = Field(alias="node")
    description: str
    type: str
    faction: str
    reward: Reward


class Alert(BaseModel):
    mission: AlertMission
    active: bool
    eta: str


class Faction(BaseModel):
    faction: str
    reward: Reward


class Invasion(BaseModel):
    location: str = Field(alias="node")
    eta: str
    defender: Faction
    attacker: Faction
    completed: bool


class WorldState(BaseModel):
    name: str = Field(alias="id")
    state: Optional[str] = Field(alias="active")
    eta: str = Field(alias="timeLeft")

    class Config:
        allow_population_by_field_name = True

    @validator("state")
    def capitalize_state(cls, value):
        
        return value.capitalize()

    @validator("name", always=True)
    def set_name(cls, value):
        template = {
            "earth": "🌎 Earth",
            "cetus": "✨ Cetus",
            "cambion": "🔥 Cambion Drift",
            "vallis": "🌪 Orb Vallis"
        }
        value = value.split("Cycle")[0]
        if value in template.keys():
            return template[value]
        else:
            return value


class Article(BaseModel):
    title: str
    description: str
    date: str
    photo: str
    url: str


class APIDump(BaseModel):
    timestamp: str
    sortie: Sortie
    invasions: list[Invasion]
    alerts: list[Alert]
    cetusCycle: Optional[WorldState]
    vallisCycle: Optional[WorldState]
    cambionCycle: Optional[WorldState]
    earthCycle: Optional[WorldState]
    cycles: Optional[list[WorldState]]

    @validator("invasions")
    def validate_invasion(cls, value):
        value = [i for i in value if not i.completed]

        return value


    @validator("cycles", always=True)
    def validate_cycles(cls, value, values):
        if value:
            return value
        else:
            value = []
            cycle_list = [re.findall("\D*Cycle", i) for i in values.keys()]
            cycle_list = [i[0] for i in cycle_list if i]
            for i in cycle_list:
                value.append(values[i])
            return value


class RelicReward(BaseModel):
    name: str = Field(alias="itemName")
    rarity: Optional[str] = Field(alias="chance")


class Relic(BaseModel):
    name: str = Field(alias="relicName")
    tier: str = Field(alias="tier")
    rewards: list[RelicReward]
        
    @validator("rewards")
    def validate_rewards(cls, value):
        return sorted(value, key = lambda i: (float(i.rarity)))