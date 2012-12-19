# mimicking some analysis in FEAT using AFNI
# NNO Nov 2012

E=".nii.gz"
T=_tmp # prefix for temporary files

afnidir=fmri.afni # put everything it its own directory
srcdir=".."  # where the original files are - relative to $afnidir

# do ont complain about existing files
AFNI_DECONFLICT=OVERWRITE
export AFNI_DECONFLICT

# stop when fails
set -e

if [ ! -e $afnidir ]; then mkdir $afnidir; fi

cd $afnidir || exit 1

# store 91-st volume
3dbucket -prefix ./example_func.nii.gz ${srcdir}/fmri.nii.gz'[90]'

#################################### preprocessing #################################### 
# despike
3dDespike -prefix ./${T}_ds ${srcdir}/fmri.nii.gz

# make it original space - not Talairach (ensure header is set properly)
3drefit -view orig -space ORIG ${T}_ds+tlrc
3drefit -TR 3 ${T}_ds+orig # set TR to 3 seconds
3dcopy -overwrite ${T}_ds+orig ${T}_ds${E}
rm ${T}_ds+orig.HEAD ${T}_ds+orig.BRIK*

# (from now on store everything as compressed nifti)

# motion correction
3dvolreg -overwrite -prefix ${T}_vr${E} -base example_func${E}'[0]' -1Dfile mcparam.1D ${T}_ds${E}

# coregistration of functional data
epi=example_func.nii.gz
anat=structural_brain.nii.gz
template=MNI152_T1_2mm_brain.nii.gz

# link the anatomical and template files - easy for visualization later on
ln -s ${srcdir}/$anat .
ln -s ${srcdir}/$template .

# align epi to anat (for now with 12 dof affine registration)
align_epi_anat.py -anat_has_skull no -epi $epi -anat $anat -epi_base 0 -epi_strip None -big_move -cmass cmass+xyz  -dset2to1 -overwrite

# align anat to MNI
align_epi_anat.py -dset1_strip None -dset2_strip None -dset1 $anat -dset2 $template -suffix _al -overwrite -big_move -cmass cmass+xyz -overwrite 

# define matrix input and output files
mx1=example_func.nii.gz_al_mat.aff12.1D
mx2=structural_brain.nii.gz_al_mat.aff12.1D
mx=func2mni.aff12.1D

# store the combined coregistration matrices in a single 3x4 matrix file
cat_matvec $mx2 $mx1 > $mx

# apply transformation and resample to anatomical grid
3dWarp -gridset $template -matvec_out2in $mx -prefix ${T}_vr_mni${E} ${T}_vr${E}
3drefit -space MNI -view tlrc ${T}_vr_mni${E}

# make a simple automask 
# note to michael: an alternative would be to use the MNI brain as a mask.
maskfile=epi_mask${E}

3dAutomask -overwrite -prefix $maskfile ${T}_vr_mni${E}

# blur with 5 mm FWHM kernel
3dmerge -overwrite -1filter_blur 5.0 -1fmask epi_mask${E} -doall -prefix ${T}_bl${E} ${T}_vr_mni${E}

# compute mean
3dTstat -overwrite -prefix ${T}_mean${E} ${T}_bl${E}

# compute signal change
3dcalc -overwrite -a ${T}_bl${E} -b ${T}_mean${E} -expr '100*a/b' -prefix preproc${E} -datum float

# remove temporary files
rm ${T}*${E}

#################################### GLM #################################### 

# run simple GLM - ordinary least squares, polynomial detrending up to and including fourth legendre polynomial
# note: for temporal autocorrelation one should use 3dREMLfit
3dDeconvolve -num_stimts 2 -overwrite -stim_times 1 '1D: 0 60 120 180 240 300 360 420 480' 'SPMG2(30)' -stim_times 2 '1D: 0 90 180 270 360 450' 'SPMG2(45)' -input preproc${E} -prefix glm -polort 4 -fout -tout -bucket glm${E} -errts glm_errts${E}

# convert overall ANOVA F test into z score (which is in the first sub-brick of glm output)
3dmerge -overwrite -prefix full_f_as_z${E} -1zscore glm${E}'[0]' 

#################################### clustering #################################### 

# determine smoothness of the noise
fwhm=`3dFWHMx -combine -mask $maskfile glm_errts${E} | cut -c30-`

echo $fwhm > smoothness.1D

# define uncorrected voxel-wise threshold
zthr=2.15 # michael please check! currently everything is connected - so I think it should be better to get a higher value

# convert to p value for monte carlo simulation
pthr=`cdf -t2p fizt $zthr  | cut -f2 -d'='`

# cluster-based whole-brain corrected threshold (alpha value)
athr=0.01

# run monte carlo simulation - a relatively fast one with only 2000 iterations
3dClustSim -mask $maskfile -fwhm $fwhm -pthr $pthr -athr $athr -niter 2000 > clustsim.log

# get critical cluster size
minclsize=`tail -1 clustsim.log | cut -c10-`

# generated a clustered dataset
3dmerge -dxyz=1 -1clust 1 $minclsize -1thresh $zthr -1tindex 0 -prefix full_f_as_z_clusters${E} full_f_as_z${E}

# generate a cluster table
3dclust -1clip 1 0 0 full_f_as_z_clusters${E} > full_f_as_z_clustertable.txt
