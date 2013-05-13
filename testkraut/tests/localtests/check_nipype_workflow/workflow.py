import os
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

infosource = pe.Node(
        interface=niu.IdentityInterface(fields=['subject_id']),
        name="infosource")
infosource.iterables = ('subject_id', [str(i) for i in range(3)])


datasink = pe.Node(
    name="datasink",
    interface=nio.DataSink(
        base_directory=os.curdir
    )
)

wf = pe.Workflow(name='demo_wf')
wf.connect(infosource, 'subject_id', datasink, 'container')

test_workflow = wf
