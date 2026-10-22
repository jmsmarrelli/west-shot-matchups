import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from matchup import leave_pairing_out

def test_absent_pairing_zone_keeps_rest_of_season_profile():
    rows=[(2025,"A","B","Restricted Area",10),(2025,"A","C","Restricted Area",10),
          (2025,"A","C","Corner 3",10),(2025,"D","B","Corner 3",10)]
    p=pd.DataFrame(rows,columns=["season","offence","defence","zone5","att"])
    x=leave_pairing_out(p).query("offence == 'A' and defence == 'B'").iloc[0]
    assert x["actual_share_Corner 3"] == 0
    assert x["off_share_Corner 3"] == .5
    assert x["def_share_Corner 3"] == 1

def test_duplicate_pairing_zone_fails_loudly():
    p=pd.DataFrame([(2025,"A","B","Restricted Area",10)]*2,
                   columns=["season","offence","defence","zone5","att"])
    with pytest.raises(ValueError):leave_pairing_out(p)
