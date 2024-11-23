#Base
Dimension = int('3')
Composition = 'Na1H9V6O20'
Num_Atom = [int('36'), int('36')]
Space_Group = [[1, 230]]

#2-Dimension settings
Vacuum_Space = 15
Thickness = 1
Z_Layers = 3

#3-Dimension settings
Pressure = 0

#Model
Use_Pretrain_Model = [True if 'NOPRE' == 'PRE' else False][0]
Update_ML_Model = True

#Recycling
Num_Recycle = 1
Num_ML_Iter = [1 for _ in range(Num_Recycle)]
Energy_Convergence = -1
Use_Succeed = True

#Sampling
Use_ML_Clustering = [True if 'CLUS' == 'CLUS' else False][0]
Min_Dis_Constraint = True
Init_Strus_per_Node = 40
Num_Sample_Limit = 50000
Sampling_Time_Limit = 1200
Rand_Latt_Ratio = 0.8
#SpaceGroup-based
General_Search = True
Latt_per_Node = 100
SG_per_Latt = 20
#Cluster-based
Cluster_Search = False
Clus_per_Node = 10
Cluster_Num_Ratio = 0.8
Cluster_Weight = [1]
#Tempelate-based
Template_Search = False
Disturb_Seeds = False
Temp_per_Node = 20
Num_Fixed_Temp = 16

#Searching
SA_Path_per_Node = 40
Restart_Times = 5
Exploration_Ratio = 0.8
Exploitation_Num = 10
SA_Steps = 75
SA_Decay = .97
SA_Path_Ratio = 0.2

#Sample select
Num_Clusters_per_Node = 20
SA_Energy_Ratio = 0.5

#Energy calculate
Energy_Method = 'VASP'
Num_Opt_Low_per_Node = 5
Num_Opt_High_per_Node = 2
Num_Opt_Low_per_Job = 3
Num_Opt_High_per_Job = 2
Refine_Stru = False
Scf_Time_Limit = 6000
Opt_Time_Limit = 6000
#VASP
Use_VASP_Scf = True
Use_VASP_Opt = True
VASP_Opt_Symm = True
#LAMMPS
Use_LAMMPS_Scf = True
Use_LAMMPS_Opt = True

#Energy cutoff eV/atom
E_Range = [-10, 0]