from openbabel import pybel
from openbabel import openbabel as ob
import numpy as np
import getopt, sys, os, subprocess, pkg_resources, glob 
from dataclasses import dataclass, field, asdict
from Common             import * 
from Molecule           import Molecule 
from SolventBox         import SolventBox 
from AntechamberDocker  import AntechamberDocker 
from TleapDocker        import TleapDocker 
from PackmolDocker      import PackmolDocker
from ParmchkDocker      import ParmchkDocker 
import tools 



def update_mol(mol: object) -> None:
    r'''
    @TODO: 
        1. implement update for solute, or there is no need to update solute 
    '''
    if mol.mol_type == 'solvent': 
        update_solvent(mol)
    elif mol.mol_type == 'solute': 
        '''
        @TODO:
        figure out if solvent and solute are treat differently 
        '''
        update_solvent(mol)
    else: 
        raise Exception('mol_type is not set')
       
        


def update_solvent(mol: object) -> None:
    #four cases: 

    #solvent ready in amber library
    if mol.pdb is None and mol.xyz is None: 
        if mol.box is not None and mol.frcmod is not None and mol.lib is not None: 
            return 
    

    #only has xyz ready 
    if mol.xyz is not None and mol.pdb is None:
        if mol.box is None and mol.frcmod is None and mol.lib is None and mol.mol2 is None: 
            tools.xyz_to_pdb(mol) 
            mol.update()
            update_solvent(mol) 
            return


    #solvent ready in data/ folder  
    if mol.pdb is not None: 
        if mol.frcmod is not None:
            if mol.mol2 is None and mol.lib is None: 
                '''
                @TODO: 
                1. double check with Fangning if it is ok to only have frcmod file 
                2. I dont see how this case is different from the case below
                ''' 
                pass 

    #custome solvent only has pdb file 
    if mol.pdb is not None: 
        '''
        @TODO:
        1. custome solvent. use AntechamberDocker to convert the solvet 
        '''
        ante = AntechamberDocker() 
        ante.run(mol)
        mol.update() 
        
        parmk = ParmchkDocker() 
        parmk.run(mol) 
        mol.update() 

        tleap = TleapDocker() 
        tleap.run(mol)
        mol.update()
        return 



def update_box(box: object) -> None: 
    tleap_box(box) 


def pack_box(box: object) -> None: 
    pack = PackmolDocker() 
    pack.run(box) 
    tools.edit_system_pdb(box)
    box.update()
    


def tleap_box(box: object) -> None: 
    tleap = TleapDocker() 
    tleap.run(box) 
    box.update() 

