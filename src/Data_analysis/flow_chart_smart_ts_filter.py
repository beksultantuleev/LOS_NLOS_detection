from pyflowchart import *


"smart ts filter"
st = StartNode('getting \ndata from MQTT')
op = OperationNode('apply ML model \nfor each anchor')
cond = ConditionNode('LOS?')
op2 = OperationNode(
    'add TimeStamps to n-size list\n\tthat self-updates.\nGet std and avrg \nof updated values.')
sub = SubroutineNode('Pass')
cond2 = ConditionNode('if TimeStamp \nin std interval')
op3 = OperationNode('Prediction from mitigation is 1.\nReturn avrg value of TS\nwith LOS prediction')
sub2 = SubroutineNode('Prediction from mitigation is 0.\nReturn avrg value of TS\nwith LOS prediction')
op4 = OperationNode('Get TS with LOS prediction')
sub2.set_connect_direction("right")


st.connect(op)
op.connect(cond)
cond.connect_yes(op2)
cond.connect_no(sub)
sub.connect(cond2)
op2.connect(cond2)

cond2.connect_yes(op3)
cond2.connect_no(sub2)
sub2.connect(op4)
op3.connect(op4)


fc = Flowchart(st)
print('>>>>>>>>>')
print(fc.flowchart())
print('>>>>>>>>>')
