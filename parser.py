import csv
import enum
import logging
import os
from typing import Dict, List, Union
from pathlib import Path, WindowsPath

class categories(enum.Enum, str):
    A ="A kategória",
    B ="B kategória",
    C ="C kategória",
    D ="D kategória",
    E ="E kategória",
    EP="E+ kategória",
    F ="F kategória",
    FP="F+ kategória",
    K ="K kategória",
    KP="K+ kategória"

def parse_data(tsv_path:Path) -> csv.DictReader[str]:
    if tsv_path.suffix != "tsv":
        logging.warning('The file format suggest wrong structure')
    with open(tsv_path,'r') as f:
        data = csv.DictReader(f,delimiter='\t')
    return data

"""
Select teams for local round if the teams are in the category "kicsik" ( == small)
"""
def select_lsmall_teams(data:csv.DictReader[str])->List[Dict]:
    r_ = list()
    for I in data:
        if I['Kategória'] == categories.A or I['Kategória'] == categories.B:
            r_.append(I)
    return r_

"""
Group teams by the location of local round.
retur data grupped by group_by id
default should be: "Helyszín (középiskola)"
"""
def group_teams(data:Union[csv.DictReader[str],List[Dict]],group_by:str)->Dict[str,List[Dict]]:
    r_:Dict = dict() 
    for I in data:
        if group_by not in I:
            raise ValueError(f"Groupping failed, there are no fileds: {group_by}")
        location = I[group_by]
        if location not in r_:
            r_[location] = list()
        r_[location].append(I)
    return r_


"""
Lookup enum for matching the possible BP school location datas with Full-Names.
"""
schoolLUT:Dict = {
    'VPG'  :"Békásmegyeri Veres Péter Gimnázium",
    'ELTE' :"ELTE Déli Tömb",
    'BPG'  :"Bornemissza Péter Gimnázium",
    'JÁG'  :"Jedlik Ányos Gimnázium",
    'SZIG' :"Szent István Gimnázium",
}

"""
Given custom implementation for BUdapest based teams, for specifying the locations further.
It requires a parsed tsc of the specification, and the groupped team list for the teams.
It appends the location of the writeing with a '-' at the end of the location, resulting in a special use-case.
It removes the data["Budapest"] location group.
When generating the folders the generator script MAY support the subfolder options for this.
"""
def specify_Bp_teams(bp_specific:csv.DictReader[str],data:Dict[str,List[Dict]],BP_name:str = "Budapest")->Dict[str,List[Dict]]:
    if BP_name not in data:
        logging.warning(f"Missing filed [{BP_name}] in data.")
    BP_list = data[BP_name]
    BP_data_list = group_teams(bp_specific,"Helyszín")
    for key in  BP_data_list:
        if key not in schoolLUT:
            raise ValueError(f"Unknown school code: {key}")
        fullname = schoolLUT[key]
        # create custom formatting for location name
        formatted_key = f"{fullname} - {BP_name}"
        data[formatted_key] = list()
        #traverse spec info list for given location
        for comparsion_info in BP_data_list[key]:
            #linear search the corresponding team based on team name match
            for team_data in BP_list:
                if team_data["Csapatnév"] == comparsion_info["Csapatnév"]:
                    data[formatted_key].append(team_data)
    del data[BP_name]
    return data

    
"""
20/21 parsing main modell
"""
def load_big_data()->Dict[str,List[Dict]]:
    team_info_big = Path("data_nagyok.tsv")
    info_BP = Path("data_nagyok_spec.tsv")
    data_reader = parse_data(team_info_big)
    datas = group_teams(data_reader,"Helyszín (középiskola)")
    bp_reader = parse_data(info_BP)
    datas = specify_Bp_teams(bp_reader,datas)
    return datas


