import os
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.io as nio           # Data i/o
import nipype.pipeline.engine as pe          # pypeline engine

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

test_workflow = pe.Workflow(name='justbet')

datasource = pe.Node(interface=nio.DataGrabber(outfields=['head']),
                     name = 'datasource')
datasource.inputs.base_directory = os.path.abspath(os.curdir)
datasource.inputs.template = '%s.nii.gz'
datasource.inputs.template_args = dict(head=[['head']])


bet = pe.Node(interface=fsl.BET(mask=True),
              name='bet')

datasink = pe.Node(interface=nio.DataSink(parameterization=False),
                   name="datasink")
datasink.inputs.base_directory = os.path.abspath(os.curdir)
test_workflow.connect(datasource, 'head', bet, 'in_file')
test_workflow.connect(bet, 'out_file', datasink, 'output.@brain')
test_workflow.connect(bet, 'mask_file', datasink, 'output.@brainmask')
