#Server
Job_System = 'SLURM'
Job_Queue = 'CPU'
Host_Node = 'HOST_NODE'
CPU_Nodes = 'CPU_NODES'
GPU_Nodes = 'GPU_NODES'
Num_GPUs = 'GPU_NUM'

#Environment
SCCOP_Env = 'source /home/cli20/anaconda3/bin/activate sccop'
# SCCOP_Env = 'source /global/homes/c/chuannan/anaconda3/bin/activate sccop'
Sources = ''
Modules = f'''
           module load cpu/0.15.4
           module load intel/19.1.1.217
           module load intel-mpi/2019.8.254
           module load intel-mkl/2018.1.163
           '''
Envs = ''
# SCCOP_Env = 'source /public1/home/sch9368/anaconda3/bin/activate sccop'
# Sources = ''
# Modules = f'''
#            module purge
#            module load mpi/intel/20.0.4
#            '''
# Envs = f'''
#         export PATH=/public1/home/sch9368/bin/new/lammps-2Aug2023/src:$PATH
#         export LD_LIBRARY_PATH=/public1/soft/intel/2020/compilers_and_libraries_2020.4.304/linux/mkl/lib/intel64_lin:$LD_LIBRARY_PATH
#         '''
# SCCOP_Env = 'source /home/phys/qihangyu/anaconda3/bin/activate sccop'
# Sources = 'source /etc/profile'
# Modules = 'module load vasp/6.3.2/oneapi_latest'
# Envs = ''
# SCCOP_Env = ''
# Sources = ''
# Modules = ''
# Envs = ''

#Scf and Opt settings
# VASP_scf = '/opt/intel/impi/4.0.3.008/intel64/bin/mpirun -np 4 vasp'
# VASP_opt = '/opt/intel/impi/4.0.3.008/intel64/bin/mpirun -np 48 vasp'
# VASP_scf = 'mpirun -np 4 vasp_std'
# VASP_opt = 'mpirun -np 64 vasp_std'
# LAMMPS_scf = 'lmp_mpi -in input.inp'
# LAMMPS_opt = 'mpirun -np 48 lmp_mpi -in input.inp'
LAMMPS_scf = 'lmp_intel_cpu_intelmpi -in input.inp'
LAMMPS_opt = 'mpirun -np 96 lmp_intel_cpu_intelmpi -in input.inp'
# VASP_opt = '/opt/openmpi-1.6.3/bin/mpirun -np 48 vasp_relax_ab'
# VASP_scf = 'mpirun -np 96 vasp_std'
# VASP_opt = 'mpirun -np 96 /public5/home/sch6940/bin/vasp_relax_ab'
# VASP_scf = 'mpirun -np 4 vasp_std'
# VASP_opt = 'mpirun -np 96 vasp_std'
VASP_scf = 'mpirun -np 8 /home/cli20/bin/vasp.5.4.4/bin/vasp_std'
VASP_opt_low = 'mpirun -np 24 /home/cli20/bin/vasp.5.4.4/bin/vasp_std'
VASP_opt_high = 'mpirun -np 64 /home/cli20/bin/vasp.5.4.4/bin/vasp_std'

#Save directory
SCCOP_Path = '/tmp/sccop'
Commun_Path = 'commun'
Save_Path = 'data/save'
Seed_Path = 'data/seeds'
Model_Path = 'data/gnn_model'
Search_Path = 'data/search'
Grid_Path = 'data/grid'
Json_Path = 'data/grid/json'
Buffer_Path = 'data/grid/buffer'
Recyc_Store_Path = 'data/grid/store'
SCCOP_Out_Path = 'data/poscar/SCCOP'
Optim_Strus_Path = 'data/poscar/optim_strus'
Init_Strus_Path = 'data/poscar/initial_strus'

#File
Log_File = 'data/log.sccop'
Time_File = 'data/time.dat'
Elements_File = 'data/elements.dat'
Atom_Init_File = 'data/atom_init.dat'
New_Atom_File = 'data/new_atom.json'
Cluster_Angle_File = 'data/cluster_angles.dat'
Bond_File = 'data/bond.json'
Pretrain_Path = 'data/pretrain'
Pretrain_Save = f'{Pretrain_Path}/store'
Pretrain_Model_2d = f'{Pretrain_Path}/models/model_2d.pth.tar'
Pretrain_Model_3d = f'{Pretrain_Path}/models/model_3d.pth.tar'

#VASP directory
POSCAR_Path = 'data/poscar' 
POTCAR_Path = 'libs/POTCAR/PBE'
VASP_Files_Path = 'libs/VASP_inputs'
VASP_Out_Path = 'data/vasp_out'
Optim_VASP_Path = f'{VASP_Out_Path}/optim_strus'

#LAMMPS directory
ForceField_Path = 'libs/ForceField'
LAMMPS_Files_Path = 'libs/LAMMPS_inputs'
LAMMPS_Out_Path = 'data/lammps_out'
Optim_LAMMPS_Path = f'{LAMMPS_Out_Path}/optim_strus'