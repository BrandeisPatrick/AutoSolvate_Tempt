from .molecule import *
from .dockers import *
from .utils import *

amber_solv_dict = {'water':     [' ','TIP3PBOX '],
                   'methanol':  ['loadOff solvents.lib\n loadamberparams frcmod.meoh\n', 'MEOHBOX '],
                   'chloroform':['loadOff solvents.lib\n loadamberparams frcmod.chcl3\n', 'CHCL3BOX '],
                   'nma':       ['loadOff solvents.lib\n loadamberparams frcmod.nma\n', 'NMABOX ']}

custom_solv_dict = {'acetonitrile':'ch3cn'}
custom_solv_residue_name = {'acetonitrile':'C3N'}

class AmberParamsBuilder(object):
    """ 
    This class handles the Amber parameter creation for one single molecule.
    1. Generate standard pdb
    2. AnteChamber or Gaussian charge fitting
    3. Tleap create Lib
    """
    def __init__(self, xyzfile:str, name = "", resname = "", charge = 0, spinmult = 1, 
                 charge_method="resp", folder = WORKING_DIR, **kwargs):
            
            self.folder = folder
            self.mol = Molecule(xyzfile, charge, spinmult, name = name, residue_name=resname, folder = self.folder)
            self.charge_method = charge_method

            self.bcc_pipeline = [
                AntechamberDocker("bcc", "mol2", workfolder = self.folder),
                ParmchkDocker("frcmod", workfolder = self.folder),
                TleapDocker(workfolder = self.folder)
            ]

            self.resp_pipeline = [] # 还没整

    def build(self, **kwargs):
        for docker in self.bcc_pipeline:
            docker:GeneralDocker
            docker.run(self.mol, **kwargs)

class solventBoxBuilder(object):
    r"""
    Solvated molecule in specified solvent.
    
    Parameters
    ----------
    solvent : str, Optional, default: 'water'
        Currently implemented solvents are: 'water', 'methanol', 'chloroform', 'nma', 'acetonitrile'
    slu_netcharge: int, Optional, default 0
        Charge of solute, the solvent box will be neutralized with Cl- and Na+ ions
    cube_size: float, Optional, default: 54
        Size of MM solvent box
    charge_method: str, Optional, default: "resp"
        Use 'resp' (quantum mechanical calculation needed) or 'bcc' to estimate partial charges
    slu_spinmult: int, Optional, default: 1
        Spinmultiplicity of solute
    outputFile: str, Optional, default='water_solvated'
        Filename-prefix for outputfiles
    srun_use: bool, Optional, default='False
        Run all commands with a srun prefix
    Returns
    -------
    None
        To run solvation, call build function.
    """
    def __init__(self, 
                 xyzfile:str, slu_netcharge=0, slu_spinmult=1, charge_method="resp", slu_count = 1,
                 solvent = "water", solvent_frcmod = "", solvent_off = "", solvent_box_name = "SLVBOX",
                 slv_generate = False, slv_xyz = "", slv_count = 210*8,
                 cube_size = 54, closeness = 0.8, folder = WORKING_DIR, outputFile = "",
                 **kwargs):
        
        self.kwargs = kwargs
        self.folder = folder

        self.solute = Molecule(xyzfile, slu_netcharge, slu_spinmult, folder = self.folder, residue_name="SLU")
        self.solute.number = slu_count

        if not outputFile:
            outputFile = solvent + "_solvated"

        self.solvent = self.get_solvent(solvent, slv_xyz, solvent_frcmod, solvent_off, slv_generate, slv_count, solvent_box_name)
        self.system = SolvatedSystem(outputFile, solute = self.solute, solvent=self.solvent,
                                     cubesize=cube_size, closeness=closeness, solute_number=slu_count, solvent_number=slv_count,
                                     folder = self.folder)
        self.system.set_closeness(closeness=closeness)
        self.solute_bcc_pipeline = [
            AntechamberDocker("bcc", "mol2", workfolder = self.folder),
            ParmchkDocker("frcmod", workfolder = self.folder),
            TleapDocker(workfolder = self.folder)
        ]
        self.solvent_pipeline = [
            AntechamberDocker("bcc", "mol2", workfolder = self.folder),
            ParmchkDocker("frcmod", workfolder = self.folder),
            TleapDocker(workfolder = self.folder)
        ]
        self.prebuilt_solvation = [
            TleapDocker(workfolder = self.folder)
        ]
        self.custom_solvation = [
            PackmolDocker(workfolder = self.folder),
            TleapDocker(workfolder = self.folder)
        ]
    
    def get_solvent(self, solvent:str, slv_xyz:str = "", solvent_frcmod:str = "", solvent_off:str = "", slv_generate:bool = False, slv_count:int = 210*8, solvent_box_name:str = "SLVBOX"):
        if solvent in AMBER_SOLVENT_DICT:
            # amber solvents
            self_solvent = AMBER_SOLVENT_DICT[solvent]
        elif solvent in custom_solv_dict:
            # solvent data prepared by autosolvate
            solvPrefix = custom_solv_dict[solvent]
            solvent_frcmod_path = pkg_resources.resource_filename('autosolvate', 
                os.path.join('data',solvPrefix,solvPrefix+".frcmod"))
            solvent_prep_path = pkg_resources.resource_filename('autosolvate', 
                os.path.join('data',solvPrefix,solvPrefix+".prep"))
            solvent_pdb_path = pkg_resources.resource_filename('autosolvate', 
                os.path.join('data',solvPrefix,solvPrefix+".pdb"))
            self_solvent = Molecule(solvent_pdb_path, 0, 1, solvent, residue_name = custom_solv_residue_name[solvent], folder = self.folder)
            self_solvent.frcmod = solvent_frcmod_path
            self_solvent.prep   = solvent_prep_path
            self_solvent.number = slv_count
        elif os.path.exists(solvent_frcmod) and os.path.exists(solvent_off):
            # using prebuilt solvent box
            self_solvent = SolventBox(solvent_off, solvent_frcmod, name = solvent, folder = self.folder, box_name=solvent_box_name)
        elif os.path.exists(slv_xyz) and slv_generate == True:
            # generate solvent box
            self_solvent = Molecule(slv_xyz, folder = self.folder)
            self_solvent.number = slv_count
        else:
            raise ValueError("Solvent not found")
        return self_solvent

    def build(self):
        for docker in self.solute_bcc_pipeline:
            docker:GeneralDocker
            docker.run(self.solute)
        if isinstance(self.solvent, Molecule):
            for docker in self.solvent_pipeline:
                docker.run(self.solvent)
        if isinstance(self.solvent, SolventBox):
            self.prebuilt_solvation[0].run(self.system)
        elif isinstance(self.solvent, Molecule):
            self.custom_solvation[0].run(self.system)
            self.custom_solvation[1].run(self.system)

