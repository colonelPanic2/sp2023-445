from matplotlib import pyplot as plt
import numpy as np
import subprocess,shlex
def readfile(fname):
    metadata = [] # Each entry is (<num_its>, <runtime_cap>)
    overall_data = {'num_its':{'WAIT':0, 'CHASE':0, 'ACQUIRE':0, 'FETCH':0, 'RETURN':0}, 'runtime':{'WAIT':0, 'CHASE':0, 'ACQUIRE':0, 'FETCH':0, 'RETURN':0}}
    unit_data = {}
    with open(fname,'r') as f:
        filedata = f.read().split("\n")
    test_idx = 0
    total_its = {'WAIT':0,'CHASE':0,'ACQUIRE':0,'FETCH':0,'RETURN':0}
    unit_data[test_idx] = {'WAIT':[0,0], 'CHASE':[0,0], 'ACQUIRE':[0,0], 'FETCH':[0,0], 'RETURN':[0,0]}
    states_mask={'WAIT':1,'CHASE':1,'ACQUIRE':1,'FETCH':1,'RETURN':1}
    for line in filedata:
        line_text = line.split(" ")
        if len(line_text)==3:
            overall_data['num_its'][line_text[0]] += int(line_text[1])
            overall_data['runtime'][line_text[0]] += round(float(line_text[2]),2)
            overall_data['runtime'][line_text[0]] = round(overall_data['runtime'][line_text[0]],2)
            unit_data[test_idx][line_text[0]] = (unit_data[test_idx][line_text[0]][0]+int(line_text[1]), \
                                                 unit_data[test_idx][line_text[0]][1]+float(line_text[2]))
            if int(line_text[1])==0:
                states_mask[line_text[0]]=0
        elif len(line_text)==2:
            test_idx+=1
            unit_data[test_idx] = {'WAIT':[0,0], 'CHASE':[0,0], 'ACQUIRE':[0,0], 'FETCH':[0,0], 'RETURN':[0,0]}
            metadata.append((int(line_text[0],16),float(line_text[1])))
            for state in ['WAIT','CHASE','ACQUIRE','FETCH','RETURN']:
                total_its[state]+=states_mask[state]
            states_mask={'WAIT':1,'CHASE':1,'ACQUIRE':1,'FETCH':1,'RETURN':1}
    metadata.append(total_its)
    data = {'md':metadata, 'overall':overall_data, 'unit':unit_data}
    return data

def create_subplots(data,numtests_or_testidx,num_its_total,num_its_test=None,align='center',color=['red','black','red','black','red']):
    states = ['WAIT', 'CHASE', 'ACQUIRE', 'FETCH', 'RETURN']
    fig,ax = plt.subplots(2)
    ax[1].set_ylabel('num_its')
    ax[1].set_title('# of iterations for each state function')
    ax[0].set_ylabel('runtime (milliseconds)')
    ax[0].set_title('Average runtimes (ms) for each state function')
    fig.subplots_adjust(hspace=0.5)
    dirs = str(subprocess.check_output(shlex.split("ls")))[2:-1].split("\\n")[:-1]
    pwd = ''
    if 'timedata' in dirs:
        pwd+='timedata/'
    if 'num_its' in list(data.keys()):
        if f"{pwd}fetching-tests/overall.png" in dirs:
            subprocess.run(shlex.split('rm '+f'{pwd}fetching-tests/overall.png'))
        subprocess.run(shlex.split("touch "+f"{pwd}fetching-tests/overall.png"))
        num_its_avg = list(np.round(np.array(list(data['num_its'].values())),0))
        runtime_avg = []
        # list(np.round(np.array(list(data['runtime'].values()))/(num_its_total),2))
        print(num_its_total)
        for state in states:
            if num_its_total[state]==0:
                runtime_avg.append(data['runtime'][state])
            else:
                runtime_avg.append(round(data['runtime'][state]/num_its_total[state],2))
        ax[1].bar(states,height=num_its_avg,align=align,color=color)
        ax[0].bar(states,height=runtime_avg,align=align,color=color)
        fig.suptitle("Across all {} tests".format(numtests_or_testidx),fontsize=14)
        plt.savefig(f'{pwd}fetching-tests/overall.png')
        return num_its_avg,runtime_avg
    else:
        unit_data = data
        if f"{pwd}fetching-tests/test{numtests_or_testidx}.png" in dirs:
            subprocess.run(shlex.split('rm '+pwd+f'fetching-tests/test{numtests_or_testidx}.png'))
        subprocess.run(shlex.split("touch "+pwd+f"fetching-tests/test{numtests_or_testidx}.png"))
        num_its,runtimes=[],[]
        for state in states:
            num_its.append(unit_data[numtests_or_testidx][state][0]) # num_its at index 0
            runtimes.append(unit_data[numtests_or_testidx][state][1])
        runtimes = list(np.round(np.array(runtimes)/num_its_test,2))
        # num_its = num_its
        ax[0].bar(states, height=runtimes,align='center',color=['red','black','red','black','red'])
        ax[1].bar(states, height=num_its,align='center',color=['red','black','red','black','red'])
        fig.subplots_adjust(hspace=0.5)
        fig.suptitle(f"Test {numtests_or_testidx}",fontsize=14)
        plt.savefig(f'{pwd}fetching-tests/test{numtests_or_testidx}.png')
        return num_its,runtimes
