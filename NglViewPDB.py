import mdtraj as md
import nglview as nv

import os

class NglViewPDB:
    def __init__(self, pdb_path:str) -> None:
        pass

if __name__ == "__main__":

    pdb_dir = "pdb"
    pdb_root = "Ab42_seq"
    pdb_no = 1000

    #######
    
    pdb_name = f"{pdb_root}_{pdb_no}"
    pdb_path = os.path.join(pdb_dir, pdb_name)

    ngl_view = NglViewPDB(
        pdb_path=pdb_path
    )