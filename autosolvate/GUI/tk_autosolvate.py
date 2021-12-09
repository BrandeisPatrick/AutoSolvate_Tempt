import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
from tkinter.ttk import *
from PIL import ImageTk, Image
import nglview
import glob
import os
import subprocess
import shutil
import imolecule
import pkg_resources

this_dir, this_filename = os.path.split(__file__)

def mol_with_atom_index(mol):
    atoms = mol.GetNumAtoms()
    for idx in range(atoms):
        mol.GetAtomWithIdx(idx).SetProp('molAtomMapNumber', str(mol.GetAtomWithIdx(idx).GetIdx()))
    return mol


def view_w_ngl(xyz):
    shutil.copy(xyz, '_autosolvate_input.xyz')
    SCRIPT_PATH = os.path.join(this_dir, "nb_scripts", "view_autosolvate_input.ipynb")
    shutil.copy(SCRIPT_PATH, './')

    subprocess.call('jupyter notebook view_autosolvate_input.ipynb &', shell=True)


def view_w_imol(xyz):
    imolecule.draw(open(xyz).read(), format='xyz')


def cleanUp():
    if os.path.exists('_autosolvate_input.xyz'):
        os.remove('_autosolvate_input.xyz')
    if os.path.exists('view_autosolvate_input.ipynb'):
        os.remove('view_autosolvate_input.ipynb')


colwidth = [25, 25, 7, 7, 50]

class baseGUI():
    def __init__(self,master):
        self.master = master
        self.padx = 5
        self.irow = 0

    def display_logo(self):
        path = pkg_resources.resource_filename('autosolvate', 'GUI/images/logo.png')

        #Creates a Tkinter-compatible photo image, which can be used everywhere Tkinter expects an image object. Scale the image to fix into the current window
        self.master.update()
        win_width = self.master.winfo_width() - self.padx*2
        img = Image.open(path)
        zoom = win_width/img.size[0]
        #multiple image size by zoom
        pixels_x, pixels_y = tuple([int(zoom * x)  for x in img.size])
        scaled_img = ImageTk.PhotoImage(img.resize((pixels_x, pixels_y)))

        #The Label widget is a standard Tkinter widget used to display a text or image on the screen.
        self.logo = Label(self.master, image = scaled_img)
        self.logo.image = scaled_img
        self.logo.grid(column=0, row=self.irow, columnspan=6, sticky=W+E, padx=self.padx)
        self.irow += 1



