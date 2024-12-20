import os, sys
import time
import numpy as np

from pymatgen.core.structure import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

sys.path.append(f'{os.getcwd()}/src')
from core.log_print import *
from core.utils import ListRWTools, SSHTools, system_echo
from core.del_duplicates import DeleteDuplicates
from core.DPT_lammps import LammpsDPT


class ParallelSubLammps(ListRWTools, SSHTools, LammpsDPT):
    #submit lammps jobs
    def __init__(self, wait_time=0.1):
        SSHTools.__init__(self)
        self.wait_time = wait_time
    
    def sub_job(self, iteration):
        """
        calculate POSCARs and return energys
        
        POSCAR file notation: POSCAR-iteration-number-node
        e.g. POSCAR-001-136
        
        Parameters
        ----------
        iteration [int, 0d]: sccop iteration
        """
        poscars = os.listdir(f'{POSCAR_Path}/ml_{iteration:02.0f}')
        num_poscar = len(poscars)
        system_echo(f'Start LAMMPS Calculation --- itersions: '
                    f'{iteration}, number: {num_poscar}')
        #lammps calculation
        self.sub_lammps_job(poscars, iteration)
        #get energy of outputs
        self.get_energy(iteration)
    
    def sub_lammps_job(self, poscars, iteration):
        """
        submit lammps jobs to nodes

        Parameters
        ----------
        poscars [str, 1d]: name of poscars
        iteration [int, 0d]: sccop iteration
        """
        #make directory
        poscar_path = f'{POSCAR_Path}/ml_{iteration:02.0f}'
        out_path = f'{LAMMPS_Out_Path}/ml_{iteration:02.0f}'
        os.mkdir(out_path)
        #generate scf script
        self.get_scf_script(poscar_path)
        #send poscars to work nodes
        jobs = self.group_poscars(poscars)
        work_node_num = len(jobs)
        for job in jobs:
            self.send_zip_poscars(job, iteration)
        while not self.is_done(out_path, work_node_num):
            time.sleep(self.wait_time)
        self.remove_flag(out_path)
        #sub lammps job to work nodes
        for job in jobs:
            self.sub_job_with_ssh(job, iteration)
        #check finish of jobs
        while not self.is_done(out_path, work_node_num):
            time.sleep(self.wait_time)
        self.remove_flag(out_path)
    
    def send_zip_poscars(self, job, iteration):
        """
        send poscars to work nodes
        
        Parameters
        ----------
        job [str, 1d]: name of poscars in same node
        iteration [int, 0d]: sccop iteration
        """
        node = self.extract_node_name(job[0])
        poscar_str = ' '.join(job)
        local_LAMMPS_Out_Path = f'{SCCOP_Path}/{LAMMPS_Out_Path}/ml_{iteration:02.0f}'
        #zip poscar and scf script
        shell_script = f'''
                        #!/bin/bash --login
                        cd {SCCOP_Path}/{POSCAR_Path}/ml_{iteration:02.0f}
                        tar -zcf {node}.tar.gz `echo {poscar_str}` lammps_scf.sh
                        scp {node}.tar.gz {node}:{SCCOP_Path}/.
                        rm {node}.tar.gz
                        '''
        os.system(shell_script)
        #send poscar and scf script
        shell_script = f'''
                        #!/bin/bash --login
                        {SCCOP_Env}

                        cd {SCCOP_Path}
                        if [ ! -d lammps ]; then
                            mkdir lammps
                        fi
                        mv {node}.tar.gz lammps/.
                        cd lammps
                        tar -zxf {node}.tar.gz
                        
                        for poscar in {poscar_str}
                        do
                            mkdir calc-$poscar
                            mv $poscar calc-$poscar/POSCAR
                            cd calc-$poscar
                            cp ../../{LAMMPS_Files_Path}/SinglePointEnergy/* .
                            cd ../
                        done
                        python ../src/core/DPT_lammps.py --flag 0
                        
                        touch FINISH-{node}
                        scp FINISH-{node} {Host_Node}:{local_LAMMPS_Out_Path}/
                        rm FINISH-{node} {node}.tar.gz
                        '''
        self.ssh_node(shell_script, node)
    
    def sub_job_with_ssh(self, job, iteration, limit=50, wait_time=5, finish_ratio=.8):
        """
        SSH to target node and call lammps for calculation
        
        Parameters
        ----------
        job [str, 1d]: name of poscars in same node
        iteration [int, 0d]: sccop iteration
        limit [int, 0d]: limit of lammps jobs
        wait_time [float, 0d]: wait time of finishing job
        finish_ratio [float, 0d]: ratio of finished jobs
        """
        node = self.extract_node_name(job[0])
        poscar_str = ' '.join(job)
        finish_num = max(1, int(finish_ratio*len(job)))
        job_num = f'`ls calc-* | grep RUNNING | wc -l`'
        local_LAMMPS_Out_Path = f'{SCCOP_Path}/{LAMMPS_Out_Path}/ml_{iteration:02.0f}'
        shell_script = f'''
                        #!/bin/bash --login
                        {SCCOP_Env}
                        {Sources}
                        {Modules}
                        {Envs}
                        
                        start=$(date +%s)
                        cd {SCCOP_Path}/lammps
                        for poscar in {poscar_str}
                        do
                            cd calc-$poscar
                            cp ../lammps_scf.sh .
                            sed -i s/POSCAR/$poscar/g lammps_scf.sh
                            if [ {limit} -eq 1 ]; then
                                sh lammps_scf.sh > log
                            else
                                sh lammps_scf.sh > log&
                            fi
                            cd ../
                            
                            end=$(date +%s)
                            time=$((end - start))
                            if [ $time -ge {Scf_Time_Limit} ]; then
                                finish=`ls * | grep FINISH | wc -l`
                                if [ $finish -ge {finish_num} ]; then
                                    ps -ef | grep \"{LAMMPS_scf}\" | grep -v grep | awk '{{print $2}}' | xargs kill -9
                                    break
                                fi
                            fi
                            echo $time >> scp_time.log
                            
                            counter={job_num}
                            while [ $counter -ge {limit} ]
                            do
                                counter={job_num}
                                sleep 0.1s
                            done
                        done
                        
                        repeat=0
                        while true;
                        do
                            num={job_num}
                            end=$(date +%s)
                            time=$((end - start))
                            if [ $num -eq 0 ]; then
                                ((repeat++))
                                if [ $repeat -ge {wait_time} ]; then
                                    break
                                fi
                            fi
                            if [ $time -ge {Scf_Time_Limit} ]; then
                                finish=`ls * | grep FINISH | wc -l`
                                if [ $finish -ge {finish_num} ]; then
                                    ps -ef | grep \"{LAMMPS_scf}\" | grep -v grep | awk '{{print $2}}' | xargs kill -9
                                    break
                                fi
                            fi
                            echo $time >> scp_time.log
                            sleep 0.1s
                        done
                        
                        for poscar in {poscar_str}
                        do
                            cd calc-$poscar
                            if [ ! -e $poscar.out ]; then
                                touch $poscar.out 
                            fi
                            cp $poscar.out ../.
                            cd ../
                        done
                        touch FINISH-{node}
                        
                        scp *.out FINISH-{node} {Host_Node}:{local_LAMMPS_Out_Path}/
                        rm -r *
                        '''
        self.ssh_node(shell_script, node)
    
    def get_scf_script(self, path):
        """
        generate lammps scf script
        
        Parameters
        ----------
        path [str, 0d]: path of scf script
        """
        shell_script = f'''
                        touch RUNNING
                        date > POSCAR.out
                        {LAMMPS_scf} >> POSCAR.out
                        date >> POSCAR.out
                        rm RUNNING
                        touch FINISH
                        '''
        with open(f'{SCCOP_Path}/{path}/lammps_scf.sh', 'w') as obj:
            obj.write(shell_script)
    
    def get_energy(self, iteration):
        """
        generate energy file of current lammps outputs directory 
        
        Parameters
        ----------
        iteration [int, 0d]: sccop iteration
        """
        true_E, energys = [], []
        lammps_out = os.listdir(f'{LAMMPS_Out_Path}/ml_{iteration:02.0f}')
        lammps_out = sorted(lammps_out)
        for out in lammps_out:
            LAMMPS_output_file = f'{LAMMPS_Out_Path}/ml_{iteration:02.0f}/{out}'
            try:
                ave_E = self.get_ave_energy_from_log(LAMMPS_output_file)
            except:
                ave_E = 1e6
            if ave_E == 1e6:
                true_E.append(False)
                system_echo(' *WARNING* SinglePointEnergy is failed!')
            else:
                if ave_E < 1e2:
                    true_E.append(True)
                else:
                    true_E.append(False)
            energys.append([out, true_E[-1], ave_E])
            system_echo(f'{out}, {true_E[-1]}, {ave_E}')
        self.write_list2d(f'{LAMMPS_Out_Path}/Energy-{iteration:02.0f}.dat', energys)
        system_echo(f'Energy file generated successfully!')


