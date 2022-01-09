from pyflowchart import *

'draw model logic Simple ts filter'
st = StartNode('getting \ndata from MQTT')
op = OperationNode('apply ML model \nfor each anchor')
cond = ConditionNode('LOS?')
op2 = OperationNode(
    'add TimeStamps to n-size list\n\tthat self-updates.\nGet std and avrg of updated values.\nReturn avrg value of TS\nwith LOS prediction')
sub = SubroutineNode('Return avrg \nvalue of TS\nwith LOS prediction')
op3 = OperationNode('Get TS with LOS prediction')

sub.set_connect_direction("right")

st.connect(op)
op.connect(cond)
cond.connect_yes(op2)
cond.connect_no(sub)
sub.connect(op3)
op2.connect(op3)
'end of simple TS fiter'


fc = Flowchart(st)
print('>>>>>>>>>')
print(fc.flowchart())
print('>>>>>>>>>')
