from pyflowchart import *


"smart ts filter"
st = StartNode('getting TS \nwith LOS prediction')
cond = ConditionNode('Exclude NLOS?')


op = OperationNode('Calculate Position')
qn_more_than3_anch = ConditionNode('Any >=3 \n\tLOS anchors?')
op2 = OperationNode('use only LOS anchors')
# op3 = OperationNode('use any LOS and NLOS anchors\n(3 in total)')
sub = SubroutineNode('use any LOS \nand NLOS anchors\n(3 in total)')


sub.set_connect_direction("right")

st.connect(cond)
cond.connect_no(op)
cond.connect_yes(qn_more_than3_anch)
qn_more_than3_anch.connect_yes(op2)
op2.connect(op)
qn_more_than3_anch.connect_no(sub)
sub.connect(op)




fc = Flowchart(st)
print('>>>>>>>>>')
print(fc.flowchart())
print('>>>>>>>>>')
