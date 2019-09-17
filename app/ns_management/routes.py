import os
import shutil
from typing import List
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from config import Config as UploaderConfig
from app import db
from app.models import Action, VNF, NS
from app.ns_management import bp
from app.ns_management.forms import VNFForm, NSForm
from Helper import Log


@bp.route('/repository', methods=['GET', 'POST'])
@login_required
def repository():
    VNFs: List[VNF] = current_user.userVNFs()
    NSs: List[NS] = current_user.userNSs()
    return render_template('ns_management/repository.html', title='Home', VNFs=VNFs, NSs=NSs)


@bp.route('/uploadNs', methods=['GET', 'POST'])
@login_required
def upload_NS():
    form = NSForm()
    if form.validate_on_submit():

        # Check if files were uploaded correctly
        if 'fileNSD' not in request.files:
            Log.I('Can\'t upload NS. There are files missing')
            flash('There are files missing', 'error')
            return redirect(request.url)

        fileNSD = request.files['fileNSD']

        if fileNSD.filename == '':
            flash('There are files missing', 'error')
            return redirect(request.url)

        if fileNSD:
            fileNSDName = secure_filename(fileNSD.filename)
            Log.D(f'Upload NSD form data - Name: {form.name.data}, Description: {form.description.data}, '
                  f'NSD {fileNSDName}')
            newNS: NS = NS(name=form.name.data, author=current_user, description=form.description.data,
                              NSD=fileNSDName)
            db.session.add(newNS)
            db.session.commit()

            Log.I(f'Added VNF {newNS.name}')
            action: Action = Action(timestamp=datetime.utcnow(), author=current_user,
                                    message=f'<a href="/VNF/repository">Uploaded VNF: {newNS.name}</a>')
            Log.I(f'Added action - Uploaded NS')
            db.session.add(action)
            db.session.commit()

            # Store VNFD and Image files
            baseFolder = os.path.join(UploaderConfig.UPLOAD_FOLDER, 'nss', str(newNS.id))
            os.makedirs(os.path.join(baseFolder, "nss"), mode=0o755, exist_ok=True)
            fileNSD.save(os.path.join(baseFolder, "nss", fileNSDName))
            Log.D(f'Saved NSD file {fileNSDName} in NS {newNS.id}')

            flash('Your NS has been successfully uploaded', 'info')
            return redirect(url_for('NsManagement.repository'))

        Log.I('Can\'t upload NS. There are files missing')
        flash('There are files missing', 'error')
    return render_template('ns_management/upload_ns.html', title='Home', form=form)

@bp.route('/uploadVnf', methods=['GET', 'POST'])
@login_required
def upload_VNF():
    form = VNFForm()
    if form.validate_on_submit():

        # Check if files were uploaded correctly
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
            fileVNFDName = secure_filename(fileVNFD.filename)
            fileImageName = secure_filename(fileImage.filename)
            Log.D(f'Upload VNF form data - Name: {form.name.data}, Description: {form.description.data}, '
                  f'VNFD {fileVNFDName}, image: {fileImageName}')
            newVNF: VNF = VNF(name=form.name.data, author=current_user, description=form.description.data,
                              VNFD=fileVNFDName, image=fileImageName)
            db.session.add(newVNF)
            db.session.commit()

            Log.I(f'Added VNF {newVNF.name}')
            action: Action = Action(timestamp=datetime.utcnow(), author=current_user,
                                    message=f'<a href="/VNF/repository">Uploaded VNF: {newVNF.name}</a>')
            Log.I(f'Added action - Uploaded VNF')
            db.session.add(action)
            db.session.commit()

            # Store VNFD and Image files
            baseFolder = os.path.join(UploaderConfig.UPLOAD_FOLDER, 'vnfs', str(newVNF.id))
            os.makedirs(os.path.join(baseFolder, "vnfd"), mode=0o755, exist_ok=True)
            os.makedirs(os.path.join(baseFolder, "images"), mode=0o755, exist_ok=True)
            fileVNFD.save(os.path.join(baseFolder, "vnfd", fileVNFDName))
            Log.D(f'Saved VNFD file {fileVNFDName} in VNF {newVNF.id}')
            fileImage.save(os.path.join(baseFolder, "images", fileImageName))
            Log.D(f'Saved Image file {fileImageName} in VNF {newVNF.id}')

            flash('Your VNF has been successfully uploaded', 'info')
            return redirect(url_for('NsManagement.repository'))

        Log.I('Can\'t upload VNF. There are files missing')
        flash('There are files missing', 'error')
    return render_template('ns_management/upload_vnf.html', title='Home', form=form)