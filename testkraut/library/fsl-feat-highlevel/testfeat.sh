set -e
for i in a b c; do
	sed -e "s,1stlevel,$(pwd)/1stlevel_$i,g" < 1stlevel.fsf > 1stlevel_$i.fsf
cat << EOT >> 1stlevel_$i.fsf
set fmri(regstandard) $(pwd)/MNI152_T1_2mm_brain
set feat_files(1) $(pwd)/fmri_$i
set highres_files(1) $(pwd)/structural_brain
EOT
done
# run the 1st level analysis three times
# each time increasing the design-unrelated noise
# by adding the residuals from the previous run to the input data
ln -s fmri.nii.gz fmri_a.nii.gz
feat 1stlevel_a.fsf
fslmaths fmri.nii.gz -add 1stlevel_a.feat/stats/res4d.nii.gz fmri_b.nii.gz
feat 1stlevel_b.fsf
fslmaths fmri.nii.gz -add 1stlevel_b.feat/stats/res4d.nii.gz fmri_c.nii.gz
feat 1stlevel_c.fsf
cat << EOT >> highlevel.fsf
set fmri(regstandard) $(pwd)/MNI152_T1_2mm_brain
set feat_files(1) "$(pwd)/1stlevel_a.feat"
set feat_files(2) "$(pwd)/1stlevel_b.feat"
set feat_files(3) "$(pwd)/1stlevel_c.feat"
EOT
feat highlevel.fsf