def startboxgen(argumentList):
    r"""
    Wrap function that parses command line options for autosolvate boxgen,
    adds solvent box to a given solute,
    and generates related force field parameters.
    
    Parameters
    ----------
    argumentList: list
       The list contains the command line options to specify solute, solvent, and other options
       related to structure and force field parameter generation.

       Command line option definitions
         -m, --main  solute xyz file
         -s, --solvent  name of solvent (water, methanol, chloroform, nma)
         -o, --output  prefix of the output file names
         -c, --charge  formal charge of solute
         -u, --spinmultiplicity  spin multiplicity of solute
         -g, --chargemethod  name of charge fitting method (bcc, resp)
         -b, --cubesize  size of solvent cube in angstroms
         -r, --srunuse  option to run inside a slurm job
         -e, --gaussianexe  name of the Gaussian quantum chemistry package executable used to generate electrostatic potential needed for RESP charge fitting
         -d, --gaussiandir  path to the Gaussian package
         -a, --amberhome  path to the AMBER molecular dynamics package root directory. Definition of the environment variable $AMBERHOME
         -t, --closeness  Solute-solvent closeness setting, for acetonitrile tolerance parameter in packmol in Å, for water, methanol, nma, chloroform the scaling factor in tleap, setting to 'automated' will automatically set this parameter based on solvent.
         -l, --solventoff  path to the custom solvent .off library file. Required if the user want to use some custom solvent other than the 5 solvents contained in AutoSolvate (TIP3P water, methanol, NMA, chloroform, MeCN)
         -p, --solventfrcmod  path to the custom solvent .frcmod file. Required if the user wants to use some custom solvent other than the 5 solvents contained in AutoSolvate.
         -h, --help  short usage description

    Returns
    -------
    None
        Generates the structure files and save as ```.pdb```. Generates the MD parameter-topology and coordinates files and saves as ```.prmtop``` and ```.inpcrd```
    """
    #print(argumentList)
    options = "hm:s:o:c:b:g:u:re:d:a:t:l:p:"
    long_options = ["help", "main", "solvent", "output", "charge", "cubesize", "chargemethod", "spinmultiplicity", "srunuse","gaussianexe", "gaussiandir", "amberhome", "closeness","solventoff","solventfrcmod"]
    arguments, values = getopt.getopt(argumentList, options, long_options)
    solutexyz=""
    solvent='water'
    slu_netcharge=0
    cube_size=54
    charge_method="bcc"
    slu_spinmult=1
    outputFile=""
    srun_use=False
    amberhome=None
    gaussianexe=None
    gaussiandir=None
    closeness=0.8
    solvent_off=""
    solvent_frcmod=""
    #print(arguments)
    #print(values)
    for currentArgument, currentValue in arguments:
        if  currentArgument in ("-h", "--help"):
            print('Usage: autosolvate boxgen [OPTIONS]')
            print('  -m, --main                 solute xyz file')
            print('  -s, --solvent              name of solvent')
            print('  -o, --output               prefix of the output file names')
            print('  -c, --charge               formal charge of solute')
            print('  -u, --spinmultiplicity     spin multiplicity of solute')
            print('  -g, --chargemethod         name of charge fitting method (bcc, resp)')
            print('  -b, --cubesize             size of solvent cube in angstroms')
            print('  -r, --srunuse              option to run inside a slurm job')
            print('  -e, --gaussianexe          name of the Gaussian quantum chemistry package executable')
            print('  -d, --gaussiandir          path to the Gaussian package')
            print('  -a, --amberhome            path to the AMBER molecular dynamics package root directory')
            print('  -t, --closeness            Solute-solvent closeness setting')
            print('  -l, --solventoff           path to the custom solvent .off library file')
            print('  -p, --solventfrcmod        path to the custom solvent .frcmod file')
            print('  -h, --help                 short usage description')
            exit()
        elif currentArgument in ("-m", "--main"):
            print ("Main/solutexyz", currentValue)
            solutexyz=str(currentValue)     
        elif currentArgument in ("-s", "--solvent"):
            print ("Solvent:", currentValue)
            solvent=str(currentValue)
        elif currentArgument in ("-o", "--output"):
            print ("Output:", currentValue)
            outputFile=str(currentValue)
        elif currentArgument in ("-c", "--charge"):
            print ("Charge:", currentValue)
            slu_netcharge=int(currentValue)
        elif currentArgument in ("-b", "--cubesize"):
            print ("Cubesize:", currentValue)
            cube_size=float(currentValue)
        elif currentArgument in ("-g", "--chargemethod"):
            print ("Chargemethod:", currentValue)
            charge_method=str(currentValue)
        elif currentArgument in ("-u", "--spinmultiplicity"):
            print ("Spinmultiplicity:", currentValue)
            slu_spinmult=int(currentValue)
        elif currentArgument in ("-r", "--srunuse"):
            print("usign srun")
            srun_use=True
        elif currentArgument in ("-e","--gaussianexe"):
            print("Gaussian executable name:", currentValue)
            gaussianexe = currentValue
        elif currentArgument in ("-d","--gaussiandir"):
            print("Gaussian package directory:", currentValue)
            gaussiandir = currentValue
        elif currentArgument in ("-a","--amberhome"):
            print("Amber home directory:", currentValue)
            amberhome = currentValue
        elif currentArgument in ("-t", "--closeness"):
            print("Solute-Solvente closeness parameter", currentValue)
            closeness = currentValue
        elif currentArgument in ("-l", "--solventoff"):
            print("Custom solvent .off library path:", currentValue)
            solvent_off = currentValue
        elif currentArgument in ("-p", "--solventfrcmod"):
            print("Custom solvent .frcmmod file path:", currentValue)
            solvent_frcmod = currentValue

    if solutexyz == "":
        print("Error! Solute xyzfile must be provided!\nExiting...")
        exit()
    elif not os.path.exists(solutexyz):
        print("Error! Solute xyzfile path ", solutexyz, " does not exist!\nExiting...")
        exit()

    try:
        _, ext = os.path.splitext(solutexyz)
        pybel.readfile(ext[1:], solutexyz).__next__()
    except:
        print("Error! Solute structure file format issue!")
        print(solutexyz," cannot be opened with openbabel.\n Exiting...")
        exit()

    global WORKING_DIR
    WORKING_DIR = os.getcwd()
    builder = solventBoxBuilder(solutexyz, solvent=solvent, slu_netcharge=slu_netcharge, cube_size=cube_size, charge_method=charge_method, 
                                slu_spinmult=slu_spinmult, outputFile=outputFile, srun_use=srun_use, 
                                gaussianexe=gaussianexe, gaussiandir=gaussiandir, amberhome=amberhome, 
                                closeness=closeness, solvent_off=solvent_off, solvent_frcmod=solvent_frcmod, folder = WORKING_DIR)
    builder.build()

if __name__ == '__main__':
    argumentList = sys.argv[1:]
    startboxgen(argumentList)
