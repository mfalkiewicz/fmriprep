#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Utility workflows
"""
from __future__ import print_function, division, absolute_import, unicode_literals

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import ants

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
from niworkflows.interfaces.masks import SimpleShowMaskRPT


def init_enhance_and_skullstrip_epi_wf(name='enhance_and_skullstrip_epi_wf'):
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(niu.IdentityInterface(fields=['in_file']),
                        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['mask_file',
                                                       'skull_stripped_file',
                                                       'bias_corrected_file',
                                                       'out_report']),
                         name='outputnode')
    n4_correct = pe.Node(ants.N4BiasFieldCorrection(dimension=3, copy_header=True),
                         name='n4_correct')
    skullstrip_first_pass = pe.Node(fsl.BET(frac=0.2, mask=True),
                                    name='skullstrip_first_pass')
    unifize = pe.Node(afni.Unifize(t2=True, outputtype='NIFTI_GZ',
                                   args='-clfrac 0.4',
                                   out_file="uni.nii.gz"), name='unifize')
    skullstrip_second_pass = pe.Node(afni.Automask(dilate=1,
                                                   outputtype='NIFTI_GZ'),
                                     name='skullstrip_second_pass')
    combine_masks = pe.Node(fsl.BinaryMaths(operation='mul'),
                            name='combine_masks')
    apply_mask = pe.Node(fsl.ApplyMask(),
                         name='apply_mask')
    mask_reportlet = pe.Node(SimpleShowMaskRPT(), name='mask_reportlet')

    workflow.connect([
        (inputnode, n4_correct, [('in_file', 'input_image')]),
        (n4_correct, skullstrip_first_pass, [('output_image', 'in_file')]),
        (skullstrip_first_pass, unifize, [('out_file', 'in_file')]),
        (unifize, skullstrip_second_pass, [('out_file', 'in_file')]),
        (skullstrip_first_pass, combine_masks, [('mask_file', 'in_file')]),
        (skullstrip_second_pass, combine_masks, [('out_file', 'operand_file')]),
        (unifize, apply_mask, [('out_file', 'in_file')]),
        (combine_masks, apply_mask, [('out_file', 'mask_file')]),
        (n4_correct, mask_reportlet, [('output_image', 'background_file')]),
        (combine_masks, mask_reportlet, [('out_file', 'mask_file')]),
        (combine_masks, outputnode, [('out_file', 'mask_file')]),
        (mask_reportlet, outputnode, [('out_report', 'out_report')]),
        (apply_mask, outputnode, [('out_file', 'skull_stripped_file')]),
        (n4_correct, outputnode, [('output_image', 'bias_corrected_file')]),
        ])

    return workflow
