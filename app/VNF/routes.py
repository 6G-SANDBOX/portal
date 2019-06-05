import os
import shutil
from typing import List
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from config import Config as UploaderConfig
from app import db
from app.models import Action, VNF
from app.VNF import bp
from app.VNF.forms import VNFForm
from Helper import Log


@bp.route('/repository', methods=['GET', 'POST'])
@login_required
def repository():
    VNFs: List[VNF] = current_user.user_VNFs()
    return render_template('VNF/repository.html', title='Home', VNFs=VNFs)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = VNFForm()
    if form.validate_on_submit():
        if 'fileVNFD' not in request.files or 'fileImage' not in request.files:
            Log.I('Can\'t upload VNF. There are files missing')
            flash('There are files missing', 'error')
            return redirect(request.url)

        fileVNFD = request.files['fileVNFD']
        fileImage = request.files['fileImage']

        if fileVNFD.filename == '' or fileImage.filename == '':
            flash('There are files missing', 'error')
            return redirect(request.url)

        if fileVNFD and fileImage:
            fileVNFD_name = secure_filename(fileVNFD.filename)
            fileImage_name = secure_filename(fileImage.filename)

            Log.D(f'Upload VNF form data - Name: {form.name.data}, Description: {form.description.data}'
                  f', VNFD {fileVNFD_name}, image: {fileImage_name}')

            new_VNF: VNF = VNF(name=form.name.data, author=current_user, description=form.description.data,
                          VNFD=fileVNFD_name, image=fileImage_name)

            db.session.add(new_VNF)
            db.session.commit()
            Log.I(f'Added VNF {new_VNF.name}')
            action: Action = Action(timestamp=datetime.utcnow(), author=current_user,
                            message=f'<a href="/VNF/repository">Uploaded VNF: {new_VNF.name}</a>')
            Log.I(f'Added action - Uploaded VNF')
            db.session.add(action)
            db.session.commit()

            baseFolder = os.path.join(UploaderConfig.UPLOAD_FOLDER, 'vnfs', str(new_VNF.id))
            os.makedirs(os.path.join(baseFolder, "vnfd"), mode=0o755, exist_ok=True)
            os.makedirs(os.path.join(baseFolder, "images"), mode=0o755, exist_ok=True)
            fileVNFD.save(os.path.join(baseFolder, "vnfd", fileVNFD_name))
            Log.D(f'Saved VNFD file {fileVNFD_name} in VNF {new_VNF.id}')
            fileImage.save(os.path.join(baseFolder, "images", fileImage_name))
            Log.D(f'Saved Image file {fileImage_name} in VNF {new_VNF.id}')

            flash('Your VNF has been successfully uploaded', 'info')
            return redirect(url_for('VNF.repository'))
        Log.I('Can\'t upload VNF. There are files missing')
        flash('There are files missing', 'error')
    return render_template('VNF/upload.html', title='Home', form=form)


@bp.route('/delete/<vnf_id>', methods=['GET'])
@login_required
def delete(vnf_id: int):
    vnf: VNF = VNF.query.get(vnf_id)
    if vnf:
        if vnf.user_id == current_user.id:
            db.session.delete(vnf)
            db.session.commit()
            shutil.rmtree(os.path.join(UploaderConfig.UPLOAD_FOLDER, 'vnfs', str(vnf_id)))
            Log.I(f'VNF {vnf_id} successfully removed')
            flash(f'The VNF has been successfully removed', 'info')
        else:
            Log.I(f'Forbidden - User {current_user.name} don\'t have permission to remove VNF {vnf_id}')
            flash(f'Forbidden - You don\'t have permission to remove this VNF', 'error')
    else:
        return render_template('errors/404.html'), 404
    return redirect(url_for('VNF.repository'))
