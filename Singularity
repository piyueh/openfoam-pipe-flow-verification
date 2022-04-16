# vim:ft=singularity

Bootstrap: docker
From: openfoam/openfoam9-paraview56:9

%post
    # fix the installation path when not using BASH nor ZSH
    sed -i "s/\[\ \"\$BASH\"\ -o\ \"\$ZSH_NAME\"\ \]\ \&\&\ \\\\//g" \
        /opt/openfoam9/etc/bashrc

    # make the singularity runtime directory if not exist
    mkdir -p /.singularity.d/env

    # make a symlink of openfoam environment
    ln -s /opt/openfoam9/etc/bashrc /.singularity.d/env/99-z-openfoam9.sh