class boxgenGUI(baseGUI):
    def __init__(self,master):
        super().__init__(master)
        self.master.title("Automated solvated box structure and MD parameter generator")
        self.master.geometry('820x600')
        self.cube_size_max = 100
        
        self.display_logo()

        ### Add a solute path
        self.lbl00 = Label(self.master, text="Enter solute xyz file path", width=colwidth[0])
        self.lbl00.grid(column=0, row=self.irow)
        
        self.txt01 = Entry(self.master, width=colwidth[3])
        self.txt01.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        self.xyzfile = StringVar()
        self.txt_torsion = []
        
        def set_xyz():
            my_filetypes = [('xyz files', '.xyz')]
            mypath = self.txt01.get()
            if mypath !="" and os.path.exists(mypath):
                    self.xyzfile.set(self.txt01.get())
            else:
                answer = filedialog.askopenfilename(parent=self.master,
                                    initialdir=os.getcwd(),
                                    title="No file path entered.\n Please select a file:",
                                    filetypes=my_filetypes)
                self.xyzfile.set(answer)
                self.txt01.delete(0,END)
                self.txt01.insert(0,answer)
            res = self.xyzfile.get()
            self.lbl11.configure(text=res)
        
        
        self.btn02 = Button(self.master, text="Set solute xyz", command=set_xyz, width=colwidth[3])
        self.btn02.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        
        self.irow += 1

        ### Display solute path
        self.lbl10 = Label(self.master, text="Current solute xyz file path:", width=colwidth[0])
        self.lbl10.grid(column=0, row=self.irow)
        
        self.lbl11 = Label(self.master, text="Waiting...", width=colwidth[4])
        self.lbl11.grid(column=1, row=self.irow, columnspan=6, sticky=W+E)
        self.irow += 1
        
        ### Visualize the solute molecule
        self.lbl20 = Label(self.master, text="Select visualization method", width=colwidth[0])
        self.lbl20.grid(column=0, row=self.irow)
        
        # Adding combobox drop down list 
        self.n = StringVar()
        self.view_chosen = Combobox(self.master, textvariable=self.n, width=colwidth[3])
        self.view_chosen['values'] = ('imolecule',
                                     'nglview',)
        
        self.view_chosen.current(0)
        self.view_chosen.grid(column=1, row=self.irow,columnspan=3,sticky=W+E)
        
        
        def view_xyz():
            if self.view_chosen.get() == 'imolecule':
                view_w_imol(self.xyzfile.get())
            else:
                view_w_ngl(self.xyzfile.get())
        
        
        self.btn22 = Button(self.master, text="View", command=view_xyz, width=colwidth[3])
        self.btn22.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1
        
        ### Verbose output or not
        self.verbose = BooleanVar()
        
        self.lbl04 = Label(self.master, text="Verbose output", width=colwidth[0])
        self.lbl04.grid(column=0, row=self.irow)
        
        self.rad14 = Radiobutton(self.master, text='Yes', value=True, variable=self.verbose, width=colwidth[3])
        self.rad14.grid(column=1, row=self.irow)
        
        self.rad24 = Radiobutton(self.master, text='No', value=False, variable=self.verbose)
        self.rad24.grid(column=2, row=self.irow)
        
        self.verbose.set(False)
        self.irow += 1
        
        ### Adding combobox drop down list for selecting solvent 
        self.lbl050 = Label(self.master, text="Select solvent", width=colwidth[0])
        self.lbl050.grid(column=0, row=self.irow)
        self.n5 = StringVar()
        self.solvent = Combobox(self.master, textvariable=self.n5, width=colwidth[3])
        self.solvent['values'] = ('water',
                                     'methanol',
                                     'chloroform',
                                     'nma',
                                     'acetonitrile')
        
        self.solvent.current(0)
        self.solvent.grid(column=1, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1
        
        ### Adding combobox drop down list for selecting charge method
        self.lbl060 = Label(self.master, text="Select charge method for\n force field fitting", width=colwidth[0])
        self.lbl060.grid(column=0, row=self.irow)
        self.n6 = StringVar()
        self.charge_method = Combobox(self.master, textvariable=self.n6, width=colwidth[3])
        self.charge_method['values'] = ('bcc',
                                     'resp')
        
        self.charge_method.current(0)
        self.charge_method.grid(column=1, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1

        ### Output File path
        self.lbl08 = Label(self.master, text="Output directory", width=colwidth[0])
        self.lbl08.grid(column=0, row=self.irow)
        
        self.txt18 = Entry(self.master)
        self.txt18.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.output_path = StringVar()
        
        def set_output_path():
            mypath = self.txt18.get()
            if mypath !="" and os.path.exists(mypath):
                    self.output_path.set(self.txt18.get())
            else:
                answer = filedialog.askdirectory(title="No file path entered.\n Please select a path:")
                self.output_path.set(answer)
                self.txt18.delete(0,END)
                self.txt18.insert(0,answer)
            res = self.output_path.get()
        
        self.btn28 = Button(self.master, text="Set", command=set_output_path, width=colwidth[3])
        self.btn28.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1
        
        ### Terachem input file template
        self.lbl09 = Label(self.master, text="Output file name prefix", width=colwidth[0])
        self.lbl09.grid(column=0, row=self.irow)
        
        
        self.txt19 = Entry(self.master)
        self.txt19.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.output_prefix = StringVar()
        
        def set_prefix():
            if self.txt19.get()!= "":
                    self.output_prefix.set(self.txt19.get())
            else:
                default_output_prefix = self.solvent.get()+"_solvated"
                self.output_prefix.set(default_output_prefix)
                self.txt19.insert(0,default_output_prefix)
        
        self.btn29 = Button(self.master, text="Set", command=set_prefix, width=colwidth[3])
        self.btn29.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1

        ### Solute charge 
        self.lbl010 = Label(self.master, text="solute charge", width=colwidth[0])
        self.lbl010.grid(column=0, row=self.irow)
        
        
        self.txt110 = Entry(self.master)
        self.txt110.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.charge = IntVar()
        
        def set_charge():
            answer = 0
            try: 
                answer = int(self.txt110.get())
            except ValueError:
                answer = simpledialog.askinteger(parent=self.master,
                                                 title="Dialog",
                                                 prompt="Charge must be an integer! Please re-enter.") 
                self.txt110.delete(0,END)
                self.txt110.insert(0,answer)
            self.charge.set(answer)
            res = self.charge.get()
        
        self.btn210 = Button(self.master, text="Set", command=set_charge, width=colwidth[3])
        self.btn210.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1

        ### Solute spin multiplicity
        self.lbl011 = Label(self.master, text="solute spin multiplicity", width=colwidth[0])
        self.lbl011.grid(column=0, row=self.irow)
        
        
        self.txt111 = Entry(self.master)
        self.txt111.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.spin_multiplicity = IntVar()
        
        def set_spin_multiplicity():
            answer = 0
            try: 
                answer = int(self.txt111.get())
            except ValueError:
                answer = simpledialog.askinteger(parent=self.master,
                                     title="Dialog",
                                     prompt="Spin multiplicity must be a positive integer! Please re-enter.")
                self.txt111.delete(0,END)
                self.txt111.insert(0,answer)
            self.spin_multiplicity.set(answer)
            res = self.spin_multiplicity.get()
        
        self.btn211 = Button(self.master, text="Set", command=set_spin_multiplicity, width=colwidth[3])
        self.btn211.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)

        self.irow += 1
        
        ### Solvent cube size
        self.lbl012 = Label(self.master, text="Solvent cube size (Angstrom)", width=colwidth[0])
        self.lbl012.grid(column=0, row=self.irow)
        
        
        self.txt112 = Entry(self.master)
        self.txt112.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.cube_size = DoubleVar()
        
        def set_cubesize():
            answer = 0
            try: 
                answer = int(self.txt112.get())
            except ValueError:
                answer = simpledialog.askfloat(parent=self.master,
                                               title="Dialog",
                                               prompt="Solvent cube size must be a float! Please re-enter.")
                self.txt112.delete(0,END)
                self.txt112.insert(0,answer)
            self.cube_size.set(answer)
            res = self.cube_size.get()
        
        self.btn212 = Button(self.master, text="Set", command=set_cubesize, width=colwidth[3])
        self.btn212.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1
        
        ### AMBERHOME path
        self.lbl013 = Label(self.master, text="AMBERHOME directory", width=colwidth[0])
        self.lbl013.grid(column=0, row=self.irow)
        
        self.txt113 = Entry(self.master)
        self.txt113.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.amberhome = StringVar()
        
        def set_amberhome():
            mypath = self.txt113.get()
            if mypath !="" and os.path.exists(mypath):
                    self.amberhome.set(self.txt113.get())
            else:
                answer = filedialog.askdirectory(title="No file path entered.\n Please select a path:")
                self.amberhome.set(answer)
                self.txt113.delete(0,END)
                self.txt113.insert(0,answer)
            res = self.amberhome.get()
        
        self.btn213 = Button(self.master, text="Set", command=set_amberhome, width=colwidth[3])
        self.btn213.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1

        ### Gaussian EXE
        self.lbl014 = Label(self.master, text="Select gaussian exe", width=colwidth[0])
        self.lbl014.grid(column=0, row=self.irow)
        self.n6 = StringVar()
        self.gaussianexe = Combobox(self.master, textvariable=self.n6, width=colwidth[3])
        self.gaussianexe['values'] = ('None',
                                      'g09',
                                      'g16')
        
        self.gaussianexe.current(0)
        self.gaussianexe.grid(column=1, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1

        ### Gaussian path
        self.lbl015 = Label(self.master, text="Gaussian EXE directory", width=colwidth[0])
        self.lbl015.grid(column=0, row=self.irow)
        
        self.txt115 = Entry(self.master)
        self.txt115.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        
        self.gaussiandir = StringVar()
        
        def set_gaussiandir():
            mypath = self.txt115.get()
            if mypath !="" and os.path.exists(mypath):
                    self.gaussiandir.set(self.txt115.get())
            else:
                answer = filedialog.askdirectory(title="No file path entered.\n Please select a path:")
                self.gaussiandir.set(answer)
                self.txt115.delete(0,END)
                self.txt115.insert(0,answer)
            res = self.gaussiandir.get()
        
        self.btn215 = Button(self.master, text="Set", command=set_gaussiandir, width=colwidth[3])
        self.btn215.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        self.irow += 1

        ### Sanity check to make sure that all required buttons are set
        def GUI_input_sanity_check():
            boxgen_error =0 
            if self.xyzfile.get() =="":
                  print("Solute molecule xyz file must be provided!")
                  boxgen_error = 1
            else:
                  print("Solute molecule xyz file: ", self.xyzfile.get())
            # Check charge method based on spin multiplicity
            if self.spin_multiplicity.get() > 1 and  self.charge_method_chose.get()!='resp':
                print("{:s} charge method cannot ".format(self.charge_method_chose.get()) +
                    + "handle open-shell system with spin multiplicity"
                    + "{:d}".format(self.spin_multiplicity.get()))
                boxgen_error = 2
            if self.cube_size.get() < 0 or self.cube_size.get() > self.cube_size_max :
                print("Solvent box size (Angstrom) must be a positive"
                    + "number no bigger than {:d}".format(self.cube_size_max))
                boxgen_error = 3 
            # TODO: add check for number of electrons and spin multiplicity
            if self.amberhome.get()=="":
                print("WARNING: AMBERHOME not provided from GUI.")
            if self.charge_method_chose.get()=='resp':
                if self.gaussianexe.get()=='None':
                    print("WARNING: Gaussian exe file name not specified for RESP charge fitting.")
                    print("WARNING: Will use default value with the risk to fail later.")
                if self.gaussiandir.get()=="":
                    print("WARNING: Gaussian exe directory not specified for RESP charge fitting.")
                    print("WARNING: Will use default value with the risk to fail later.")
            
            return boxgen_error

        def write_boxgen_input():
            cmd = "python " + os.path.join(this_dir,"../autosolvate.py")
        
            if self.xyzfile.get() != "":
               cmd += " -m " + self.xyzfile.get()
            if self.solvent.get() != "":
                cmd += " -s " + self.solvent.get()
            if self.verbose.get() == 1:
                cmd += " -v "
            if self.charge_method.get() != "":
                cmd += " -g " + self.charge_method.get()
            if self.charge.get() != "":
                cmd += " -c {:d}".format(self.charge.get())
            if self.spin_multiplicity.get() != "":
                cmd += " -u {:d}".format(self.spin_multiplicity.get())
            if self.cube_size.get() != "":
                cmd += " -b {:f}".format(self.cube_size.get())
            if self.output_prefix !="":
                cmd += " -o {:s}".format(self.output_prefix.get())
            if self.gaussianexe !="None":
                cmd += " -e {:s}".format(self.gaussianexe.get())
            if self.gaussiandir !="":
                cmd += " -d {:s}".format(self.gaussiandir.get())
            if self.amberhome !="":
                cmd += " -a {:s}".format(self.amberhome.get())
            return cmd
        
        
        # Execute  python command to run autosolvate
        def execute():
            boxgen_error = GUI_input_sanity_check()
            if boxgen_error == 0:
                cmd = write_boxgen_input()
                res = "Congratulations! AutoSolvate command generated: \n" + cmd
                messagebox.showinfo(title="Confirmation", message=res)
                question = "Do you want to continue to generate the "\
                         + "solvent box structure and force field parameters?"
                answer = messagebox.askyesno(title="Confirmation", message=question)
                if answer == True:
                    subprocess.call(cmd, shell=True)
        
            else:
                res = "Error found in input.\n"
                if boxgen_error == 1:
                    res += "Please enter xyz file path"
                elif boxgen_error == 2:
                    res += "Please modify charge method. Only gaussian RESP charge\n"\
                          + "fitting can handle open-shell system with spin multiplicity > 1"
                elif boxgen_error == 3:
                    res += "Please re-define solvent box size. Solvent box size (Angstrom)"\
                         + "must be a positive number no bigger than {:d}".format(self.cube_size_max)
                messagebox.showerror(message=res)
        
        # Generate solvated box and MD parameter files
        self.btn132 = Button(self.master, text="Generate Solvent box and MD parameters! ", command=execute)
        self.btn132.grid(column=0, row=self.irow, columnspan=3, sticky=W+E, padx=self.padx, pady=5)
        self.irow += 1

### START MD automation window ###
class mdGUI(baseGUI):
    def __init__(self, master):
        super().__init__(master)
        self.master.title("MD simulation automation")
        self.master.geometry('820x600')
        self.display_logo()

        ### Enter .parmtop and .inpcrd filename prefix 
        self.lbl00 = Label(self.master, text="Enter file name prefix for existing .inpcrd and .parmtop files", width=colwidth[0])
        self.lbl00.grid(column=0, row=self.irow)
        
        self.txt01 = Entry(self.master, width=colwidth[3])
        self.txt01.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        self.prefix = StringVar()
        
        def set_prefix():
            mypath = self.txt01.get()
            inpcrd = "{}.inpcrd".format(mypath)
            prmtop = "{}.prmtop".format(mypath)
            if mypath !="" and os.path.exists(inpcrd) and os.path.exists(prmtop):
                    self.prefix.set(self.txt01.get())
            else:
                msg = "Invalid prefix provided!\n"
                answer = ""
                answerValid = False
                if mypath !="":
                    if not os.path.exists(inpcrd):
                        msg+= "File " + inpcrd + " does not exist!\n"
                    if not os.path.exists(prmtop):
                        msg+= "File " + prmtop + " does not exist!\n"
                    msg+= "Please re-try\n"
                else:
                    msg = "Empty file prefix. Please enter.\n"
                while (not answerValid):
                    answer = filedialog.askString(parent=self.master,
                                    title=msg)
                    inpcrd = "{}.inpcrd".format(mypath)
                    prmtop = "{}.prmtop".format(mypath)
                    msg = "Invalid prefix provided!\n"
                    answerValid = True
                    if not os.path.exists(inpcrd):
                        msg+= "File " + inpcrd + " does not exist!\n"
                        answerValid = False
                    if not os.path.exists(prmtop):
                        msg+= "File " + prmtop + " does not exist!\n"
                        answerValid = False
                    msg+= "Please re-try\n"

                self.prefix.set(answer)
                self.txt01.delete(0,END)
                self.txt01.insert(0,answer)
        
        self.btn02 = Button(self.master, text="Set file prefix", command=set_prefix, width=colwidth[3])
        self.btn02.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        
        self.irow += 1

        ### set Temperature
        self.lblTemp = Label(self.master, text="Enter Temperature (K)", width=colwidth[0])
        self.lblTemp.grid(column=0, row=self.irow)
        
        self.txtTemp = Entry(self.master, width=colwidth[3])
        self.txtTemp.grid(column=1, row=self.irow, columnspan=3, sticky=W+E)
        self.Temp = DoubleVar()
        
        def set_Temp():
            answer = 298
            try: 
                answer = int(self.txtTemp.get())
            except ValueError:
                anserValid = False
                while (not answerValid):
                    msg = "Temperature must be a positive float!\n"
                    msg += "Please re-enter.\n"
                    answer = simpledialog.askfloat(parent=self.master,
                                               title="Dialog",
                                               prompt=msg)
                    answerValid = True
                    if not isinstance(answer,float):
                        answerValid = False
                    elif answer <= 0 :
                        answerValid = False

                self.Temp.set(answer)
                self.txtTemp.delete(0,END)
                self.txtTemp.insert(0,answer)
        
        self.btnTemp = Button(self.master, text="Set", command=set_prefix, width=colwidth[3])
        self.btnTemp.grid(column=4, row=self.irow,columnspan=3,sticky=W+E)
        
        self.irow += 1


### START MD automation window ###

### START cluster extraction window ###
class clusterGUI(baseGUI):
    def __init__(self,master):
        super().__init__(master)
        master.title("Microsolvated cluster extraction")
        master.geometry('820x800')
        self.display_logo()
     #TODO: link to scripts that post process MD trajectories

### END Cluster extraction window ###

## The master GUI of AutoSolvate where we select what task to do ##
class autosolvateGUI(baseGUI):
    def __init__(self,master):
        super().__init__(master)
        self.master.title("Welcome to AutoSolvate!")
        self.master.geometry('360x180')

        # Display logo
        self.display_logo()

        ### select the task to do
        self.lbl00 = Label(master, text="Please select the task",width=20)
        self.lbl00.grid(column=0, row=self.irow,  sticky=W+E, padx=self.padx)
        self.lbl00.configure(anchor="center")
        self.irow += 1
        # Adding combobox drop down list 
        self.task = StringVar()
        self.task_chosen = Combobox(master, textvariable=self.task, width=30)
        self.task_chosen['values'] = ('Solvated box and MD parameter generation',
                                      'MD automation',
                                     'Microsolvated cluster extraction') 
        self.task_chosen.current(0)
        self.task_chosen.grid(column=0, row=self.irow,  sticky=W+E, padx=self.padx)
        self.irow += 1

        # Create new window to do the task
        def create_task_window():
            if self.task_chosen.get() == 'Solvated box and MD parameter generation':
                self.master2 = Toplevel(self.master)
                my_gui = boxgenGUI(self.master2)
            elif self.task_chosen.get() == 'MD automation':
                self.master3 = Toplevel(self.master)
                my_gui = mdGUI(self.master3)
            else:
                self.master4 = Toplevel(self.master)
                my_gui = clusterGUI(self.master4)
        
        self.btn02 = Button(master, text="Go!", command=create_task_window, width=20)
        self.btn02.grid(column=0, row=self.irow,  sticky=W+E, padx=self.padx)
        self.irow += 1

# This part does not need to be modified
if __name__ == '__main__':
    window = Tk()
    my_gui = autosolvateGUI(window)
    window.mainloop()

    cleanUp()