class LammpsOpt(SSHTools, DeleteDuplicates, LammpsDPT):
    #optimize structure by LAMMPS
    def __init__(self, recycle, wait_time=1):
        SSHTools.__init__(self)
        self.wait_time = wait_time
        self.sccop_out_path = f'{SCCOP_Out_Path}_{recycle:02.0f}'
        self.Optim_Strus_Path = f'{Optim_Strus_Path}_{recycle:02.0f}'
        self.energy_path = f'{LAMMPS_Out_Path}/optim_strus_{recycle:02.0f}'
        self.local_Optim_Strus_Path = f'{SCCOP_Path}/{self.Optim_Strus_Path}'
        self.local_sccop_out_path = f'{SCCOP_Path}/{self.sccop_out_path}'
        self.local_energy_path = f'{SCCOP_Path}/{self.energy_path}'
        self.calculation_path = f'{SCCOP_Path}/lammps'
        if recycle <= Num_Recycle - 1:
            os.mkdir(self.Optim_Strus_Path)
            os.mkdir(self.energy_path)
        else:
            self.local_Optim_Strus_Path = f'{SCCOP_Path}/{Optim_Strus_Path}'   
            self.local_sccop_out_path = f'{SCCOP_Path}/{SCCOP_Out_Path}'
            self.local_energy_path = f'{SCCOP_Path}/{Optim_LAMMPS_Path}'
            os.mkdir(Optim_Strus_Path)
            os.mkdir(Optim_LAMMPS_Path)
    
    def run_optimization_low(self, finish_ratio=.5):
        '''
        optimize configurations at low level
        '''
        files = sorted(os.listdir(self.sccop_out_path))
        poscars = [i for i in files if i.startswith('POSCAR')]
        num_poscar = len(poscars)
        #sub optimization script to each node
        system_echo(f'Start LAMMPS Calculation --- Optimization')
        self.get_optimization_script_low()
        jobs = self.group_poscars(poscars)
        for job in jobs:
            self.sub_optimization(job)
        start = time.time()
        while not self.is_done(self.Optim_Strus_Path, num_poscar):
            time.sleep(self.wait_time)
            end = time.time()
            lammps_opt_cost = end - start
            if lammps_opt_cost > Opt_Time_Limit:
                finish_num = self.count_num(self.Optim_Strus_Path)
                if finish_num >= int(finish_ratio*Num_Opt_Low_per_Node*self.work_nodes_num):
                    for job in jobs:
                        self.kill_lammps_jobs(job)
                    break
        #delete same structures
        poscars, energys = self.get_energy(self.energy_path)
        strus = [Structure.from_file(f'{self.Optim_Strus_Path}/{i}') for i in poscars]
        idx = self.delete_same_strus_by_energy(strus, energys)
        self.delete_same_files(idx, poscars, self.Optim_Strus_Path, self.energy_path)
        self.export_energy_file(idx, poscars, energys, self.energy_path)
        self.remove_flag(self.Optim_Strus_Path)
        if Refine_Stru:
            self.add_symmetry_to_structure(self.Optim_Strus_Path)
        system_echo(f'All jobs are completed --- Optimization')
    
    def run_optimization_high(self, finish_ratio=.5):
        '''
        optimize configurations at high level
        '''
        files = sorted(os.listdir(SCCOP_Out_Path))
        poscars = [i for i in files if i.startswith('POSCAR')]
        poscar_num = len(poscars)
        #sub optimization script to each node
        system_echo(f'Start LAMMPS Calculation --- Optimization')
        self.get_optimization_script_high()
        jobs = self.group_poscars(poscars)
        for job in jobs:
            self.sub_optimization(job)
        start = time.time()
        while not self.is_done(Optim_Strus_Path, poscar_num):
            time.sleep(self.wait_time)
            end = time.time()
            lammps_opt_cost = end - start
            if lammps_opt_cost > Opt_Time_Limit:
                finish_num = self.count_num(Optim_Strus_Path)
                if finish_num >= int(finish_ratio*Num_Opt_High_per_Node*self.work_nodes_num):
                    for job in jobs:
                        self.kill_lammps_jobs(job)
                    break
        #delete same structures
        poscars, energys = self.get_energy(Optim_LAMMPS_Path)
        strus = [Structure.from_file(f'{Optim_Strus_Path}/{i}') for i in poscars]
        idx = self.delete_same_strus_by_energy(strus, energys)
        self.delete_same_files(idx, poscars, Optim_Strus_Path, Optim_LAMMPS_Path)
        self.export_energy_file(idx, poscars, energys, Optim_LAMMPS_Path)
        self.remove_flag(Optim_Strus_Path)
        if Refine_Stru:
            self.add_symmetry_to_structure(Optim_Strus_Path)
        system_echo(f'All jobs are completed --- Optimization')
    
    def get_optimization_script_low(self):
        """
        generate lammps optimization script
        """
        lammps_flag = 1 if Use_LAMMPS_Opt else 0
        shell_script = f'''
                        touch RUNNING
                        if [ {lammps_flag} -eq 1 ]; then
                            cp input_1.inp input.inp
                            date > lammps.lammps
                            {LAMMPS_opt} >> lammps.lammps
                            date >> lammps.lammps
                        else
                            {LAMMPS_scf} >> lammps.lammps
                        fi
                        rm RUNNING
                        touch FINISH
                        '''
        with open(f'{SCCOP_Path}/lammps/lammps_opt.sh', 'w') as obj:
            obj.write(shell_script)
    
    def get_optimization_script_high(self):
        """
        generate lammps optimization script
        """
        lammps_flag = 1 if Use_LAMMPS_Opt else 0
        shell_script = f'''
                        touch RUNNING
                        if [ {lammps_flag} -eq 1 ]; then
                            cp input_2.inp input.inp
                            date > lammps.lammps
                            {LAMMPS_opt} >> lammps.lammps
                            date >> lammps.lammps
                        else
                            {LAMMPS_scf} >> lammps.lammps
                        fi
                        rm RUNNING
                        touch FINISH
                        '''
        with open(f'{SCCOP_Path}/lammps/lammps_opt.sh', 'w') as obj:
            obj.write(shell_script)
    
    def sub_optimization(self, job, limit=1, wait_time=5, finish_ratio=.5):
        """
        SSH to target node and call lammps for optimization
        
        Parameters
        ----------
        job [str, 1d]: name of poscars in same node
        limit [int, 0d]: limit of lammps jobs
        wait_time [float, 0d]: wait time of finishing job
        finish_ratio [float, 0d]: ratio of finished jobs
        """
        lammps_flag = 1 if Use_LAMMPS_Opt else 0
        node = self.extract_node_name(job[0])
        poscar_str = ' '.join(job)
        finish_num = max(1, int(finish_ratio*len(job)))
        job_num = f'`ls calc-* | grep RUNNING | wc -l`'
        shell_script = f'''
                        #!/bin/bash --login
                        {SCCOP_Env}
                        {Sources}
                        {Modules}
                        {Envs}
                        
                        cd {self.calculation_path}
                        scp {Host_Node}:{SCCOP_Path}/lammps/lammps_opt.sh .
                        start=$(date +%s)
                        
                        for poscar in {poscar_str}
                        do
                            mkdir calc-$poscar
                            cd calc-$poscar
                            scp {Host_Node}:{self.local_sccop_out_path}/$poscar POSCAR
                            if [ {lammps_flag} -eq 1 ]; then
                                cp ../../{LAMMPS_Files_Path}/Optimization/* .
                            else
                                cp ../../{LAMMPS_Files_Path}/SinglePointEnergy/* .
                            fi
                            cp ../lammps_opt.sh .
                            cp POSCAR POSCAR_0
                            cd ../
                        done
                        python ../src/core/DPT_lammps.py --flag 0
                        
                        for poscar in {poscar_str}
                        do
                            cd calc-$poscar
                            if [ {limit} -eq 1 ];then
                                sh lammps_opt.sh > log
                            else
                                sh lammps_opt.sh > log&
                            fi
                            cd ../
                            
                            end=$(date +%s)
                            time=$((end - start))
                            if [ $time -ge {Opt_Time_Limit} ]; then
                                finish=`ls * | grep FINISH | wc -l`
                                if [ $finish -ge {finish_num} ]; then
                                    ps -ef | grep \"{LAMMPS_opt}\" | grep -v grep | awk '{{print $2}}' | xargs kill -9
                                    break
                                fi
                            fi
                            
                            counter={job_num}
                            while [ $counter -ge {limit} ]
                            do
                                counter={job_num}
                                sleep 0.1s
                            done
                        done
                        
                        repeat=0
                        while true;
                        do
                            num={job_num}
                            if [ $num -eq 0 ]; then
                                ((repeat++))
                                if [ $repeat -ge {wait_time} ]; then
                                    break
                                fi
                            fi
                            
                            end=$(date +%s)
                            time=$((end - start))
                            if [ $time -ge {Opt_Time_Limit} ]; then
                                finish=`ls * | grep FINISH | wc -l`
                                if [ $finish -ge {finish_num} ]; then
                                    ps -ef | grep \"{LAMMPS_opt}\" | grep -v grep | awk '{{print $2}}' | xargs kill -9
                                    break
                                fi
                            fi
                            
                            sleep 0.1s
                        done
                        
                        python ../src/core/DPT_lammps.py --flag 1
                        for poscar in {poscar_str}
                        do
                            cd calc-$poscar
                            if [ -e FINISH ]; then
                                cp POSCAR ../$poscar
                                cp lammps.lammps ../out-$poscar
                            else
                                touch lammps.lammps
                                cp POSCAR ../$poscar
                                cp lammps.lammps ../out-$poscar
                            fi
                            
                            cd ../
                            touch FINISH-$poscar
                        done
                        
                        scp POSCAR* {Host_Node}:{self.local_Optim_Strus_Path}/.
                        scp out-* {Host_Node}:{self.local_energy_path}/.
                        scp FINISH-* {Host_Node}:{self.local_Optim_Strus_Path}/.
                        rm -rf *
                        '''
        self.ssh_node(shell_script, node)
    
    def add_symmetry_to_structure(self, path, symm_tol=.1):
        """
        find symmetry unit of structure

        Parameters
        ----------
        path [str, 0d]: structure save path 
        """
        files = sorted(os.listdir(path))
        poscars = [i for i in files if i.startswith('POSCAR')]
        for i in poscars:
            stru = Structure.from_file(f'{path}/{i}')
            anal_stru = SpacegroupAnalyzer(stru, symprec=symm_tol)
            sym_stru = anal_stru.get_refined_structure()
            sym_stru.to(filename=f'{path}/{i}', fmt='poscar')
    
    def delete_same_files(self, idx, poscars, POSCAR_Path, energy_path):
        """
        delete duplicate poscar and energy files

        Parameters
        ----------
        idx [int, 1d]: index of unique structures
        poscars [str, 1d]: right poscars
        POSCAR_Path [str, 0d]: poscars path
        energy_path [str, 0d]: energy file path
        """
        files = os.listdir(POSCAR_Path)
        all_poscars = [i for i in files if i.startswith('POSCAR')]
        unique_poscars = [poscars[i] for i in idx]
        del_poscars = np.setdiff1d(all_poscars, unique_poscars)
        for poscar in del_poscars:
            file_1 = f'{POSCAR_Path}/{poscar}'
            fiel_2 = f'{energy_path}/out-{poscar}'
            if os.path.exists(file_1):
                os.remove(file_1)
            if os.path.exists(fiel_2):
                os.remove(fiel_2)
        system_echo(f'Delete same structures: {len(unique_poscars)}')
    
    def get_energy(self, path):
        """
        generate energy file of lammps outputs directory
        
        Parameters
        ----------
        path [str, 0d]: energy file path
        
        Returns
        ----------
        poscars [str, 1d]: right poscars
        energys [float, 1d]: right energys
        """
        store = []
        lammps_out = os.listdir(f'{path}')
        lammps_out_order = sorted(lammps_out)
        for out in lammps_out_order:
            LAMMPS_output_file = f'{path}/{out}'
            try:
                ave_E = self.get_ave_energy_from_log(LAMMPS_output_file)
            except:
                ave_E = 1e6
            poscar = out[4:]
            system_echo(f'{poscar}, {ave_E:18.9f}')
            store.append([poscar, ave_E])
        #get right structures
        poscars, energys = [], []
        for poscar, energy in store:
            if energy < 1e2:
                poscars.append(poscar)
                energys.append(energy)
        return poscars, energys
    
    def export_energy_file(self, idx, poscars, energys, energy_path):
        """
        export energy of unique structures
        
        Parameters
        ----------
        idx [int, 1d]: index of unique structures
        poscars [str, 1d]: right poscars
        energys [float, 1d]: right energys
        energy_path [str, 0d]: energy file path
        """
        store = []
        for i in idx:
            store.append([poscars[i], energys[i]])
        self.write_list2d(f'{energy_path}/Energy.dat', store)
        system_echo(f'Energy file generated successfully!')
    
    def kill_lammps_jobs(self, job):
        """
        kill lammps jobs that reach time limit
        
        Parameters
        ----------
        job [str, 1d]: name of poscars in same node
        """
        node = self.extract_node_name(job[0])
        poscar_str = ' '.join(job)
        shell_script = f'''
                        #!/bin/bash --login
                        cd {self.calculation_path}
                        
                        python ../src/core/DPT_lammps.py --flag 1
                        for poscar in {poscar_str}
                        do
                            cd calc-$poscar
                            if [ -e FINISH ]; then
                                cp POSCAR ../$poscar
                                cp lammps.lammps ../out-$poscar
                                
                            else
                                touch lammps.lammps
                                cp POSCAR ../$poscar
                                cp lammps.lammps ../out-$poscar
                            fi
                            
                            cd ../
                            touch FINISH-$poscar
                        done
                        
                        scp POSCAR* {Host_Node}:{self.local_Optim_Strus_Path}/.
                        scp out-* {Host_Node}:{self.local_energy_path}/.
                        scp FINISH-* {Host_Node}:{self.local_Optim_Strus_Path}/.
                        rm -rf *
                        
                        ps -ef | grep lmp | grep -v grep | awk '{{print $2}}' | xargs kill -9
                        '''
        self.ssh_node(shell_script, node)


if __name__ == "__main__":
    pass