def process_data(microcontroller_time_data_list=[]):
    pwd = ""
    dirs = str(subprocess.check_output(shlex.split("ls")))[2:-1].split("\\n")[:-1]
    if 'timedata' in dirs:
        pwd+='timedata/'
    dirs = str(subprocess.check_output(shlex.split(f"ls {pwd}")))[2:-1].split("\\n")[:-1]
    if 'fetching-tests' not in dirs:
        subprocess.run(shlex.split(f"mkdir {pwd}fetching-tests"))
        print('hi')
    data = readfile(pwd+'timedata.csv')
    metadata,overall_data,unit_data = data['md'],data['overall'],data['unit']
    test_idx = 0
    for num_its,runtime_cap in metadata[:-1]:
        num_its,runtime = create_subplots(unit_data,test_idx,metadata[-1],num_its)
        print("Test {}:\nruntimes (ms): {}\n      num_its: {}\n".format(test_idx,runtime,num_its))
        test_idx+=1
    overall_num_its,overall_runtime = create_subplots(data['overall'],len(metadata[:-1]),metadata[-1])
    print("\n\nOverall:\nruntimes (ms): {}\n      num_its: {}\n".format(overall_runtime,overall_num_its))
    dirs = str(subprocess.check_output(shlex.split(f"ls {pwd}fetching-tests")))[2:-1].split("\\n")[:-1]
    for i in range(test_idx,len(dirs)):
        if f"test{i}.png" in dirs:
            subprocess.run(shlex.split('rm '+pwd+f'fetching-tests/test{i}.png'))
    print("Created bar graphs for {} tests.".format(test_idx))
    # If there is time data for the microcontroller, then do something with it.
    if microcontroller_time_data_list!=[]:
        if len(microcontroller_time_data_list)>0:
            print(f"\nMICROCONTOLLER RESPONSE TIMES: {microcontroller_time_data_list}")
            dirs = str(subprocess.check_output(shlex.split("ls")))[2:-1].split("\\n")[:-1]
            if 'microcontroller-runtimes.csv' not in dirs:
                subprocess.run(shlex.split(f"touch {pwd}microcontroller-runtimes.csv"))
            with open(f'{pwd}microcontroller-runtimes.csv','a') as f:
                f.write(str(microcontroller_time_data_list)[1:-1].strip()+'\n')
        else:
            print("No microcontroller response time data collected")
        # TODO: to be continued...

    return 0

if __name__=='__main__':
    process_data()