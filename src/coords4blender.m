function coords4blender(subj, basedir)
%blender_coords = coords4blender(subj)
% provides monopolar and bipolar  coordinates from the talStruct to use for
% visualization in blender. Also gives original starting coordinates.
%
% subj ............... The subject being analyzed.

% -JMS (October 2016)
% joel.stein@uphs.upenn.edu

%Get the monopolar data from talStruct

try
    try
       talStruct_mono = getBipolarSubjElecs(subj,1);
    catch
        disp(sprintf('%s: No talStruct',subj));
        return;
    end
    talStruct_mono = getBipolarSubjElecs(subj,0);
    monopolars = {talStruct_mono.tagName};
    monoTypes = {talStruct_mono.eType};
    monoSurf = [talStruct_mono.indivSurf];
    
    %Get the bipolar data from talStruct
    talStruct = getBipolarSubjElecs(subj,1);
    bipolars = {talStruct.tagName};
    bipoTypes = {talStruct.eType};
    bipoSurf = [talStruct.indivSurf];
    
    %Get the original starting monopolar coordinates
    if isfield(monoSurf,'x')
        start_coords = 0.02*double([[monoSurf.x]', [monoSurf.y]', [monoSurf.z]']);
    else
        disp(sprintf('%s: Could not get starting coordinates',subj));
        return;
    end
    
    %Check if surface electrodes are present based on eType in talStruct
    if ~any(strcmp(monoTypes,'S')) & ~any(strcmp(monoTypes,'G'))
        disp(sprintf('%s: No surface electrodes',subj));
        surf_coords = 0.02*double([[monoSurf.x]', [monoSurf.y]', [monoSurf.z]']);
        surf_coords_bipolar = 0.02*double([[bipoSurf.x]', [bipoSurf.y]', [bipoSurf.z]']);
        %return;
    else
    
    %Check if Dykstra coordinates are present
    if isfield(monoSurf,'x_Dykstra')
        surf_coords = 0.02*double([[monoSurf.x_Dykstra]', [monoSurf.y_Dykstra]', [monoSurf.z_Dykstra]']);
    else
        disp(sprintf('%s: Surface electrodes but no Dykstra coords',subj));
        return;
    end
    
    surf_coords_bipolar = 0.02*double([[bipoSurf.x_Dykstra]', [bipoSurf.y_Dykstra]', [bipoSurf.z_Dykstra]']);
    
    end
    
    %write to the specified or default outfile for monopolar starting coordinates
    outfile_starting = fullfile(basedir, 'monopolar_start_blender.txt')
    fid = fopen(outfile_starting,'w');
    for elec_i=1:size(surf_coords,1)
        fprintf(fid, '%s\t%d\t%d\t%d\t%s\n', strcat('o', monopolars{1,elec_i}), start_coords(elec_i,1), ...
        start_coords(elec_i,2), start_coords(elec_i,3), monoTypes{1,elec_i});
    end
    
    %write to the specified or default outfile for monopolars
    outfile = fullfile(basedir, 'monopolar_blender.txt')
    fid = fopen(outfile,'w');
    for elec_i=1:size(surf_coords,1)
        fprintf(fid, '%s\t%d\t%d\t%d\t%s\n', monopolars{1,elec_i}, surf_coords(elec_i,1), ...
        surf_coords(elec_i,2), surf_coords(elec_i,3), monoTypes{1,elec_i});
    end
    
    %write to the specified or default outfile for bipolars
    outfile_bipolar = fullfile(basedir, 'bipolar_blender.txt')
    fid = fopen(outfile_bipolar,'w');
    for elec_i=1:size(surf_coords_bipolar,1)
        fprintf(fid, '%s\t%d\t%d\t%d\t%s\n', bipolars{1,elec_i}, surf_coords_bipolar(elec_i,1), ...
        surf_coords_bipolar(elec_i,2), surf_coords_bipolar(elec_i,3), bipoTypes{1,elec_i});
    end
    
    %write the names of the monopolar starting coordinates
    outfile = fullfile(basedir, 'monopolar_start_names.txt')
    fid = fopen(outfile,'w');
    for elec_i=1:size(surf_coords,1)
        fprintf(fid, '"%s",', strcat('o', monopolars{1,elec_i}));
    end
    
    %write the names of the monopolars
    outfile = fullfile(basedir, 'monopolar_names.txt')
    fid = fopen(outfile,'w');
    for elec_i=1:size(surf_coords,1)
        fprintf(fid, '"%s",', monopolars{1,elec_i});
    end
    
    %write the names of the bipolars
    outfile_bipolar = fullfile(basedir, 'bipolar_names.txt')
    fid = fopen(outfile_bipolar,'w');
    for elec_i=1:size(surf_coords_bipolar,1)
        fprintf(fid, '"%s",', bipolars{1,elec_i});
    end
catch
    exit;
end    
