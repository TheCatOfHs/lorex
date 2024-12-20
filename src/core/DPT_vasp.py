import os
import argparse


class VaspDPT():
    #vasp data process tool
    def get_POTCAR_files(self, out_path, potcar_path):
        '''read POSCAR and get POTCAR
        '''
        potcar_choose = {'H':'H', 
                'He':'He', 
                'Li':'Li_sv', 
                'B':'B', 
                'Be':'Be', 
                'C':'C', 
                'N':'N', 
                'O':'O', 
                'F':'F', 
                'Ne':'Ne', 
                'Na':'Na_pv', 
                'Mg':'Mg', 
                'Al':'Al', 
                'Si':'Si', 
                'P':'P', 
                'S':'S', 
                'Cl':'Cl', 
                'Ar':'Ar', 
                'K':'K_sv', 
                'Ca':'Ca_sv', 
                'Sc':'Sc_sv', 
                'Ti':'Ti_sv', 
                'V':'V_sv', 
                'Cr':'Cr_sv', 
                'Mn':'Mn_pv', 
                'Fe':'Fe', 
                'Co':'Co', 
                'Ni':'Ni', 
                'Cu':'Cu', 
                'Zn':'Zn', 
                'Ga':'Ga_d', 
                'Ge':'Ge_d', 
                'As':'As', 
                'Se':'Se', 
                'Br':'Br', 
                'Kr':'Kr', 
                'Rb':'Rb_sv', 
                'Sr':'Sr_sv', 
                'Y':'Y_sv', 
                'Zr':'Zr_sv', 
                'Nb':'Nb_sv', 
                'Mo':'Mo_sv', 
                'Tc':'Tc_pv', 
                'Ru':'Ru_pv', 
                'Rh':'Rh_pv', 
                'Pd':'Pd', 
                'Ag':'Ag', 
                'Cd':'Cd', 
                'In':'In_d', 
                'Sn':'Sn_d', 
                'Sb':'Sb', 
                'Te':'Te', 
                'I':'I', 
                'Xe':'Xe', 
                'Cs':'Cs_sv', 
                'Ba':'Ba_sv', 
                'La':'La', 
                'Ce':'Ce', 
                'Pr':'Pr_3', 
                'Nd':'Nd_3', 
                'Pm':'Pm_3', 
                'Sm':'Sm_3', 
                'Eu':'Eu_2', 
                'Gd':'Gd_3', 
                'Tb':'Tb_3', 
                'Dy':'Dy_3', 
                'Ho':'Ho_3', 
                'Er':'Er_3', 
                'Tm':'Tm_3', 
                'Yb':'Yb', 
                'Lu':'Lu', 
                'Hf':'Hf_pv', 
                'Ta':'Ta_pv', 
                'W':'W_sv', 
                'Re':'Re', 
                'Os':'Os', 
                'Ir':'Ir', 
                'Pt':'Pt', 
                'Au':'Au', 
                'Hg':'Hg', 
                'Tl':'Tl_d', 
                'Pb':'Pb_d', 
                'Bi':'Bi_d', 
                'Po':'Po_d', 
                'At':'At_d', 
                'Rn':'Rn', 
                'Fr':'Fr_sv', 
                'Ra':'Ra_sv', 
                'Ac':'Ac', 
                'Th':'Th', 
                'Pa':'Pa', 
                'U':'U', 
                'Np':'Np', 
                'Pu':'Pu', 
                'Am':'Am', 
                'Cm':'Cm', 
                'Bk':'Bk', 
                'Cf':'Cf', 
                'Es':'Es', 
                'Fm':'Fm', 
                'Md':'Md', 
                'No':'No', 
                'Lr':'Lr', 
                'Rf':'Rf', 
                'Db':'Db', 
                'Sg':'Sg', 
                'Bh':'Bh', 
                'Hs':'Hs', 
                'Mt':'Mt', 
                'Ds':'Ds', 
                'Rg':'Rg', 
                'Cn':'Cn'}
        #read POSCAR
        with open(f'{out_path}/POSCAR', 'r') as obj:
            poscar = obj.readlines()
        atoms = poscar[5].split()
        poscar_files = ' '.join(['{0}/{1}/POTCAR'.format(potcar_path, potcar_choose[atom]) for atom in atoms])
        os.system(f'cat {poscar_files} > {out_path}/POTCAR')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str)
    args = parser.parse_args()
    
    potcar_path = args.path
    vasp = VaspDPT()
    
    paths = [i for i in os.listdir() if i.startswith('calc')]
    for path in paths:
        vasp.get_POTCAR_files(path, potcar_path)