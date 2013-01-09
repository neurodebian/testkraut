cat << EOT >> design.fsf
set fmri(regstandard) $(pwd)/MNI152_T1_2mm_brain
set feat_files(1) $(pwd)/fmri
set highres_files(1) $(pwd)/structural_brain
set fmri(outputdir) $(pwd)/fmri.feat
EOT
feat design.fsf
